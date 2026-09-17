import io
import os
import re
import sys
import uuid
import zipfile
import logging
from datetime import datetime, timezone, date
from pathlib import Path
from typing import List, Optional, Dict, Annotated, Any

from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, FileResponse, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from openpyxl import load_workbook, Workbook

import document_service as docsvc
import master_data as masterdata
import residents_service as ressvc

# Sample Excel columns (header -> example value) matching the contract template.
SAMPLE_COLUMNS = [
    ("Номер договора", "0047390 003370"),
    ("Дата подписания", "« 21 » июля 2026"),
    ("Номер приказа", "228"),
    ("Дата приказа", "«21» июля 2026"),
    ("Гражданство", "Туркменистана"),
    ("ФИО", "Шаназаров Мырат"),
    ("Дата рождения", "15.05.2007"),
    ("Номер комнаты", "302/2"),
    ("Срок договора до", "30.06.2028"),
    ("Адрес регистрации", "пр-т Дзержинского, 85, ком. 302/2"),
    ("Номер паспорта", "А3058202"),
    ("Дата выдачи", "08.01.2025"),
    ("Срок действия", "07.01.2030"),
    ("Кем выдан", "Государственной Миграционной Службой Туркменистана"),
    ("ИИН", "LB00258610"),
    ("Телефон", "+37529354-11-59"),
]

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

UPLOAD_DIR = ROOT_DIR / "templates_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def _active_tpl():
    """Return path (str) of the active custom template, or None for the built-in one."""
    s = await db.app_settings.find_one({"key": "active_template"})
    tid = s.get("value") if s else "default"
    if not tid or tid == "default":
        return None
    t = await db.templates.find_one({"id": tid})
    if not t:
        return None
    p = UPLOAD_DIR / t["filename"]
    return str(p) if p.exists() else None


async def _render(fields):
    return docsvc.render_docx(fields, await _active_tpl())

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PyObjectId = Annotated[str, BeforeValidator(str)]


