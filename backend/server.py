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
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from openpyxl import load_workbook

import document_service as docsvc

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


class BatchGenerateRequest(BaseModel):
    contracts: List[Dict[str, str]]


class Contract(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    contract_number: str = ""
    full_name: str = ""
    fields: Dict[str, str]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BatchDownloadRequest(BaseModel):
    ids: List[str]
    format: str = "docx"


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


async def _save_contract(fields: Dict[str, str]) -> Contract:
    contract = Contract(
        contract_number=fields.get("contract_number", ""),
        full_name=fields.get("full_name", ""),
        fields=fields,
    )
    await db.contracts.insert_one(contract.model_dump())
    return contract


@api_router.post("/contracts")
async def create_contract(req: GenerateRequest):
    contract = await _save_contract(req.fields)
    return contract.model_dump()


@api_router.post("/contracts/batch")
async def create_contracts_batch(req: BatchGenerateRequest):
    created = []
    for fields in req.contracts:
        contract = await _save_contract(fields)
        created.append(contract.model_dump())
    return {"created": created, "count": len(created)}


@api_router.get("/contracts")
async def list_contracts(q: Optional[str] = None):
    query = {}
    if q:
        query = {"$or": [
            {"full_name": {"$regex": re.escape(q), "$options": "i"}},
            {"contract_number": {"$regex": re.escape(q), "$options": "i"}},
        ]}
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


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
