import io
import os
import re
import uuid
import zipfile
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Annotated

from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from openpyxl import load_workbook, Workbook

import document_service as docsvc

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


class Contract(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    contract_number: str = ""
    full_name: str = ""
    fields: Dict[str, str]
    status: str = "final"  # "final" | "draft"
    demo: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BatchDownloadRequest(BaseModel):
    ids: List[str]
    format: str = "docx"


class Preset(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    fields: Dict[str, str]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PresetRequest(BaseModel):
    name: str
    fields: Dict[str, str]


# ---------- Helpers ----------
def _cell_to_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
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


async def _save_contract(fields: Dict[str, str], status: str = "final") -> Contract:
    contract = Contract(
        contract_number=fields.get("contract_number", ""),
        full_name=fields.get("full_name", ""),
        fields=fields,
        status=status if status in ("final", "draft") else "final",
    )
    await db.contracts.insert_one(contract.model_dump())
    return contract


@api_router.post("/contracts")
async def create_contract(req: GenerateRequest):
    contract = await _save_contract(req.fields, req.status or "final")
    return contract.model_dump()


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
    for fields in req.contracts:
        contract = await _save_contract(fields)
        created.append(contract.model_dump())
    return {"created": created, "count": len(created)}


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
    docx_bytes = docsvc.render_docx(fields)
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
    docx_bytes = docsvc.render_docx(req.fields)
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
            docx_bytes = docsvc.render_docx(fields)
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
        docx_bytes = docsvc.render_docx(doc["fields"])
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
# `yarn build`). In the cloud dev setup this directory is absent, so nothing changes.
FRONTEND_BUILD = Path(
    os.environ.get("FRONTEND_BUILD_DIR", str(ROOT_DIR.parent / "frontend" / "build"))
)
if (FRONTEND_BUILD / "index.html").exists():
    logger.info("Serving frontend build from %s", FRONTEND_BUILD)

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
        return FileResponse(str(FRONTEND_BUILD / "index.html"))


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