# ---------- Models ----------
class Dataset(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    columns: List[str]
    rows: List[Dict[str, str]]
    mapping: Dict[str, str]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class GenerateRequest(BaseModel):
    fields: Dict[str, str]
    status: Optional[str] = "final"


class BatchGenerateRequest(BaseModel):
    contracts: List[Dict[str, str]]
    masters: List[Dict[str, Any]] = []


class Contract(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    contract_number: str = ""
    full_name: str = ""
    fields: Dict[str, str]
    master: Dict[str, str] = {}
    status: str = "final"  # "final" | "draft"
    demo: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BatchDownloadRequest(BaseModel):
    ids: List[str]
    format: str = "docx"


class ManualDuplexRequest(BaseModel):
    ids: List[str]
    side: str = "front"          # "front" | "back"
    back_order: str = "reversed"  # "reversed" | "normal"
    separators: bool = False
    orientation: str = "portrait"  # "portrait" | "landscape"
    flip_edge: str = "long"        # "long" | "short"


class Preset(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    fields: Dict[str, str]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PresetRequest(BaseModel):
    name: str
    fields: Dict[str, str]


class Resident(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    floor: int = 0
    block: str = ""            # "902"
    room: str = ""             # "2"
    full_name: str = ""
    status: str = ""
    study_group: str = ""      # учебная группа (Группа)
    benefit: str = ""          # ЛЬГОТА
    contract_number: str = ""
    move_in_date: str = ""
    term: str = ""             # срок действия
    note: str = ""
    no_contract_needed: bool = False   # договор не требуется
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ResidentRequest(BaseModel):
    """Частичное создание/обновление жильца."""
    model_config = ConfigDict(extra="ignore")
    block: Optional[str] = None
    room: Optional[str] = None
    full_name: Optional[str] = None
    status: Optional[str] = None
    study_group: Optional[str] = None
    benefit: Optional[str] = None
    contract_number: Optional[str] = None
    move_in_date: Optional[str] = None
    term: Optional[str] = None
    note: Optional[str] = None
    no_contract_needed: Optional[bool] = None


# ---------- Helpers ----------
def _cell_to_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y")
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y")
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _safe_name(name: str) -> str:
    name = re.sub(r'[^\w\-. ]', '_', name or "contract")
    return name.strip() or "contract"


# ---------- Routes ----------
@api_router.get("/")
async def root():
    return {"message": "Contract generator API"}


@api_router.get("/fields")
async def get_fields():
    return {"fields": docsvc.FIELDS}


@api_router.get("/stats")
async def stats():
    final_q = {"status": {"$ne": "draft"}}
    total = await db.contracts.count_documents(final_q)
    drafts = await db.contracts.count_documents({"status": "draft"})
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    this_month = await db.contracts.count_documents(
        {"created_at": {"$gte": month_start}, "status": {"$ne": "draft"}}
    )
    datasets = await db.datasets.count_documents({})
    recent = await db.contracts.find(final_q, {"_id": 0}).sort("created_at", -1).to_list(6)
    return {
        "total": total,
        "drafts": drafts,
        "this_month": this_month,
        "datasets": datasets,
        "recent": recent,
    }


@api_router.get("/sample-template")
async def sample_template():
    wb = Workbook()
    ws = wb.active
    ws.title = "Студенты"
    ws.append([h for h, _ in SAMPLE_COLUMNS])
    ws.append([v for _, v in SAMPLE_COLUMNS])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=sample_students.xlsx"},
    )


@api_router.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=400, detail="Поддерживаются только файлы .xlsx")
    content = await file.read()
    try:
        wb = load_workbook(io.BytesIO(content), data_only=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Не удалось прочитать файл: {e}")
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)
    try:
        header_row = next(rows_iter)
    except StopIteration:
        raise HTTPException(status_code=400, detail="Файл пуст")

    columns = [(_cell_to_str(h) or f"Колонка {i+1}") for i, h in enumerate(header_row)]
    rows = []
    for raw in rows_iter:
        if raw is None or all(c is None for c in raw):
            continue
        row = {}
        for i, col in enumerate(columns):
            row[col] = _cell_to_str(raw[i]) if i < len(raw) else ""
        if any(v for v in row.values()):
            rows.append(row)

    mapping = docsvc.auto_map_columns(columns)
    dataset = Dataset(filename=file.filename, columns=columns, rows=rows, mapping=mapping)
    await db.datasets.insert_one(dataset.model_dump())
    return dataset.model_dump()


@api_router.get("/datasets/latest")
async def latest_dataset():
    doc = await db.datasets.find_one({}, {"_id": 0}, sort=[("created_at", -1)])
    return doc


def _apply_mapping(rows, mapping):
    """Convert raw rows to field-keyed student dicts using column mapping."""
    students = []
    for row in rows:
        student = {}
        for key, col in mapping.items():
            student[key] = row.get(col, "")
        students.append(student)
    return students


@api_router.post("/students/map")
async def map_students(payload: Dict):
    rows = payload.get("rows", [])
    mapping = payload.get("mapping", {})
    return {"students": _apply_mapping(rows, mapping)}


async def _save_contract(fields: Dict[str, str], status: str = "final",
                         master: Dict[str, str] = None) -> Contract:
    contract = Contract(
        contract_number=fields.get("contract_number", ""),
        full_name=fields.get("full_name", ""),
        fields=fields,
        master=master or {},
        status=status if status in ("final", "draft") else "final",
    )
    await db.contracts.insert_one(contract.model_dump())
    return contract


@api_router.post("/contracts")
async def create_contract(req: GenerateRequest):
    contract = await _save_contract(req.fields, req.status or "final")
    return contract.model_dump()


# ---------------------------------------------------------------------------
# Настройки приложения (свои столбцы, зависимости) — коллекция settings
# ---------------------------------------------------------------------------
SETTINGS_ID = "app_settings"


async def _get_setting(key: str, default=None):
    doc = await db.settings.find_one({"id": SETTINGS_ID}, {"_id": 0})
    if not doc:
        return default
    return doc.get(key, default)


async def _set_setting(key: str, value):
    await db.settings.update_one({"id": SETTINGS_ID},
                                 {"$set": {"id": SETTINGS_ID, key: value}},
                                 upsert=True)


async def _custom_columns() -> list:
    return await _get_setting("custom_columns", []) or []


# ---------- Схема таблицы (встроенные + свои колонки) ----------
@api_router.get("/master-schema")
async def get_master_schema():
    custom = await _custom_columns()
    builtin = [{"key": c["key"], "label": c["header"], "section": c["section"],
                "dropdown": c.get("dropdown"), "builtin": True}
               for c in masterdata.MASTER_COLUMNS]
    custom_cols = [{"key": c["key"], "label": c["label"],
                    "section": c.get("section", "Дополнительно"),
                    "dropdown": c.get("dropdown"), "builtin": False}
                   for c in custom]
    return {"columns": builtin + custom_cols}


# ---------- Вся база строками для таблицы-Excel ----------
@api_router.get("/contracts/grid")
async def contracts_grid():
    docs = await db.contracts.find({}, {"_id": 0}).sort("created_at", -1).to_list(100000)
    rows = []
    for d in docs:
        m = dict(d.get("master") or {})
        if not any(str(v).strip() for v in m.values()):
            m = masterdata.contract_to_master(d.get("fields", {}) or {})
        rows.append({
            "id": d.get("id"),
            "status": d.get("status", "final"),
            "created_at": d.get("created_at", ""),
            "contract_number": d.get("contract_number", ""),
            "full_name": d.get("full_name", ""),
            "master": m,
        })
    return {"rows": rows}


class MasterRowUpdate(BaseModel):
    id: str
    master: Dict[str, Any] = {}


class MasterBulkRequest(BaseModel):
    rows: List[MasterRowUpdate]


@api_router.put("/contracts/master-bulk")
async def save_master_bulk(req: MasterBulkRequest):
    """Сохранить отредактированные строки таблицы: пересобрать поля документов из master."""
    updated = 0
    for r in req.rows:
        m = {k: ("" if v is None else str(v)) for k, v in (r.master or {}).items()}
        fields = masterdata.master_to_contract(m)
        upd = {
            "master": m,
            "fields": fields,
            "full_name": fields.get("full_name", "") or m.get("fio", ""),
            "contract_number": fields.get("contract_number", "") or m.get("contract_number", ""),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        res = await db.contracts.update_one({"id": r.id}, {"$set": upd})
        if res.matched_count:
            updated += 1
    return {"updated": updated}


# ---------- Свои столбцы ----------
class CustomColumnRequest(BaseModel):
    label: str
    section: Optional[str] = "Дополнительно"
    dropdown: Optional[List[str]] = None


@api_router.get("/custom-columns")
async def get_custom_columns():
    return {"columns": await _custom_columns()}


@api_router.post("/custom-columns")
async def add_custom_column(req: CustomColumnRequest):
    label = (req.label or "").strip()
    if not label:
        raise HTTPException(status_code=400, detail="Название столбца обязательно")
    cols = await _custom_columns()
    if any(c.get("label", "").strip().lower() == label.lower() for c in cols):
        raise HTTPException(status_code=400, detail="Столбец с таким названием уже есть")
    col = {
        "key": "cc_" + uuid.uuid4().hex[:8],
        "label": label,
        "section": (req.section or "Дополнительно").strip() or "Дополнительно",
        "dropdown": [str(x) for x in req.dropdown] if req.dropdown else None,
    }
    cols.append(col)
    await _set_setting("custom_columns", cols)
    return col


@api_router.delete("/custom-columns/{key}")
async def delete_custom_column(key: str):
    cols = await _custom_columns()
    new_cols = [c for c in cols if c.get("key") != key]
    await _set_setting("custom_columns", new_cols)
    # заодно чистим зависимости, ссылающиеся на этот столбец
    deps = await _get_setting("dependencies", []) or []
    deps = [d for d in deps if d.get("source") != key]
    await _set_setting("dependencies", deps)
    _rebuild_active_deps(deps)
    return {"deleted": True}


# ---------------------------------------------------------------------------
# Зависимости: столбец -> поле бланка
# ---------------------------------------------------------------------------
DOCUMENT_LABELS = {
    "contract": "Договор найма",
    "forma19": "Форма 19 (прибытие)",
    "forma24": "Талон учёта (Форма 24)",
    "soobshenie": "Сообщение",
    "zayavlenie": "Заявление о регистрации",
}

DOCUMENT_TARGETS = {
    "contract": [
        ("full_name", "ФИО"), ("birth_date", "Дата рождения"), ("citizenship", "Гражданство"),
        ("passport_number", "Паспорт (серия/номер)"), ("passport_issue_date", "Паспорт: дата выдачи"),
        ("passport_valid_until", "Паспорт: действителен до"), ("passport_issued_by", "Паспорт: кем выдан"),
        ("id_number", "Идентификационный номер"), ("phone", "Телефон"),
        ("registration_address", "Адрес регистрации"), ("room_number", "Номер комнаты"),
        ("contract_number", "Номер договора"), ("sign_date", "Дата подписания"),
        ("order_number", "Номер приказа"), ("order_date", "Дата приказа"),
        ("contract_end_date", "Срок договора до"),
    ],
    "forma19": [
        ("surname", "Фамилия"), ("first_name", "Имя"), ("patronymic", "Отчество"),
        ("id_number", "Идентификационный номер"), ("citizenship", "Гражданство"),
        ("res_street", "Улица"), ("res_house", "Дом"), ("res_korpus", "Корпус"),
        ("res_apartment", "Комната/квартира"), ("reg_authority", "Орган регистрации"),
        ("purpose", "Цель приезда"), ("purpose_term", "Срок пребывания"),
        ("employment", "Где и кем работал"), ("arrival_date", "Дата прибытия"),
        ("passport_issued", "Паспорт: кем выдан"),
    ],
    "forma24": [
        ("surname", "Фамилия"), ("first_name", "Имя"), ("patronymic", "Отчество"),
        ("nationality", "Национальность"), ("citizenship", "Гражданство"),
        ("arrival_date", "Дата прибытия"), ("lived_since", "Проживал там с"),
        ("term", "Срок пребывания"), ("prev_work", "Где и кем работал"),
        ("children_count", "Детей до 14 лет"),
    ],
    "soobshenie": [
        ("reg_organ", "Орган регистрации"), ("number", "№ сообщения"), ("fio", "ФИО"),
        ("birth", "Место и год рождения"), ("address", "Адрес"),
        ("issued_by", "Паспорт: кем выдан"), ("chief", "Начальник (ФИО)"),
    ],
    "zayavlenie": [
        ("fio", "ФИО"), ("birth_year", "Год рождения"),
        ("passport_issued_by", "Паспорт: кем выдан"), ("passport_issue_date", "Паспорт: дата выдачи"),
        ("res_street", "Улица"), ("res_house", "Дом"), ("res_korpus", "Корпус"),
        ("res_apartment", "Комната/квартира"), ("stay_term", "Срок пребывания"),
        ("from_place", "Откуда прибыл"), ("basis", "Основание"),
        ("sign_date", "Дата подписания"), ("area", "Общая площадь"),
    ],
}


def _rebuild_active_deps(deps):
    d = {}
    for dep in deps or []:
        doc = dep.get("document")
        tf = dep.get("target_field")
        src = dep.get("source")
        if doc and tf and src:
            d.setdefault(doc, {})[tf] = src
    masterdata.ACTIVE_DEPS = d


async def _load_active_deps():
    deps = await _get_setting("dependencies", []) or []
    _rebuild_active_deps(deps)


class DependencyRequest(BaseModel):
    document: str
    target_field: str
    source: str


@api_router.get("/document-targets/{document}")
async def document_targets(document: str):
    tg = DOCUMENT_TARGETS.get(document)
    if tg is None:
        raise HTTPException(status_code=404, detail="Неизвестный документ")
    return {"document": document, "label": DOCUMENT_LABELS.get(document, document),
            "targets": [{"field": f, "label": l} for f, l in tg]}


@api_router.get("/dependencies")
async def list_dependencies(document: Optional[str] = None):
    deps = await _get_setting("dependencies", []) or []
    if document:
        deps = [d for d in deps if d.get("document") == document]
    # обогащаем метками для удобного отображения
    cols = await _custom_columns()
    key_to_label = {c["key"]: c["header"] for c in masterdata.MASTER_COLUMNS}
    key_to_label.update({c["key"]: c["label"] for c in cols})
    field_labels = {}
    for doc, items in DOCUMENT_TARGETS.items():
        field_labels[doc] = {f: l for f, l in items}
    for d in deps:
        d["source_label"] = key_to_label.get(d.get("source"), d.get("source"))
        d["target_label"] = field_labels.get(d.get("document"), {}).get(
            d.get("target_field"), d.get("target_field"))
    return {"dependencies": deps}


@api_router.post("/dependencies")
async def add_dependency(req: DependencyRequest):
    if req.document not in DOCUMENT_TARGETS:
        raise HTTPException(status_code=400, detail="Неизвестный документ")
    valid_fields = {f for f, _ in DOCUMENT_TARGETS[req.document]}
    if req.target_field not in valid_fields:
        raise HTTPException(status_code=400, detail="Неизвестное поле документа")
    if not (req.source or "").strip():
        raise HTTPException(status_code=400, detail="Не выбран столбец-источник")
    deps = await _get_setting("dependencies", []) or []
    # одна привязка на поле: заменяем предыдущую
    deps = [d for d in deps if not (d.get("document") == req.document
            and d.get("target_field") == req.target_field)]
    dep = {"id": str(uuid.uuid4()), "document": req.document,
           "target_field": req.target_field, "source": req.source}
    deps.append(dep)
    await _set_setting("dependencies", deps)
    _rebuild_active_deps(deps)
    return dep


@api_router.delete("/dependencies/{dep_id}")
async def delete_dependency(dep_id: str):
    deps = await _get_setting("dependencies", []) or []
    deps = [d for d in deps if d.get("id") != dep_id]
    await _set_setting("dependencies", deps)
    _rebuild_active_deps(deps)
    return {"deleted": True}



@api_router.put("/contracts/{contract_id}")
async def update_contract(contract_id: str, req: GenerateRequest):
    existing = await db.contracts.find_one({"id": contract_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Договор не найден")
    update = {
        "fields": req.fields,
        "contract_number": req.fields.get("contract_number", ""),
        "full_name": req.fields.get("full_name", ""),
        "status": (req.status or existing.get("status", "final")),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.contracts.update_one({"id": contract_id}, {"$set": update})
    doc = await db.contracts.find_one({"id": contract_id}, {"_id": 0})
    return doc


@api_router.post("/contracts/batch")
async def create_contracts_batch(req: BatchGenerateRequest):
    created = []
    for i, fields in enumerate(req.contracts):
        master = req.masters[i] if i < len(req.masters) else {}
        contract = await _save_contract(fields, master=master)
        created.append(contract.model_dump())
    return {"created": created, "count": len(created)}


@api_router.post("/generate/upload")
async def generate_upload(file: UploadFile = File(...)):
    """Умная загрузка для «Генерация из Excel».
    Единый шаблон «Данные» → возвращает students(поля договора) + masters(полные данные).
    Старый договорный Excel → как раньше (columns/rows/mapping)."""
    if not file.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=400, detail="Поддерживаются только файлы .xlsx")
    content = await file.read()
    if masterdata.has_master_headers(content):
        people = masterdata.parse_master_xlsx(content)
        if not people:
            raise HTTPException(status_code=400, detail="В шаблоне нет данных (заполните строки с 3-й)")
        students = [masterdata.master_to_contract(m) for m in people]
        return {"mode": "master", "count": len(people),
                "students": students, "masters": people}
    # --- старый договорный формат ---
    try:
        wb = load_workbook(io.BytesIO(content), data_only=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Не удалось прочитать файл: {e}")
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)
    try:
        header_row = next(rows_iter)
    except StopIteration:
        raise HTTPException(status_code=400, detail="Файл пуст")
    columns = [(_cell_to_str(h) or f"Колонка {i+1}") for i, h in enumerate(header_row)]
    rows = []
    for raw in rows_iter:
        if raw is None or all(c is None for c in raw):
            continue
        row = {}
        for i, col in enumerate(columns):
            row[col] = _cell_to_str(raw[i]) if i < len(raw) else ""
        if any(v for v in row.values()):
            rows.append(row)
    mapping = docsvc.auto_map_columns(columns)
    students = _apply_mapping(rows, mapping)
    return {"mode": "contract", "count": len(students),
            "students": students, "masters": [],
            "columns": columns, "rows": rows, "mapping": mapping}


def _contract_master(doc: dict) -> dict:
    """Полные данные человека для пакета: сохранённый master или вывод из полей договора."""
    m = doc.get("master") or {}
    if any(str(v).strip() for v in m.values()):
        return m
    return masterdata.contract_to_master(doc.get("fields", {}) or {})


@api_router.get("/contracts")
async def list_contracts(q: Optional[str] = None, status: Optional[str] = None):
    query = {}
    if status in ("final", "draft"):
        query["status"] = status if status == "draft" else {"$ne": "draft"}
    if q:
        query["$or"] = [
            {"full_name": {"$regex": re.escape(q), "$options": "i"}},
            {"contract_number": {"$regex": re.escape(q), "$options": "i"}},
        ]
    docs = await db.contracts.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return docs


@api_router.get("/contracts/export")
async def export_contracts(q: Optional[str] = None, status: Optional[str] = None):
    """Export the whole contracts history into a single .xlsx registry."""
    query = {}
    if status in ("final", "draft"):
        query["status"] = status if status == "draft" else {"$ne": "draft"}
    if q:
        query["$or"] = [
            {"full_name": {"$regex": re.escape(q), "$options": "i"}},
            {"contract_number": {"$regex": re.escape(q), "$options": "i"}},
        ]
    docs = await db.contracts.find(query, {"_id": 0}).sort("created_at", -1).to_list(5000)

    from openpyxl.styles import Font, PatternFill, Alignment

    wb = Workbook()
    ws = wb.active
    ws.title = "Реестр договоров"

    headers = ["№", "Дата создания", "Статус"] + [f["label"] for f in docsvc.FIELDS]
    ws.append(headers)

    header_fill = PatternFill("solid", fgColor="E11D48")
    header_font = Font(color="FFFFFF", bold=True)
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(vertical="center")

    def fmt_date(iso):
        try:
            return datetime.fromisoformat(iso).strftime("%d.%m.%Y %H:%M")
        except Exception:
            return iso or ""

    for i, doc in enumerate(docs, start=1):
        fields = doc.get("fields", {}) or {}
        status_ru = "Черновик" if doc.get("status") == "draft" else "Готов"
        row = [i, fmt_date(doc.get("created_at", "")), status_ru]
        row += [fields.get(f["key"], "") for f in docsvc.FIELDS]
        ws.append(row)

    # auto-ish column widths
    for col_idx, header in enumerate(headers, start=1):
        max_len = len(str(header))
        for r in range(2, ws.max_row + 1):
            v = ws.cell(row=r, column=col_idx).value
            if v is not None:
                max_len = max(max_len, len(str(v)))
        ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = min(max(max_len + 2, 10), 45)
    ws.freeze_panes = "A2"

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    fname = f"Реестр_договоров_{stamp}.xlsx"
    from urllib.parse import quote
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(fname)}"},
    )


@api_router.get("/contracts/export-base")
async def export_contracts_base(q: Optional[str] = None, status: Optional[str] = None):
    """Скачать ТЕКУЩУЮ базу в формате исходного шаблона «Данные» (все поля, 1 строка = 1 человек).
    Такой файл можно снова загрузить через «Генерация из Excel» — данные не потеряются."""
    query = {}
    if status in ("final", "draft"):
        query["status"] = status if status == "draft" else {"$ne": "draft"}
    if q:
        query["$or"] = [
            {"full_name": {"$regex": re.escape(q), "$options": "i"}},
            {"contract_number": {"$regex": re.escape(q), "$options": "i"}},
        ]
    docs = await db.contracts.find(query, {"_id": 0}).sort("created_at", 1).to_list(100000)

    rows = []
    for d in docs:
        m = dict(d.get("master") or {})
        if not m:
            # запасной вариант — восстановить основное из fields
            f = d.get("fields") or {}
            m = {
                "fio": d.get("full_name", "") or f.get("full_name", ""),
                "contract_number": d.get("contract_number", "") or f.get("contract_number", ""),
                "phone": f.get("phone", ""),
                "room_number": f.get("room_number", ""),
                "id_number": f.get("id_number", ""),
                "order_number": f.get("order_number", ""),
            }
        rows.append(m)

    custom = await _custom_columns()
    extra = [{"key": c["key"], "header": c["label"],
              "dropdown": c.get("dropdown")} for c in custom]
    data = masterdata.build_master_xlsx(data_rows=rows, extra_columns=extra)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    fname = f"База_данные_{stamp}.xlsx"
    from urllib.parse import quote
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(fname)}"},
    )



@api_router.get("/contracts/{contract_id}")
async def get_contract(contract_id: str):
    doc = await db.contracts.find_one({"id": contract_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Договор не найден")
    return doc


@api_router.delete("/contracts/{contract_id}")
async def delete_contract(contract_id: str):
    res = await db.contracts.delete_one({"id": contract_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Договор не найден")
    return {"deleted": True}


def _build_filename(fields: Dict[str, str], ext: str) -> str:
    num = fields.get("contract_number", "")
    name = fields.get("full_name", "")
    base = "Договор"
    if num:
        base += f"_№{num}"
    if name:
        base += f"_{name}"
    return f"{_safe_name(base)}.{ext}"


@api_router.get("/contracts/{contract_id}/download")
async def download_contract(contract_id: str, format: str = "docx"):
    doc = await db.contracts.find_one({"id": contract_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Договор не найден")
    fields = doc["fields"]
    docx_bytes = await _render(fields)
    if format == "pdf":
        try:
            data = docsvc.convert_to_pdf(docx_bytes)
        except Exception as e:
            logger.exception("PDF conversion failed")
            raise HTTPException(status_code=500, detail=f"Ошибка конвертации в PDF: {e}")
        media = "application/pdf"
        filename = _build_filename(fields, "pdf")
    else:
        data = docx_bytes
        media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = _build_filename(fields, "docx")
    from urllib.parse import quote
    return StreamingResponse(
        io.BytesIO(data),
        media_type=media,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@api_router.post("/contracts/preview")
async def preview_contract(req: GenerateRequest, format: str = "docx"):
    """Generate a downloadable document without saving to history."""
    docx_bytes = await _render(req.fields)
    if format == "pdf":
        try:
            data = docsvc.convert_to_pdf(docx_bytes)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка конвертации в PDF: {e}")
        media = "application/pdf"
        filename = _build_filename(req.fields, "pdf")
    else:
        data = docx_bytes
        media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = _build_filename(req.fields, "docx")
    from urllib.parse import quote
    return StreamingResponse(
        io.BytesIO(data),
        media_type=media,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@api_router.post("/contracts/batch-download")
async def batch_download(req: BatchDownloadRequest):
    docs = await db.contracts.find({"id": {"$in": req.ids}}, {"_id": 0}).to_list(1000)
    if not docs:
        raise HTTPException(status_code=404, detail="Договоры не найдены")
    zip_buf = io.BytesIO()
    used = set()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for doc in docs:
            fields = doc["fields"]
            docx_bytes = await _render(fields)
            if req.format == "pdf":
                try:
                    data = docsvc.convert_to_pdf(docx_bytes)
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Ошибка конвертации в PDF: {e}")
                fname = _build_filename(fields, "pdf")
            else:
                data = docx_bytes
                fname = _build_filename(fields, "docx")
            # avoid duplicate names in zip
            orig = fname
            n = 1
            while fname in used:
                stem, ext = orig.rsplit(".", 1)
                fname = f"{stem}_{n}.{ext}"
                n += 1
            used.add(fname)
            zf.writestr(fname, data)
    zip_buf.seek(0)
    return StreamingResponse(
        zip_buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=contracts.zip"},
    )


@api_router.post("/contracts/batch-print")
async def batch_print(req: BatchDownloadRequest):
    docs = await db.contracts.find({"id": {"$in": req.ids}}, {"_id": 0}).to_list(1000)
    if not docs:
        raise HTTPException(status_code=404, detail="Договоры не найдены")
    by_id = {d["id"]: d for d in docs}
    pdfs = []
    for cid in req.ids:  # preserve selection order
        doc = by_id.get(cid)
        if not doc:
            continue
        docx_bytes = await _render(doc["fields"])
        try:
            pdfs.append(docsvc.convert_to_pdf(docx_bytes))
        except Exception as e:
            logger.exception("PDF conversion failed")
            raise HTTPException(status_code=500, detail=f"Ошибка конвертации в PDF: {e}")
    merged = docsvc.merge_pdfs(pdfs)
    return StreamingResponse(
        io.BytesIO(merged),
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=contracts.pdf"},
    )


@api_router.post("/contracts/manual-duplex")
async def manual_duplex(req: ManualDuplexRequest):
    """Manual double-sided printing on a single-sided printer (batch).

    Returns one merged PDF for the requested side: 'front' (odd pages of every
    document) or 'back' (even pages). Each document is padded to an even number
    of pages so documents never share a sheet.
    """
    docs = await db.contracts.find({"id": {"$in": req.ids}}, {"_id": 0}).to_list(5000)
    if not docs:
        raise HTTPException(status_code=404, detail="Договоры не найдены")
    by_id = {d["id"]: d for d in docs}
    pdfs = []
    for cid in req.ids:  # preserve selection order
        doc = by_id.get(cid)
        if not doc:
            continue
        docx_bytes = await _render(doc["fields"])
        try:
            pdfs.append(docsvc.convert_to_pdf(docx_bytes))
        except Exception as e:
            logger.exception("PDF conversion failed")
            raise HTTPException(status_code=500, detail=f"Ошибка конвертации в PDF: {e}")
    side = req.side if req.side in ("front", "back") else "front"
    back_order = req.back_order if req.back_order in ("reversed", "normal") else "reversed"
    labels = []
    for cid in req.ids:
        doc = by_id.get(cid)
        if not doc:
            continue
        f = doc.get("fields", {}) or {}
        labels.append({"number": f.get("contract_number", ""), "name": f.get("full_name", "")})
    data = docsvc.build_manual_duplex(
        pdfs, side=side, back_order=back_order, separators=bool(req.separators),
        labels=labels, orientation=("landscape" if req.orientation == "landscape" else "portrait"),
        flip_edge=("short" if req.flip_edge == "short" else "long"),
    )
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=duplex_{side}.pdf"},
    )


@api_router.get("/print-test")
async def print_test(side: str = "front", orientation: str = "portrait"):
    """One-sheet duplex orientation test page (front/back)."""
    side = side if side in ("front", "back") else "front"
    orientation = "landscape" if orientation == "landscape" else "portrait"
    data = docsvc.build_test_sheet(side, orientation=orientation)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=test_{side}.pdf"},
    )


# ---------- Presets ----------
@api_router.get("/presets")
async def list_presets():
    docs = await db.presets.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return docs


@api_router.post("/presets")
async def create_preset(req: PresetRequest):
    name = (req.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Укажите название пресета")
    preset = Preset(name=name, fields=req.fields)
    await db.presets.insert_one(preset.model_dump())
    return preset.model_dump()


@api_router.delete("/presets/{preset_id}")
async def delete_preset(preset_id: str):
    res = await db.presets.delete_one({"id": preset_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Пресет не найден")
    return {"deleted": True}


# ---------- Demo data ----------
DEMO_STUDENTS = [
    {"contract_number": "0047390 003371", "sign_date": "« 21 » июля 2026", "order_number": "228",
     "order_date": "«21» июля 2026", "citizenship": "Туркменистана", "full_name": "Шаназаров Мырат",
     "birth_date": "15.05.2007", "room_number": "302/2", "contract_end_date": "30.06.2028",
     "registration_address": "пр-т Дзержинского, 85, ком. 302/2", "passport_number": "A3058202",
     "passport_issue_date": "08.01.2025", "passport_valid_until": "07.01.2030",
     "passport_issued_by": "Государственной Миграционной Службой Туркменистана",
     "id_number": "LB00258610", "phone": "+37529354-11-59"},
    {"contract_number": "0047390 003372", "sign_date": "« 21 » июля 2026", "order_number": "229",
     "order_date": "«21» июля 2026", "citizenship": "Республики Казахстан", "full_name": "Ахметова Дана Ержановна",
     "birth_date": "03.02.2006", "room_number": "214/1", "contract_end_date": "30.06.2028",
     "registration_address": "пр-т Дзержинского, 85, ком. 214/1", "passport_number": "N12345678",
     "passport_issue_date": "12.09.2023", "passport_valid_until": "11.09.2033",
     "passport_issued_by": "МВД Республики Казахстан", "id_number": "060203500123", "phone": "+37533112-45-88"},
    {"contract_number": "0047390 003373", "sign_date": "« 22 » июля 2026", "order_number": "230",
     "order_date": "«22» июля 2026", "citizenship": "Республики Узбекистан", "full_name": "Рахимов Азиз Шухратович",
     "birth_date": "19.11.2005", "room_number": "410/3", "contract_end_date": "30.06.2029",
     "registration_address": "пр-т Дзержинского, 85, ком. 410/3", "passport_number": "AB1234567",
     "passport_issue_date": "05.04.2022", "passport_valid_until": "04.04.2032",
     "passport_issued_by": "ГУВД г. Ташкента", "id_number": "51911055230018", "phone": "+37544778-90-12"},
    {"contract_number": "0047390 003374", "sign_date": "« 23 » июля 2026", "order_number": "231",
     "order_date": "«23» июля 2026", "citizenship": "Российской Федерации", "full_name": "Смирнова Елена Викторовна",
     "birth_date": "27.07.2006", "room_number": "118/2", "contract_end_date": "30.06.2028",
     "registration_address": "пр-т Дзержинского, 85, ком. 118/2", "passport_number": "4510 123456",
     "passport_issue_date": "01.08.2022", "passport_valid_until": "27.07.2026",
     "passport_issued_by": "УМВД России по г. Москве", "id_number": "770-123-456 78", "phone": "+37529555-33-21"},
    {"contract_number": "0047390 003375", "sign_date": "« 23 » июля 2026", "order_number": "232",
     "order_date": "«23» июля 2026", "citizenship": "Республики Таджикистан", "full_name": "Назаров Фаррух Далерович",
     "birth_date": "08.03.2005", "room_number": "305/1", "contract_end_date": "30.06.2029",
     "registration_address": "пр-т Дзержинского, 85, ком. 305/1", "passport_number": "40 1234567",
     "passport_issue_date": "14.06.2021", "passport_valid_until": "13.06.2031",
     "passport_issued_by": "МВД Республики Таджикистан", "id_number": "A0123456", "phone": "+37525667-11-04"},
    {"contract_number": "0047390 003376", "sign_date": "« 24 » июля 2026", "order_number": "233",
     "order_date": "«24» июля 2026", "citizenship": "Азербайджанской Республики", "full_name": "Алиев Кямран Эльшанович",
     "birth_date": "22.12.2006", "room_number": "222/4", "contract_end_date": "30.06.2028",
     "registration_address": "пр-т Дзержинского, 85, ком. 222/4", "passport_number": "C01234567",
     "passport_issue_date": "30.10.2023", "passport_valid_until": "29.10.2033",
     "passport_issued_by": "Государственной Миграционной Службой Азербайджана",
     "id_number": "AZE0123456", "phone": "+37529901-22-33"},
]


@api_router.post("/seed-demo")
async def seed_demo():
    existing = await db.contracts.count_documents({"demo": True})
    if existing > 0:
        return {"created": 0, "already": existing, "message": "Демо-данные уже загружены"}
    created = 0
    for i, s in enumerate(DEMO_STUDENTS):
        # last two entries are saved as drafts to showcase the drafts flow
        status = "draft" if i >= len(DEMO_STUDENTS) - 2 else "final"
        c = Contract(
            contract_number=s.get("contract_number", ""),
            full_name=s.get("full_name", ""),
            fields=s,
            status=status,
            demo=True,
        )
        await db.contracts.insert_one(c.model_dump())
        created += 1
    return {"created": created, "message": f"Загружено демо-договоров: {created}"}


@api_router.delete("/seed-demo")
async def clear_demo():
    res = await db.contracts.delete_many({"demo": True})
    return {"deleted": res.deleted_count}


# ---------- Custom templates (the built-in template is NEVER modified) ----------
_PAGECOUNT_CACHE = {}


@api_router.get("/templates")
async def list_templates():
    s = await db.app_settings.find_one({"key": "active_template"})
    active = s.get("value") if s else "default"
    items = [{"id": "default", "name": "Стандартный (встроенный)", "builtin": True,
              "active": active == "default"}]
    docs = await db.templates.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    for d in docs:
        items.append({"id": d["id"], "name": d.get("name", "Шаблон"), "builtin": False,
                      "active": active == d["id"], "created_at": d.get("created_at")})
    return items


@api_router.post("/templates")
async def upload_template(file: UploadFile = File(...)):
    name = file.filename or "template.docx"
    if not name.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Нужен файл .docx")
    tid = str(uuid.uuid4())
    fname = f"{tid}.docx"
    (UPLOAD_DIR / fname).write_bytes(await file.read())
    doc = {"id": tid, "name": name, "filename": fname,
           "created_at": datetime.now(timezone.utc).isoformat()}
    await db.templates.insert_one(doc)
    _PAGECOUNT_CACHE.pop(tid, None)
    return {"id": tid, "name": name, "builtin": False, "active": False}


@api_router.post("/templates/{template_id}/activate")
async def activate_template(template_id: str):
    if template_id != "default":
        t = await db.templates.find_one({"id": template_id})
        if not t:
            raise HTTPException(status_code=404, detail="Шаблон не найден")
    await db.app_settings.update_one({"key": "active_template"},
                                     {"$set": {"value": template_id}}, upsert=True)
    return {"active": template_id}


@api_router.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    if template_id == "default":
        raise HTTPException(status_code=400, detail="Встроенный шаблон удалить нельзя")
    t = await db.templates.find_one({"id": template_id})
    if not t:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    try:
        (UPLOAD_DIR / t["filename"]).unlink(missing_ok=True)
    except Exception:
        pass
    await db.templates.delete_one({"id": template_id})
    s = await db.app_settings.find_one({"key": "active_template"})
    if s and s.get("value") == template_id:
        await db.app_settings.update_one({"key": "active_template"},
                                         {"$set": {"value": "default"}}, upsert=True)
    return {"deleted": True}


@api_router.get("/template-info")
async def template_info():
    """Pages produced by the active template (for paper estimate). Cached."""
    tpl = await _active_tpl()
    key = tpl or "default"
    if key in _PAGECOUNT_CACHE:
        return {"pages_per_doc": _PAGECOUNT_CACHE[key]}
    pages = 2
    try:
        docx_bytes = docsvc.render_docx({}, tpl)
        pdf = docsvc.convert_to_pdf(docx_bytes)
        from pypdf import PdfReader
        pages = max(1, len(PdfReader(io.BytesIO(pdf)).pages))
        _PAGECOUNT_CACHE[key] = pages
    except Exception:
        logger.exception("template-info failed")
    return {"pages_per_doc": pages}


# ---------- Printer profiles (saved duplex settings) ----------
class PrintProfileRequest(BaseModel):
    name: str
    settings: Dict[str, Any]


@api_router.get("/print-profiles")
async def list_print_profiles():
    return await db.print_profiles.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)


@api_router.post("/print-profiles")
async def create_print_profile(req: PrintProfileRequest):
    name = (req.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Укажите название профиля")
    doc = {"id": str(uuid.uuid4()), "name": name, "settings": req.settings,
           "created_at": datetime.now(timezone.utc).isoformat()}
    await db.print_profiles.insert_one(doc)
    return {k: v for k, v in doc.items() if k != "_id"}


@api_router.delete("/print-profiles/{profile_id}")
async def delete_print_profile(profile_id: str):
    res = await db.print_profiles.delete_one({"id": profile_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    return {"deleted": True}


# ---------- Overlay printing (печать на готовом бланке) ----------
class OverlayGenerateRequest(BaseModel):
    records: List[Dict[str, Any]] = []
    layout: Optional[List[Dict[str, Any]]] = None
    dx_mm: float = 0.0
    dy_mm: float = 0.0
    with_background: bool = False
    with_form: bool = False
    page_size: str = "card"  # "card" (147x103) | "a4"
    rotate: int = 0          # 0/90/180/270 — how the blank is fed into the printer
    a4_position: str = "top-left"  # A4 carrier placement (page_size="a4")
    # Full-document print (grid of complete forms on real A4 pages):
    mode: str = "overlay"        # "overlay" | "full"
    orientation: str = "portrait"  # full mode: "portrait" (2/sheet) | "landscape" (4/sheet)
    per_sheet: int = 0            # full mode: cards per sheet (0 = max)


def _build_overlay_pdf(req: "OverlayGenerateRequest") -> bytes:
    """Route an overlay request to the right builder (overlay-on-blank or full)."""
    if str(getattr(req, "mode", "overlay")).lower() == "full":
        return docsvc.build_full_sheets(
            records=req.records,
            layout=req.layout,
            orientation=req.orientation,
            per_sheet=req.per_sheet,
        )
    return docsvc.build_overlay(
        records=req.records,
        layout=req.layout,
        page_size=req.page_size,
        dx_mm=req.dx_mm,
        dy_mm=req.dy_mm,
        with_background=req.with_background,
        with_form=req.with_form,
        rotate=req.rotate,
        a4_position=req.a4_position,
    )


class OverlayLayoutSave(BaseModel):
    layout: List[Dict[str, Any]]
    dx_mm: float = 0.0
    dy_mm: float = 0.0
    rotate: int = 0


@api_router.get("/overlay/layout")
async def get_overlay_layout():
    """Return saved field layout + calibration, or the built-in default."""
    s = await db.app_settings.find_one({"key": "overlay_layout"})
    if s and s.get("value"):
        v = s["value"]
        return {
            "layout": v.get("layout", docsvc.SOOBSHENIE_LAYOUT),
            "dx_mm": v.get("dx_mm", 0.0),
            "dy_mm": v.get("dy_mm", 0.0),
            "rotate": v.get("rotate", 0),
            "page_mm": list(docsvc.SOOBSHENIE_PAGE_MM),
        }
    return {
        "layout": docsvc.SOOBSHENIE_LAYOUT,
        "dx_mm": 0.0,
        "dy_mm": 0.0,
        "rotate": 0,
        "page_mm": list(docsvc.SOOBSHENIE_PAGE_MM),
    }


@api_router.post("/overlay/layout")
async def save_overlay_layout(req: OverlayLayoutSave):
    value = {"layout": req.layout, "dx_mm": req.dx_mm, "dy_mm": req.dy_mm, "rotate": req.rotate}
    await db.app_settings.update_one(
        {"key": "overlay_layout"},
        {"$set": {"key": "overlay_layout", "value": value,
                  "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return {"saved": True, **value}


# ---------- Overlay placement PROFILES (несколько раскладок под бланк) ----------
class OverlayProfileIn(BaseModel):
    name: str = "Профиль"
    layout: List[Dict[str, Any]] = []
    dx_mm: float = 0.0
    dy_mm: float = 0.0
    rotate: int = 0
    constants: Dict[str, Any] = {}  # {field_key: {"value": str, "locked": bool}}


def _profile_public(p: dict) -> dict:
    return {
        "id": p.get("id"),
        "name": p.get("name", "Профиль"),
        "layout": p.get("layout", []),
        "dx_mm": p.get("dx_mm", 0.0),
        "dy_mm": p.get("dy_mm", 0.0),
        "rotate": p.get("rotate", 0),
        "constants": p.get("constants", {}) or {},
    }


async def _ensure_default_profile():
    """Seed a first profile from the legacy overlay_layout setting (or defaults)
    so the profiles UI always has something to show."""
    count = await db.overlay_profiles.count_documents({})
    if count > 0:
        return
    legacy = await db.app_settings.find_one({"key": "overlay_layout"})
    v = (legacy or {}).get("value", {}) or {}
    now = datetime.now(timezone.utc).isoformat()
    prof = {
        "id": str(uuid.uuid4()),
        "name": "Профиль 1",
        "layout": v.get("layout", docsvc.SOOBSHENIE_LAYOUT),
        "dx_mm": v.get("dx_mm", 0.0),
        "dy_mm": v.get("dy_mm", 0.0),
        "rotate": v.get("rotate", 0),
        "constants": {},
        "created_at": now,
        "updated_at": now,
    }
    await db.overlay_profiles.insert_one(prof)
    await db.app_settings.update_one(
        {"key": "overlay_active_profile"},
        {"$set": {"key": "overlay_active_profile", "value": prof["id"], "updated_at": now}},
        upsert=True,
    )


@api_router.get("/overlay/profiles")
async def list_overlay_profiles():
    await _ensure_default_profile()
    docs = await db.overlay_profiles.find().sort("created_at", 1).to_list(1000)
    active = await db.app_settings.find_one({"key": "overlay_active_profile"})
    active_id = (active or {}).get("value") or (docs[0]["id"] if docs else None)
    return {"profiles": [_profile_public(d) for d in docs], "active_id": active_id}


@api_router.post("/overlay/profiles")
async def create_overlay_profile(req: OverlayProfileIn):
    now = datetime.now(timezone.utc).isoformat()
    prof = {
        "id": str(uuid.uuid4()),
        "name": (req.name or "Профиль").strip() or "Профиль",
        "layout": req.layout or docsvc.SOOBSHENIE_LAYOUT,
        "dx_mm": req.dx_mm,
        "dy_mm": req.dy_mm,
        "rotate": req.rotate,
        "constants": req.constants or {},
        "created_at": now,
        "updated_at": now,
    }
    await db.overlay_profiles.insert_one(prof)
    await db.app_settings.update_one(
        {"key": "overlay_active_profile"},
        {"$set": {"key": "overlay_active_profile", "value": prof["id"], "updated_at": now}},
        upsert=True,
    )
    return _profile_public(prof)


@api_router.put("/overlay/profiles/{pid}")
async def update_overlay_profile(pid: str, req: OverlayProfileIn):
    now = datetime.now(timezone.utc).isoformat()
    upd = {
        "name": (req.name or "Профиль").strip() or "Профиль",
        "layout": req.layout,
        "dx_mm": req.dx_mm,
        "dy_mm": req.dy_mm,
        "rotate": req.rotate,
        "constants": req.constants or {},
        "updated_at": now,
    }
    res = await db.overlay_profiles.update_one({"id": pid}, {"$set": upd})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    doc = await db.overlay_profiles.find_one({"id": pid})
    return _profile_public(doc)


@api_router.delete("/overlay/profiles/{pid}")
async def delete_overlay_profile(pid: str):
    total = await db.overlay_profiles.count_documents({})
    if total <= 1:
        raise HTTPException(status_code=400, detail="Нельзя удалить последний профиль")
    res = await db.overlay_profiles.delete_one({"id": pid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    # if the active profile was removed, activate the first remaining one
    active = await db.app_settings.find_one({"key": "overlay_active_profile"})
    if (active or {}).get("value") == pid:
        first = await db.overlay_profiles.find().sort("created_at", 1).to_list(1)
        if first:
            await db.app_settings.update_one(
                {"key": "overlay_active_profile"},
                {"$set": {"value": first[0]["id"]}},
                upsert=True,
            )
    return {"deleted": True}


class ActiveProfileIn(BaseModel):
    id: str


@api_router.post("/overlay/active-profile")
async def set_active_overlay_profile(req: ActiveProfileIn):
    exists = await db.overlay_profiles.find_one({"id": req.id})
    if not exists:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    await db.app_settings.update_one(
        {"key": "overlay_active_profile"},
        {"$set": {"key": "overlay_active_profile", "value": req.id,
                  "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return {"active_id": req.id}




@api_router.post("/overlay/generate")
async def generate_overlay(req: OverlayGenerateRequest):
    """PDF of the СООБЩЕНИЕ. mode="overlay" -> data sized to the physical blank
    (147×103, optional rotation); mode="full" -> complete forms as an A4 grid."""
    try:
        data = _build_overlay_pdf(req)
    except Exception as e:
        logger.exception("overlay generation failed")
        raise HTTPException(status_code=500, detail=f"Ошибка формирования: {e}")
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=soobshenie_overlay.pdf"},
    )


@api_router.post("/overlay/preview-png")
async def overlay_preview_png(req: OverlayGenerateRequest):
    """Render the first sheet of the overlay/full-print output as a PNG image,
    so the on-screen preview shows reliably even where inline PDF is blocked."""
    try:
        pdf = _build_overlay_pdf(req)
        png = docsvc.render_pdf_first_page_png(pdf, scale=2.0)
    except Exception as e:
        logger.exception("overlay preview failed")
        raise HTTPException(status_code=500, detail=f"Ошибка предпросмотра: {e}")
    return Response(content=png, media_type="image/png",
                    headers={"Cache-Control": "no-store"})


class OverlayPrintRequest(OverlayGenerateRequest):
    printer_name: str = ""


@api_router.get("/printers")
async def list_printers_endpoint():
    """Local printers (Windows desktop app only). supported=false in the web version."""
    return {"supported": docsvc.printing_supported(), "printers": docsvc.list_printers()}


@api_router.get("/health/diagnostics")
async def health_diagnostics():
    """Self-check for the «Проверка системы» screen: MongoDB, fonts, assets,
    template, LibreOffice, PDF generation and printers. Runs on the machine
    where the backend is running (the user's PC in the desktop app)."""
    checks = docsvc.run_diagnostics()
    mongo_ok, mongo_detail = False, ""
    try:
        await db.command("ping")
        mongo_ok, mongo_detail = True, "Подключение активно"
    except Exception as e:  # pragma: no cover
        mongo_detail = str(e)
    checks.insert(0, {"key": "mongo", "label": "База данных (MongoDB)",
                      "ok": mongo_ok, "detail": mongo_detail})
    all_ok = all(c.get("ok") for c in checks)
    return {
        "checks": checks,
        "all_ok": all_ok,
        "is_desktop": docsvc.printing_supported(),
        "platform": sys.platform,
    }



@api_router.post("/overlay/print-silent")
async def overlay_print_silent(req: OverlayPrintRequest):
    """Print the overlay straight to a local printer at actual size — no dialog.
    Available only in the Windows desktop app (backend runs on the user's machine)."""
    if not docsvc.printing_supported():
        raise HTTPException(
            status_code=400,
            detail="Тихая печать доступна только в установленном Windows-приложении.",
        )
    if not req.records:
        raise HTTPException(status_code=400, detail="Нет данных для печати")
    try:
        data = _build_overlay_pdf(req)
        docsvc.print_pdf_silent(data, req.printer_name)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("silent print failed")
        raise HTTPException(status_code=500, detail=f"Ошибка печати: {e}")
    return {"printed": True, "printer": req.printer_name or "по умолчанию", "pages": len(req.records)}


@api_router.get("/overlay/test-sheet")
async def overlay_test_sheet(dx: float = 0.0, dy: float = 0.0, page_size: str = "card", rotate: int = 0):
    data = docsvc.build_overlay_test_sheet(page_size=page_size, dx_mm=dx, dy_mm=dy, rotate=rotate)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=overlay_test.pdf"},
    )


@api_router.get("/overlay/carrier-frame")
async def overlay_carrier_frame(a4_position: str = "top-left"):
    """A4 sheet with an empty 147x103 outline (+ corner marks) to tape the
    pre-printed blank into, for repeatable registration."""
    data = docsvc.build_carrier_frame(a4_position=a4_position)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=carrier_frame.pdf"},
    )


@api_router.get("/overlay/background")
async def overlay_background():
    """Scanned blank image used as the editor backdrop."""
    p = ROOT_DIR / "assets" / "soobshenie_blank.png"
    if not p.exists():
        raise HTTPException(status_code=404, detail="Фон не найден")
    return FileResponse(str(p), media_type="image/png")


@api_router.get("/overlay/form-background")
async def overlay_form_background():
    """Clean vector СООБЩЕНИЕ form (no data) — used by «Полная печать» preview.

    Unlike /overlay/background (a scanned photo, used only in the overlay-on-blank
    mode), this returns the typed document exactly as it will be printed on plain
    paper, so the full-print preview no longer relies on the scanned photo."""
    try:
        png = docsvc.render_form_background_png()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Не удалось отрисовать бланк: {e}")
    return Response(content=png, media_type="image/png",
                    headers={"Cache-Control": "public, max-age=86400"})


# ---------- App config (e.g. Windows installer download link) ----------
class AppConfig(BaseModel):
    windows_download_url: str = ""


@api_router.get("/app-config")
async def get_app_config():
    s = await db.app_settings.find_one({"key": "app_config"})
    v = (s or {}).get("value", {}) or {}
    return {"windows_download_url": v.get("windows_download_url", "")}


@api_router.post("/app-config")
async def set_app_config(cfg: AppConfig):
    value = {"windows_download_url": (cfg.windows_download_url or "").strip()}
    await db.app_settings.update_one(
        {"key": "app_config"},
        {"$set": {"key": "app_config", "value": value,
                  "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return {"saved": True, **value}


# ---------- Reg-authority profile (auto-fills the СООБЩЕНИЕ blank) ----------
class RegProfile(BaseModel):
    reg_organ: str = ""
    chief: str = ""
    city: str = ""


@api_router.get("/reg-profile")
async def get_reg_profile():
    s = await db.app_settings.find_one({"key": "reg_profile"})
    v = (s or {}).get("value", {}) or {}
    return {
        "reg_organ": v.get("reg_organ", ""),
        "chief": v.get("chief", ""),
        "city": v.get("city", ""),
    }


@api_router.post("/reg-profile")
async def set_reg_profile(p: RegProfile):
    value = {
        "reg_organ": (p.reg_organ or "").strip(),
        "chief": (p.chief or "").strip(),
        "city": (p.city or "").strip(),
    }
    await db.app_settings.update_one(
        {"key": "reg_profile"},
        {"$set": {"key": "reg_profile", "value": value,
                  "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return {"saved": True, **value}


# ---------- Desktop version & auto-update ----------
try:
    import _buildinfo as buildinfo  # generated by CI; dev fallback in repo
except Exception:  # pragma: no cover
    class buildinfo:  # type: ignore
        VERSION = "dev"
        BUILD_TIME = ""
        GIT_SHA = "dev"
        REPO = ""

# Set by the desktop entrypoint so an in-app update can stop MongoDB and quit
# the process cleanly, letting the installer replace the files.
_SHUTDOWN_HOOK = None

# Keep-alive: the desktop UI (Edge --app window) pings periodically; when it
# stops (window closed) the idle watchdog shuts the local server down. This is
# ONLY armed by the desktop entrypoint — the web/VPS server never auto-exits.
import time as _time
_LAST_PING = _time.time()
_GOT_FIRST_PING = False


@api_router.get("/_ping")
async def keepalive_ping():
    global _LAST_PING, _GOT_FIRST_PING
    _LAST_PING = _time.time()
    _GOT_FIRST_PING = True
    return {"ok": True}


def start_idle_watchdog(timeout: float = 30.0, initial_grace: float = 180.0):
    """Desktop-only: exit the process if no keep-alive ping arrives within
    `timeout` seconds (i.e. the app window was closed).

    `initial_grace`: on the very FIRST launch the Edge/Chrome window with a
    fresh profile can take a long time to cold-start before the UI sends its
    first ping. Until that first ping arrives we wait up to `initial_grace`
    seconds instead of `timeout`, so a slow first start is never mistaken for
    a closed window (which caused ERR_CONNECTION_REFUSED after ~30s)."""
    global _LAST_PING
    _LAST_PING = _time.time()
    import threading

    def _loop():
        start = _time.time()
        while True:
            _time.sleep(5)
            now = _time.time()
            if not _GOT_FIRST_PING:
                # still waiting for the window to finish loading the UI
                if now - start > initial_grace:
                    try:
                        if _SHUTDOWN_HOOK:
                            _SHUTDOWN_HOOK()
                    except Exception:
                        pass
                    os._exit(0)
                continue
            if now - _LAST_PING > timeout:
                try:
                    if _SHUTDOWN_HOOK:
                        _SHUTDOWN_HOOK()
                except Exception:
                    pass
                os._exit(0)

    threading.Thread(target=_loop, daemon=True).start()


def set_shutdown_hook(fn):
    global _SHUTDOWN_HOOK
    _SHUTDOWN_HOOK = fn


def _is_desktop() -> bool:
    """True when running as the packaged PyInstaller desktop build."""
    return bool(getattr(sys, "frozen", False))


def _github_latest_release():
    """Fetch the latest GitHub release metadata for the configured repo.
    Returns dict or None."""
    repo = (getattr(buildinfo, "REPO", "") or "").strip()
    if not repo:
        return None
    import requests
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    r = requests.get(url, headers={"Accept": "application/vnd.github+json"}, timeout=15)
    if r.status_code != 200:
        return None
    return r.json()


def _find_installer_asset(release: dict):
    for a in (release or {}).get("assets", []) or []:
        name = (a.get("name") or "").lower()
        if name.endswith(".exe") and "setup" in name:
            return a
    # fallback: first .exe asset
    for a in (release or {}).get("assets", []) or []:
        if (a.get("name") or "").lower().endswith(".exe"):
            return a
    return None


@api_router.get("/app-version")
async def app_version():
    return {
        "version": getattr(buildinfo, "VERSION", "dev"),
        "build_time": getattr(buildinfo, "BUILD_TIME", ""),
        "git_sha": getattr(buildinfo, "GIT_SHA", "dev"),
        "repo": getattr(buildinfo, "REPO", ""),
        "is_desktop": _is_desktop(),
    }


@api_router.get("/updates/check")
async def updates_check():
    """Check GitHub Releases for a newer desktop build. Online-only feature."""
    repo = (getattr(buildinfo, "REPO", "") or "").strip()
    result = {
        "supported": _is_desktop() and bool(repo),
        "current_version": getattr(buildinfo, "VERSION", "dev"),
        "current_build_time": getattr(buildinfo, "BUILD_TIME", ""),
        "update_available": False,
        "latest_version": "",
        "published_at": "",
        "download_url": "",
        "notes": "",
    }
    if not repo:
        result["error"] = "Репозиторий обновлений не задан в сборке."
        return result
    try:
        rel = _github_latest_release()
        if not rel:
            result["error"] = "Не удалось получить сведения о релизе."
            return result
        asset = _find_installer_asset(rel)
        result["latest_version"] = rel.get("tag_name") or rel.get("name") or ""
        result["published_at"] = rel.get("published_at") or ""
        result["notes"] = rel.get("body") or ""
        if asset:
            result["download_url"] = asset.get("browser_download_url") or ""
        # Determine "newer": compare our build time with the release/asset time.
        cur = (getattr(buildinfo, "BUILD_TIME", "") or "").strip()
        remote = (asset.get("updated_at") if asset else "") or rel.get("published_at") or ""
        if not cur:
            # dev build with no timestamp -> treat any published release as newer
            result["update_available"] = bool(result["download_url"])
        elif remote and remote > cur:
            result["update_available"] = bool(result["download_url"])
    except Exception as e:
        logger.exception("updates_check failed")
        result["error"] = f"Ошибка проверки обновлений: {e}"
    return result


class ApplyUpdateRequest(BaseModel):
    download_url: str = ""


@api_router.post("/updates/apply")
async def updates_apply(req: ApplyUpdateRequest):
    """Download the latest installer and launch it, then quit the app so the
    installer can replace files. Desktop-only, online-only."""
    if not _is_desktop():
        raise HTTPException(status_code=400, detail="Обновление доступно только в установленном приложении.")
    url = (req.download_url or "").strip()
    if not url:
        # resolve from GitHub if not provided
        rel = _github_latest_release()
        asset = _find_installer_asset(rel) if rel else None
        url = (asset.get("browser_download_url") if asset else "") or ""
    if not url:
        raise HTTPException(status_code=400, detail="Не найдена ссылка на установщик обновления.")
    import tempfile, subprocess, threading, requests
    try:
        tmp = Path(tempfile.gettempdir()) / "BanetskayaSetup_update.exe"
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 16):
                    if chunk:
                        f.write(chunk)
        if tmp.stat().st_size < 1_000_000:
            raise RuntimeError("Загруженный файл слишком мал — установщик повреждён.")
        # Launch installer (interactive), then quit this app shortly after.
        subprocess.Popen([str(tmp)], close_fds=True)

        def _quit():
            import time as _t
            _t.sleep(1.5)
            try:
                if _SHUTDOWN_HOOK:
                    _SHUTDOWN_HOOK()
            except Exception:
                pass
            os._exit(0)

        threading.Thread(target=_quit, daemon=True).start()
        return {"started": True, "installer": str(tmp)}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("updates_apply failed")
        raise HTTPException(status_code=500, detail=f"Ошибка обновления: {e}")


# ======================= ФОРМА 19 — Адресный листок прибытия =======================
class Forma19Request(BaseModel):
    records: List[Dict[str, Any]] = []      # список людей (поля FORMA19)
    duplex_flip: str = "long"               # "long" | "short"
    side: str = "front"                     # предпросмотр: "front" | "back"


@api_router.get("/forma19/fields")
async def forma19_fields():
    """Сгруппированный список полей Формы 19 для формы ввода."""
    return {"groups": docsvc.FORMA19_FIELDS, "keys": docsvc.FORMA19_FIELD_KEYS}


@api_router.get("/forma19/defaults")
async def forma19_get_defaults():
    """Постоянные значения (константы), которые пользователь задаёт один раз
    и применяет ко всем листкам (адрес общежития, орган регистрации и т.п.)."""
    doc = await db.app_settings.find_one({"key": "forma19_defaults"}, {"_id": 0})
    return {"defaults": (doc or {}).get("value", {})}


class Forma19Defaults(BaseModel):
    defaults: Dict[str, Any] = {}


@api_router.post("/forma19/defaults")
async def forma19_save_defaults(payload: Forma19Defaults):
    await db.app_settings.update_one(
        {"key": "forma19_defaults"},
        {"$set": {"key": "forma19_defaults", "value": payload.defaults}},
        upsert=True,
    )
    return {"saved": True, "defaults": payload.defaults}


class Forma19Prefill(BaseModel):
    students: List[Dict[str, Any]] = []     # student dicts (поля договора)


@api_router.post("/forma19/prefill")
async def forma19_prefill(payload: Forma19Prefill):
    """Пред-заполнение полей Формы 19 из данных студентов (поля договора):
    разбивает ФИО/дату рождения/паспорт на компоненты."""
    out = [docsvc.forma19_from_contract(s) for s in payload.students]
    return {"records": out}


def _build_forma19_pdf(req: "Forma19Request", template=None) -> bytes:
    return docsvc.build_forma19(
        people=req.records,
        duplex_flip=req.duplex_flip,
        template=template,
    )


@api_router.post("/forma19/preview")
async def forma19_preview(req: Forma19Request):
    try:
        tpl = await _forma_template_overrides(19)
        data = _build_forma19_pdf(req, template=tpl)
    except Exception as e:
        logger.exception("forma19 generation failed")
        raise HTTPException(status_code=500, detail=f"Ошибка формирования: {e}")
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=forma19.pdf"},
    )


@api_router.post("/forma19/preview-png")
async def forma19_preview_png(req: Forma19Request):
    """Лист как PNG — надёжный предпросмотр. side='front' → стр.1 (лицо),
    side='back' → стр.2 (оборот)."""
    try:
        tpl = await _forma_template_overrides(19)
        pdf = _build_forma19_pdf(req, template=tpl)
        page_index = 1 if str(req.side or "front").lower() == "back" else 0
        png = docsvc.render_pdf_page_png(pdf, page_index, scale=2.0)
    except Exception as e:
        logger.exception("forma19 preview failed")
        raise HTTPException(status_code=500, detail=f"Ошибка предпросмотра: {e}")
    return Response(content=png, media_type="image/png",
                    headers={"Cache-Control": "no-store"})



# ======================= ФОРМА 24 — Талон миграционного учёта =======================
class Forma24Request(BaseModel):
    records: List[Dict[str, Any]] = []
    duplex_flip: str = "long"
    side: str = "front"


@api_router.get("/forma24/fields")
async def forma24_fields():
    return {"groups": docsvc.FORMA24_FIELDS, "keys": docsvc.FORMA24_FIELD_KEYS}


@api_router.get("/forma24/defaults")
async def forma24_get_defaults():
    doc = await db.app_settings.find_one({"key": "forma24_defaults"}, {"_id": 0})
    return {"defaults": (doc or {}).get("value", {})}


@api_router.post("/forma24/defaults")
async def forma24_save_defaults(payload: Forma19Defaults):
    await db.app_settings.update_one(
        {"key": "forma24_defaults"},
        {"$set": {"key": "forma24_defaults", "value": payload.defaults}},
        upsert=True,
    )
    return {"saved": True, "defaults": payload.defaults}


@api_router.post("/forma24/prefill")
async def forma24_prefill(payload: Forma19Prefill):
    return {"records": [docsvc.forma24_from_contract(s) for s in payload.students]}


def _build_forma24_pdf(req: "Forma24Request", template=None) -> bytes:
    return docsvc.build_forma24(people=req.records, duplex_flip=req.duplex_flip,
                                template=template)


@api_router.post("/forma24/preview")
async def forma24_preview(req: Forma24Request):
    try:
        tpl = await _forma_template_overrides(24)
        data = _build_forma24_pdf(req, template=tpl)
    except Exception as e:
        logger.exception("forma24 generation failed")
        raise HTTPException(status_code=500, detail=f"Ошибка формирования: {e}")
    return StreamingResponse(io.BytesIO(data), media_type="application/pdf",
                             headers={"Content-Disposition": "inline; filename=forma24.pdf"})


@api_router.post("/forma24/preview-png")
async def forma24_preview_png(req: Forma24Request):
    try:
        tpl = await _forma_template_overrides(24)
        pdf = _build_forma24_pdf(req, template=tpl)
        idx = 1 if str(req.side or "front").lower() == "back" else 0
        png = docsvc.render_pdf_page_png(pdf, idx, scale=2.0)
    except Exception as e:
        logger.exception("forma24 preview failed")
        raise HTTPException(status_code=500, detail=f"Ошибка предпросмотра: {e}")
    return Response(content=png, media_type="image/png", headers={"Cache-Control": "no-store"})



# ---------- Редактируемые шаблоны Форм 19/24 (как в «Заявлении») ----------
class FormaTemplate(BaseModel):
    template: List[Dict[str, Any]] = []


@api_router.get("/forma19/template")
async def forma19_get_template():
    ov = await _forma_template_overrides(19)
    return {
        "template": ov if ov is not None else docsvc.get_forma19_default_template(),
        "slots": docsvc.forma_slots(19),
        "is_custom": ov is not None,
        "page_count": 2,
        "page_w_mm": docsvc.FORMA19_MM[0],
        "page_h_mm": docsvc.FORMA19_MM[1],
    }


@api_router.post("/forma19/template")
async def forma19_save_template(payload: FormaTemplate):
    await db.app_settings.update_one(
        {"key": "forma19_template"},
        {"$set": {"key": "forma19_template", "value": payload.template}},
        upsert=True,
    )
    return {"saved": True, "count": len(payload.template)}


@api_router.post("/forma19/template/reset")
async def forma19_reset_template():
    await db.app_settings.delete_one({"key": "forma19_template"})
    return {"reset": True, "template": docsvc.get_forma19_default_template()}


@api_router.get("/forma24/template")
async def forma24_get_template():
    ov = await _forma_template_overrides(24)
    return {
        "template": ov if ov is not None else docsvc.get_forma24_default_template(),
        "slots": docsvc.forma_slots(24),
        "is_custom": ov is not None,
        "page_count": 2,
        "page_w_mm": docsvc.FORMA19_MM[0],
        "page_h_mm": docsvc.FORMA19_MM[1],
    }


@api_router.post("/forma24/template")
async def forma24_save_template(payload: FormaTemplate):
    await db.app_settings.update_one(
        {"key": "forma24_template"},
        {"$set": {"key": "forma24_template", "value": payload.template}},
        upsert=True,
    )
    return {"saved": True, "count": len(payload.template)}


@api_router.post("/forma24/template/reset")
async def forma24_reset_template():
    await db.app_settings.delete_one({"key": "forma24_template"})
    return {"reset": True, "template": docsvc.get_forma24_default_template()}



# ================= ЗАЯВЛЕНИЕ о регистрации по месту жительства =================
class ZayavlenieRequest(BaseModel):
    records: List[Dict[str, Any]] = []
    duplex_flip: str = "long"
    side: str = "front"
    two_up: bool = False


class ZayavlenieLayout(BaseModel):
    layout: Dict[str, Any] = {}


class ZayavlenieTemplate(BaseModel):
    template: List[Dict[str, Any]] = []


class ZayavlenieRecords(BaseModel):
    records: List[Dict[str, Any]] = []


async def _zayav_layout_overrides():
    doc = await db.app_settings.find_one({"key": "zayavlenie_layout"}, {"_id": 0})
    return (doc or {}).get("value", {}) or {}


async def _zayav_template_overrides():
    doc = await db.app_settings.find_one({"key": "zayavlenie_template"}, {"_id": 0})
    val = (doc or {}).get("value")
    return val if isinstance(val, list) and val else None


async def _forma_template_overrides(which: int):
    """Кастомный шаблон Формы 19/24 из БД (или None → дефолт)."""
    key = "forma19_template" if int(which) == 19 else "forma24_template"
    doc = await db.app_settings.find_one({"key": key}, {"_id": 0})
    val = (doc or {}).get("value")
    return val if isinstance(val, list) and val else None



@api_router.get("/zayavlenie/fields")
async def zayavlenie_fields():
    return {"groups": docsvc.ZAYAVLENIE_FIELDS, "keys": docsvc.ZAYAVLENIE_FIELD_KEYS}


@api_router.get("/zayavlenie/defaults")
async def zayavlenie_get_defaults():
    doc = await db.app_settings.find_one({"key": "zayavlenie_defaults"}, {"_id": 0})
    return {"defaults": (doc or {}).get("value", {})}


@api_router.post("/zayavlenie/defaults")
async def zayavlenie_save_defaults(payload: Forma19Defaults):
    await db.app_settings.update_one(
        {"key": "zayavlenie_defaults"},
        {"$set": {"key": "zayavlenie_defaults", "value": payload.defaults}},
        upsert=True,
    )
    return {"saved": True, "defaults": payload.defaults}


@api_router.post("/zayavlenie/prefill")
async def zayavlenie_prefill(payload: Forma19Prefill):
    """Из строк-«людей» единого шаблона -> записи Заявления."""
    return {"records": [masterdata.master_to_zayavlenie(m) for m in payload.students]}


@api_router.get("/zayavlenie/layout")
async def zayavlenie_get_layout():
    ov = await _zayav_layout_overrides()
    return {
        "layout": docsvc._merge_zayav_layout(ov),
        "slots": docsvc.ZAYAV_OVERLAY_SLOTS,
        "page_count": 2,
    }


@api_router.post("/zayavlenie/layout")
async def zayavlenie_save_layout(payload: ZayavlenieLayout):
    await db.app_settings.update_one(
        {"key": "zayavlenie_layout"},
        {"$set": {"key": "zayavlenie_layout", "value": payload.layout}},
        upsert=True,
    )
    return {"saved": True, "layout": docsvc._merge_zayav_layout(payload.layout)}


@api_router.get("/zayavlenie/template")
async def zayavlenie_get_template():
    ov = await _zayav_template_overrides()
    return {
        "template": docsvc._resolve_zayav_template(ov),
        "slots": docsvc.ZAYAV_OVERLAY_SLOTS,
        "is_custom": ov is not None,
        "page_count": 2,
    }


@api_router.post("/zayavlenie/template")
async def zayavlenie_save_template(payload: ZayavlenieTemplate):
    await db.app_settings.update_one(
        {"key": "zayavlenie_template"},
        {"$set": {"key": "zayavlenie_template", "value": payload.template}},
        upsert=True,
    )
    return {"saved": True, "count": len(payload.template)}


@api_router.post("/zayavlenie/template/reset")
async def zayavlenie_reset_template():
    await db.app_settings.delete_one({"key": "zayavlenie_template"})
    return {"reset": True, "template": docsvc.get_zayav_default_template()}


@api_router.get("/zayavlenie/records")
async def zayavlenie_get_records():
    doc = await db.app_settings.find_one({"key": "zayavlenie_records"}, {"_id": 0})
    return {"records": (doc or {}).get("value", []) or []}


@api_router.post("/zayavlenie/records")
async def zayavlenie_save_records(payload: ZayavlenieRecords):
    await db.app_settings.update_one(
        {"key": "zayavlenie_records"},
        {"$set": {"key": "zayavlenie_records", "value": payload.records}},
        upsert=True,
    )
    return {"saved": True, "count": len(payload.records)}


@api_router.get("/zayavlenie/background")
async def zayavlenie_background(page: int = 1):
    png = docsvc.render_zayav_background_png(page)
    return Response(content=png, media_type="image/png",
                    headers={"Cache-Control": "public, max-age=60"})


def _build_zayavlenie_pdf(req: "ZayavlenieRequest", template=None) -> bytes:
    return docsvc.build_zayavlenie(people=req.records, template=template,
                                   duplex_flip=req.duplex_flip, two_up=bool(req.two_up))


@api_router.post("/zayavlenie/preview")
async def zayavlenie_preview(req: ZayavlenieRequest):
    try:
        tpl = await _zayav_template_overrides()
        data = _build_zayavlenie_pdf(req, template=tpl)
    except Exception as e:
        logger.exception("zayavlenie generation failed")
        raise HTTPException(status_code=500, detail=f"Ошибка формирования: {e}")
    return StreamingResponse(io.BytesIO(data), media_type="application/pdf",
                             headers={"Content-Disposition": "inline; filename=zayavlenie.pdf"})


@api_router.post("/zayavlenie/preview-png")
async def zayavlenie_preview_png(req: ZayavlenieRequest):
    try:
        tpl = await _zayav_template_overrides()
        pdf = _build_zayavlenie_pdf(req, template=tpl)
        idx = 1 if str(req.side or "front").lower() == "back" else 0
        png = docsvc.render_pdf_page_png(pdf, idx, scale=2.0)
    except Exception as e:
        logger.exception("zayavlenie preview failed")
        raise HTTPException(status_code=500, detail=f"Ошибка предпросмотра: {e}")
    return Response(content=png, media_type="image/png", headers={"Cache-Control": "no-store"})




@api_router.get("/master-template")
async def master_template():
    """Скачать единый Excel-шаблон «Данные» (все документы, пробная строка)."""
    data = masterdata.build_master_xlsx()
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=banetskaya_dannye.xlsx"},
    )


@api_router.post("/master-upload")
async def master_upload(file: UploadFile = File(...)):
    """Загрузить заполненный единый шаблон -> строки + готовые записи по всем документам."""
    if not file.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=400, detail="Поддерживаются только файлы .xlsx")
    content = await file.read()
    try:
        people = masterdata.parse_master_xlsx(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Не удалось прочитать файл: {e}")
    if not people:
        raise HTTPException(status_code=400, detail="В файле нет данных (заполните строки с 3-й)")
    return {
        "count": len(people),
        "master": people,
        "contracts": [masterdata.master_to_contract(m) for m in people],
        "forma19": [masterdata.master_to_forma19(m) for m in people],
        "forma24": [masterdata.master_to_forma24(m) for m in people],
        "soobshenie": [masterdata.master_to_soobshenie(m) for m in people],
        "zayavlenie": [masterdata.master_to_zayavlenie(m) for m in people],
    }


class PackageRequest(BaseModel):
    people: List[Dict[str, Any]] = []      # строки-«люди» из единого шаблона
    duplex_flip: str = "long"
    include: Dict[str, bool] = {}           # {contract, forma19, forma24, soobshenie}


def _pkg_on(include: Dict[str, bool], key: str) -> bool:
    if not include:
        return True
    return bool(include.get(key, True))


async def _soobshenie_pkg_layout():
    """Стандартный layout Сообщения + свои поля-столбцы (cc_*) из активного профиля наложения.
    Стандартные поля и их позиции не меняются — только добавляются пользовательские столбцы."""
    layout = list(docsvc.SOOBSHENIE_LAYOUT)
    try:
        act = await db.app_settings.find_one({"key": "overlay_active_profile"})
        pid = (act or {}).get("value")
        prof = await db.overlay_profiles.find_one({"id": pid}) if pid else None
        for f in ((prof or {}).get("layout") or []):
            if f.get("custom") and str(f.get("key", "")).startswith("cc_"):
                layout.append(f)
    except Exception:
        logger.exception("soobshenie custom layout build failed")
    return layout


async def _build_package_pdf(req: "PackageRequest") -> bytes:
    tpl = await _active_tpl()
    inc = req.include or {}
    _zayav_tpl = await _zayav_template_overrides()
    _tpl19 = await _forma_template_overrides(19)
    _tpl24 = await _forma_template_overrides(24)
    _soob_layout = await _soobshenie_pkg_layout()
    parts: List[bytes] = []
    for m in (req.people or []):
        if _pkg_on(inc, "contract"):
            cfields = masterdata.master_to_contract(m)
            docx = docsvc.render_docx(cfields, tpl)
            parts.append(docsvc.convert_to_pdf(docx))
        want19 = _pkg_on(inc, "forma19")
        want24 = _pkg_on(inc, "forma24")
        if want19 and want24:
            # обе формы на одном листе (верх — Ф-19, низ — Ф-24), лицо+оборот
            parts.append(docsvc.build_forma_combined(
                masterdata.master_to_forma19(m), masterdata.master_to_forma24(m),
                duplex_flip=req.duplex_flip, tpl19=_tpl19, tpl24=_tpl24))
        elif want19:
            parts.append(docsvc.build_forma19(
                [masterdata.master_to_forma19(m)], duplex_flip=req.duplex_flip,
                template=_tpl19))
        elif want24:
            parts.append(docsvc.build_forma24(
                [masterdata.master_to_forma24(m)], duplex_flip=req.duplex_flip,
                template=_tpl24))
        if _pkg_on(inc, "soobshenie"):
            parts.append(docsvc.build_overlay(
                [masterdata.master_to_soobshenie(m)],
                layout=_soob_layout, page_size="a4", with_form=True))
        if _pkg_on(inc, "zayavlenie"):
            parts.append(docsvc.build_zayavlenie(
                [masterdata.master_to_zayavlenie(m)], template=_zayav_tpl,
                duplex_flip=req.duplex_flip))
    if not parts:
        raise HTTPException(status_code=400, detail="Нет документов для пакета")
    return docsvc.merge_pdfs(parts)


@api_router.post("/package")
async def build_package(req: PackageRequest):
    """Полный пакет документов (PDF): по каждому человеку — договор, лист Формы 19
    (2 копии, лицо+оборот), лист Формы 24 (2 копии) и лист «Сообщение»."""
    if not req.people:
        raise HTTPException(status_code=400, detail="Нет данных (загрузите Excel-шаблон)")
    try:
        pdf = await _build_package_pdf(req)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("package generation failed")
        raise HTTPException(status_code=500, detail=f"Ошибка формирования пакета: {e}")
    return StreamingResponse(
        io.BytesIO(pdf), media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=paket_dokumentov.pdf"})


class SinglePackageRequest(BaseModel):
    duplex_flip: str = "long"
    include: Dict[str, bool] = {}


class ContractsPackageRequest(BaseModel):
    ids: List[str]
    duplex_flip: str = "long"
    include: Dict[str, bool] = {}


@api_router.post("/contracts/{contract_id}/package")
async def contract_package(contract_id: str, req: SinglePackageRequest = SinglePackageRequest()):
    """Полный пакет документов для одного договора из истории."""
    doc = await db.contracts.find_one({"id": contract_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Договор не найден")
    preq = PackageRequest(people=[_contract_master(doc)],
                          duplex_flip=req.duplex_flip, include=req.include)
    try:
        pdf = await _build_package_pdf(preq)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("contract package failed")
        raise HTTPException(status_code=500, detail=f"Ошибка формирования пакета: {e}")
    return StreamingResponse(
        io.BytesIO(pdf), media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=paket_dokumentov.pdf"})


@api_router.post("/contracts/package")
async def contracts_package(req: ContractsPackageRequest):
    """Полный пакет документов сразу для нескольких выбранных договоров."""
    if not req.ids:
        raise HTTPException(status_code=400, detail="Не выбрано ни одного договора")
    people = []
    for cid in req.ids:
        doc = await db.contracts.find_one({"id": cid}, {"_id": 0})
        if doc:
            people.append(_contract_master(doc))
    if not people:
        raise HTTPException(status_code=404, detail="Договоры не найдены")
    preq = PackageRequest(people=people, duplex_flip=req.duplex_flip, include=req.include)
    try:
        pdf = await _build_package_pdf(preq)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("contracts package failed")
        raise HTTPException(status_code=500, detail=f"Ошибка формирования пакета: {e}")
    return StreamingResponse(
        io.BytesIO(pdf), media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=paket_dokumentov.pdf"})

# ============================================================================
#  РАЗДЕЛ «ЗАСЕЛЕНИЕ» — распределение жильцов по этажам/блокам/комнатам
# ============================================================================

def _norm_room(s: str) -> str:
    """'902 / 2' -> '902/2'."""
    s = (s or "").strip()
    m = re.match(r"^\s*(\d{3,4})\s*/\s*(\d+)", s)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    return s


def _contract_room(c: dict) -> str:
    m = c.get("master") or {}
    f = c.get("fields") or {}
    return _norm_room(m.get("room_number") or f.get("room_number") or "")


def _contract_num(c: dict) -> str:
    return (c.get("contract_number")
            or (c.get("master") or {}).get("contract_number")
            or (c.get("fields") or {}).get("contract_number") or "").strip()


async def _contract_for_name(full_name: str):
    """Ищем договор по ФИО (нечувствительно к регистру / ё / пробелам)."""
    norm = ressvc.normalize_name(full_name)
    if not norm:
        return None
    surname = full_name.split()[0] if full_name.split() else full_name
    esc = re.escape(surname)
    cands = await db.contracts.find(
        {"$or": [
            {"full_name": {"$regex": esc, "$options": "i"}},
            {"master.fio": {"$regex": esc, "$options": "i"}},
        ]},
        {"_id": 0},
    ).to_list(80)
    for c in cands:
        names = [c.get("full_name", ""), (c.get("master") or {}).get("fio", "")]
        if norm in [ressvc.normalize_name(n) for n in names if n]:
            return c
    return None


async def _resident_checks(res: dict) -> dict:
    """Сверка жильца с базой договоров. Договоры не меняем — только подсвечиваем."""
    room = f"{res.get('block','')}/{res.get('room','')}" if res.get("room") else res.get("block", "")
    checks = {"has_contract": False, "room_mismatch": False,
              "no_contract": True, "contract_not_needed": False,
              "contract_room": "", "contract_number": "",
              "mismatches": []}
    c = await _contract_for_name(res.get("full_name", ""))
    if not c:
        if res.get("no_contract_needed"):
            # договор не требуется — не считаем это проблемой
            checks["no_contract"] = False
            checks["contract_not_needed"] = True
            return checks
        checks["mismatches"].append({
            "field": "contract", "label": "Договор",
            "accommodation": "есть в заселении", "contract": "договор не найден"})
        return checks
    checks["has_contract"] = True
    checks["no_contract"] = False
    croom = _contract_room(c)
    cnum = _contract_num(c)
    checks["contract_room"] = croom
    checks["contract_number"] = cnum
    if croom and _norm_room(room) != croom:
        checks["room_mismatch"] = True
        checks["mismatches"].append({
            "field": "room", "label": "Комната",
            "accommodation": room, "contract": croom})
    rnum = str(res.get("contract_number") or "").strip()
    if rnum and cnum and rnum != cnum:
        checks["mismatches"].append({
            "field": "contract_number", "label": "Номер договора",
            "accommodation": rnum, "contract": cnum})
    return checks


@api_router.post("/residents/import")
async def residents_import(file: UploadFile = File(...)):
    """Импорт Excel заселения. Сохраняет уже введённые вручную ЛЬГОТА/Группа."""
    content = await file.read()
    try:
        parsed = ressvc.parse_zaselenie_xlsx(content)
    except Exception as e:
        logger.exception("residents import parse failed")
        raise HTTPException(status_code=400, detail=f"Не удалось разобрать файл: {e}")
    if not parsed:
        raise HTTPException(status_code=400,
                            detail="В файле не найдено ни одного жильца (проверьте лист с колонками «Блок», «Ф.И.О»).")
    # сохраняем ручные правки по совпадению ФИО
    existing = await db.residents.find({}, {"_id": 0}).to_list(100000)
    prev = {}
    for e in existing:
        prev[ressvc.normalize_name(e.get("full_name", ""))] = e
    docs = []
    for p in parsed:
        old = prev.get(ressvc.normalize_name(p["full_name"]))
        if old:
            if not p.get("benefit"):
                p["benefit"] = old.get("benefit", "")
            if not p.get("study_group"):
                p["study_group"] = old.get("study_group", "")
        docs.append(Resident(**p).model_dump())
    await db.residents.delete_many({})
    if docs:
        await db.residents.insert_many(docs)
    return {"imported": len(docs)}


@api_router.post("/residents/import-groups")
async def residents_import_groups(files: List[UploadFile] = File(...)):
    """Загрузка Word-списков групп. Проставляет учебную группу жильцам по ФИО.
    Можно загрузить сразу несколько файлов. Не найденные в заселении — в отчёте."""
    pairs = []
    parsed_files = []
    for f in files:
        content = await f.read()
        try:
            fp = ressvc.parse_group_lists_docx(content)
        except Exception as e:
            logger.exception("group list parse failed")
            raise HTTPException(status_code=400,
                                detail=f"Не удалось разобрать «{f.filename}»: {e}")
        parsed_files.append({"file": f.filename, "names": len(fp)})
        pairs.extend(fp)
    if not pairs:
        raise HTTPException(status_code=400,
                            detail="В файлах не найдено списков групп (ожидается строка «ГРУППА ...» и ФИО под ней).")

    name_group = {}
    for fio, g in pairs:
        name_group[ressvc.normalize_name(fio)] = g

    residents = await db.residents.find(
        {}, {"_id": 0, "id": 1, "full_name": 1, "study_group": 1}).to_list(100000)
    res_norms = {ressvc.normalize_name(r["full_name"]) for r in residents}

    now = datetime.now(timezone.utc).isoformat()
    matched = changed = unchanged = 0
    groups_applied = {}
    for r in residents:
        nn = ressvc.normalize_name(r["full_name"])
        g = name_group.get(nn)
        if not g:
            continue
        matched += 1
        groups_applied[g] = groups_applied.get(g, 0) + 1
        if (r.get("study_group") or "") != g:
            await db.residents.update_one(
                {"id": r["id"]}, {"$set": {"study_group": g, "updated_at": now}})
            changed += 1
        else:
            unchanged += 1

    not_found = sorted({fio for fio, _ in pairs
                        if ressvc.normalize_name(fio) not in res_norms})
    return {
        "files": parsed_files,
        "total_names": len(pairs),
        "groups_in_files": len({g for _, g in pairs}),
        "matched": matched,
        "changed": changed,
        "unchanged": unchanged,
        "not_found_count": len(not_found),
        "not_found": not_found[:300],
        "groups": dict(sorted(groups_applied.items())),
    }


@api_router.get("/residents/floors")
async def residents_floors():
    docs = await db.residents.find({}, {"_id": 0, "floor": 1, "block": 1}).to_list(100000)
    floors = {}
    for d in docs:
        f = d.get("floor", 0)
        floors.setdefault(f, {"floor": f, "people": 0, "blocks": set()})
        floors[f]["people"] += 1
        if d.get("block"):
            floors[f]["blocks"].add(d["block"])
    out = [{"floor": f, "people": v["people"], "blocks_present": len(v["blocks"])}
           for f, v in sorted(floors.items())]
    return {"floors": out, "total": len(docs)}


@api_router.get("/residents/floor/{floor}")
async def residents_floor(floor: int):
    docs = await db.residents.find({"floor": floor}, {"_id": 0}).to_list(100000)
    by_block = {}
    for d in docs:
        by_block.setdefault(d.get("block", ""), []).append(d)
    blocks = []
    for i in range(1, 16):
        block = f"{floor}{i:02d}"
        ppl = by_block.get(block, [])
        rooms = sorted({p.get("room", "") for p in ppl if p.get("room")})
        capacity = ressvc.block_capacity(rooms)
        free = max(0, capacity - len(ppl))
        gender = ressvc.block_gender([p.get("full_name", "") for p in ppl])
        blocks.append({"block": block, "index": i, "people": len(ppl),
                       "rooms": rooms, "capacity": capacity, "free": free,
                       "gender": gender})
    return {"floor": floor, "blocks": blocks, "total": len(docs)}


@api_router.get("/residents/block/{block}")
async def residents_block(block: str):
    floor = ressvc._floor_of(block)
    docs = await db.residents.find({"block": block}, {"_id": 0}).to_list(1000)
    docs.sort(key=lambda d: (d.get("room", ""), d.get("full_name", "")))
    rooms = {}
    for d in docs:
        d["checks"] = await _resident_checks(d)
        rooms.setdefault(d.get("room", ""), []).append(d)
    # раскладка блока: показываем и стандартные пустые комнаты со свободными местами
    rooms_present = sorted({r for r in rooms.keys() if r})
    layout = ressvc.block_layout(rooms_present)
    out = []
    for room, cap in layout:
        people = rooms.get(room, [])
        out.append({"room": room, "capacity": cap, "occupied": len(people),
                    "free": max(0, cap - len(people)), "people": people})
    # комнаты без номера (если вдруг есть) — в конец
    if "" in rooms:
        out.append({"room": "", "capacity": 0, "occupied": len(rooms[""]),
                    "free": 0, "people": rooms[""]})
    total_cap = sum(x["capacity"] for x in out)
    return {"block": block, "floor": floor, "rooms": out, "total": len(docs),
            "capacity": total_cap, "occupied": len(docs),
            "free": max(0, total_cap - len(docs))}


@api_router.get("/residents/options")
async def residents_options():
    """Списки значений для фильтров: группы и льготы (непустые, отсортированы)."""
    groups = await db.residents.distinct("study_group")
    benefits = await db.residents.distinct("benefit")
    groups = sorted([g for g in groups if g and str(g).strip()])
    benefits = sorted([b for b in benefits if b and str(b).strip()])
    return {"groups": groups, "benefits": benefits}


@api_router.get("/residents/filter")
async def residents_filter(group: Optional[str] = None, benefit: Optional[str] = None,
                           q: Optional[str] = None):
    """Фильтр жильцов по группе и/или льготе (и опц. поиск по ФИО) — по всем этажам."""
    query = {}
    if group:
        query["study_group"] = group
    if benefit:
        query["benefit"] = benefit
    if q and q.strip():
        query["full_name"] = {"$regex": re.escape(q.strip()), "$options": "i"}
    docs = await db.residents.find(query, {"_id": 0}).to_list(5000)
    docs.sort(key=lambda d: (d.get("floor", 0), d.get("block", ""),
                             d.get("room", ""), d.get("full_name", "")))
    for d in docs:
        d["checks"] = await _resident_checks(d)
    return {"residents": docs, "total": len(docs)}


@api_router.get("/residents/mismatches")
async def residents_mismatches():
    """Все жильцы, у кого комната в заселении не совпадает с комнатой в договоре."""
    contracts = await db.contracts.find({}, {"_id": 0}).to_list(100000)
    index = {}
    for c in contracts:
        for nm in [c.get("full_name", ""), (c.get("master") or {}).get("fio", "")]:
            n = ressvc.normalize_name(nm)
            if n and n not in index:
                index[n] = c
    residents = await db.residents.find({}, {"_id": 0}).to_list(100000)
    out = []
    for r in residents:
        c = index.get(ressvc.normalize_name(r.get("full_name", "")))
        if not c:
            continue
        croom = _contract_room(c)
        room = f"{r.get('block','')}/{r.get('room','')}" if r.get("room") else r.get("block", "")
        if croom and _norm_room(room) != croom:
            cnum = _contract_num(c)
            item = dict(r)
            item["checks"] = {
                "has_contract": True, "room_mismatch": True, "no_contract": False,
                "contract_room": croom, "contract_number": cnum,
                "mismatches": [{"field": "room", "label": "Комната",
                                "accommodation": room, "contract": croom}],
            }
            out.append(item)
    out.sort(key=lambda d: (d.get("floor", 0), d.get("block", ""),
                            d.get("room", ""), d.get("full_name", "")))
    return {"mismatches": out, "total": len(out)}


@api_router.get("/residents/no-contract")
async def residents_no_contract():
    """Все жильцы, для которых не найден договор (по ФИО) в базе договоров."""
    contracts = await db.contracts.find({}, {"_id": 0}).to_list(100000)
    index = set()
    for c in contracts:
        for nm in [c.get("full_name", ""), (c.get("master") or {}).get("fio", "")]:
            n = ressvc.normalize_name(nm)
            if n:
                index.add(n)
    residents = await db.residents.find({}, {"_id": 0}).to_list(100000)
    out = []
    for r in residents:
        if ressvc.normalize_name(r.get("full_name", "")) in index:
            continue
        if r.get("no_contract_needed"):
            continue  # отмечен «договор не нужен» — пропускаем
        room = f"{r.get('block','')}/{r.get('room','')}" if r.get("room") else r.get("block", "")
        item = dict(r)
        item["checks"] = {
            "has_contract": False, "room_mismatch": False, "no_contract": True,
            "contract_room": "", "contract_number": "",
            "mismatches": [{"field": "contract", "label": "Договор",
                            "accommodation": "есть в заселении", "contract": "договор не найден"}],
        }
        out.append(item)
    out.sort(key=lambda d: (d.get("floor", 0), d.get("block", ""),
                            d.get("room", ""), d.get("full_name", "")))
    return {"residents": out, "total": len(out)}


@api_router.get("/residents/{res_id}")
async def residents_get(res_id: str):
    doc = await db.residents.find_one({"id": res_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Жилец не найден")
    doc["checks"] = await _resident_checks(doc)
    return doc


@api_router.post("/residents")
async def residents_create(req: ResidentRequest):
    data = req.model_dump(exclude_none=True)
    if not data.get("full_name"):
        raise HTTPException(status_code=400, detail="Укажите ФИО")
    res = Resident(**data)
    res.floor = ressvc._floor_of(res.block)
    await db.residents.insert_one(res.model_dump())
    doc = await db.residents.find_one({"id": res.id}, {"_id": 0})
    doc["checks"] = await _resident_checks(doc)
    return doc


@api_router.patch("/residents/{res_id}")
async def residents_update(res_id: str, req: ResidentRequest):
    existing = await db.residents.find_one({"id": res_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Жилец не найден")
    upd = req.model_dump(exclude_none=True)
    if "block" in upd:
        upd["floor"] = ressvc._floor_of(upd["block"])
    upd["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.residents.update_one({"id": res_id}, {"$set": upd})
    doc = await db.residents.find_one({"id": res_id}, {"_id": 0})
    doc["checks"] = await _resident_checks(doc)
    return doc


@api_router.delete("/residents/{res_id}")
async def residents_delete(res_id: str):
    res = await db.residents.delete_one({"id": res_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Жилец не найден")
    return {"deleted": True}




app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Optional: serve the built React frontend (single-server / desktop mode) ----------
# Activates ONLY when a production build exists (e.g. on a local Windows machine after
# `yarn build`, or bundled inside the PyInstaller .exe). In the cloud dev setup this
# directory is absent, so nothing changes.
if getattr(sys, "frozen", False):
    _default_build = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "frontend_build"
else:
    _default_build = ROOT_DIR.parent / "frontend" / "build"
FRONTEND_BUILD = Path(os.environ.get("FRONTEND_BUILD_DIR", str(_default_build)))
if (FRONTEND_BUILD / "index.html").exists():
    logger.info("Serving frontend build from %s", FRONTEND_BUILD)

    # Only the bundled desktop app runs "frozen" (PyInstaller .exe). In that case we
    # mark the served HTML as desktop so the frontend never shows the web start page.
    _IS_DESKTOP_BUILD = bool(getattr(sys, "frozen", False))

    def _index_html() -> Response:
        html = (FRONTEND_BUILD / "index.html").read_text(encoding="utf-8")
        if _IS_DESKTOP_BUILD and "__IS_DESKTOP__" not in html:
            html = html.replace(
                "<head>",
                "<head><script>window.__IS_DESKTOP__=true;</script>",
                1,
            )
        return Response(content=html, media_type="text/html")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # /api/* is handled by the router above; return 404 for unknown API paths
        # instead of falling back to the SPA index.
        if full_path.startswith("api/") or full_path == "api":
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = (FRONTEND_BUILD / full_path).resolve()
        if (
            full_path
            and str(candidate).startswith(str(FRONTEND_BUILD.resolve()))
            and candidate.is_file()
        ):
            return FileResponse(str(candidate))
        return _index_html()


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()


@app.on_event("startup")
async def _init_active_deps():
    try:
        await _load_active_deps()
    except Exception:
        logger.exception("failed to load active dependencies")


@app.on_event("startup")
async def ensure_soffice():
    """Self-heal: on Linux, if LibreOffice (soffice) is missing after a container
    recycle, install it in the background so PDF/print keep working."""
    import platform
    import shutil
    import subprocess
    import threading

    if platform.system() != "Linux":
        return
    if shutil.which(os.environ.get("SOFFICE_BIN", "soffice")):
        return

    def _install():
        try:
            logger.warning("soffice missing -> installing LibreOffice in background ...")
            subprocess.run(
                ["apt-get", "install", "-y", "--no-install-recommends",
                 "libreoffice-writer", "libreoffice-core"],
                capture_output=True, timeout=900,
            )
            logger.warning("LibreOffice background install finished")
        except Exception:
            logger.exception("LibreOffice auto-install failed")

    threading.Thread(target=_install, daemon=True).start()
