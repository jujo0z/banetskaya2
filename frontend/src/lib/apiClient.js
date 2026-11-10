import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API });

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401 && err.response.data?.code === "gate_required"
        && !window.location.pathname.startsWith("/tg")) {
      let had = false;
      try { had = sessionStorage.getItem("bnk_gate_ok") === "1"; sessionStorage.removeItem("bnk_gate_ok"); } catch (e) { /* ignore */ }
      if (had) window.location.reload();
    }
    return Promise.reject(err);
  }
);

export async function getStats() {
  const { data } = await api.get("/stats");
  return data;
}

export async function downloadSampleTemplate() {
  const res = await api.get("/sample-template", { responseType: "blob" });
  downloadBlob(res.data, "sample_students.xlsx");
}

// ---- Единый Excel-шаблон «Данные» (все документы) ----
export async function downloadMasterTemplate() {
  const res = await api.get("/master-template", { responseType: "blob" });
  downloadBlob(res.data, "banetskaya_dannye.xlsx");
}

export async function masterUpload(file) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/master-upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data; // { count, master, contracts, forma19, forma24, soobshenie }
}

export async function saveContract(fields, status = "final") {
  const { data } = await api.post("/contracts", { fields, status });
  return data;
}

export async function updateContract(id, fields, status) {
  const { data } = await api.put(`/contracts/${id}`, { fields, status });
  return data;
}

export async function saveContractsBatch(contracts, masters = []) {
  const { data } = await api.post("/contracts/batch", { contracts, masters });
  return data;
}

// Умная загрузка Excel для «Генерация из Excel» (единый шаблон или старый формат)
export async function generateUpload(file) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/generate/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data; // { mode, count, students, masters, [columns, rows, mapping] }
}

// Пакет из истории — по одному договору и по нескольким
export async function openContractPackage(id, duplexFlip = "long", include = {}) {
  const res = await api.post(`/contracts/${id}/package`, { duplex_flip: duplexFlip, include }, { responseType: "blob" });
  window.open(window.URL.createObjectURL(res.data), "_blank");
}
export async function openContractsPackage(ids, duplexFlip = "long", include = {}) {
  const res = await api.post("/contracts/package", { ids, duplex_flip: duplexFlip, include }, { responseType: "blob" });
  window.open(window.URL.createObjectURL(res.data), "_blank");
}

export async function listContracts(q = "", status = "") {
  const params = {};
  if (q) params.q = q;
  if (status) params.status = status;
  const { data } = await api.get("/contracts", { params });
  return data;
}

export async function getPresets() {
  const { data } = await api.get("/presets");
  return data;
}

export async function savePreset(name, fields) {
  const { data } = await api.post("/presets", { name, fields });
  return data;
}

export async function deletePreset(id) {
  const { data } = await api.delete(`/presets/${id}`);
  return data;
}

export async function seedDemo() {
  const { data } = await api.post("/seed-demo");
  return data;
}

export async function clearDemo() {
  const { data } = await api.delete("/seed-demo");
  return data;
}

export async function deleteContract(id) {
  const { data } = await api.delete(`/contracts/${id}`);
  return data;
}

// Trigger a browser download for a blob response
export function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

function parseFilename(headers, fallback) {
  const cd = headers["content-disposition"] || "";
  const match = cd.match(/filename\*=UTF-8''([^;]+)/);
  if (match) return decodeURIComponent(match[1]);
  return fallback;
}

export async function downloadSavedContract(id, format, fallback) {
  const res = await api.get(`/contracts/${id}/download`, {
    params: { format },
    responseType: "blob",
  });
  downloadBlob(res.data, parseFilename(res.headers, fallback));
}

export async function downloadPreview(fields, format, fallback) {
  const res = await api.post(`/contracts/preview`, { fields }, {
    params: { format },
    responseType: "blob",
  });
  downloadBlob(res.data, parseFilename(res.headers, fallback));
}

export async function previewPdfUrl(fields) {
  const res = await api.post(`/contracts/preview`, { fields }, {
    params: { format: "pdf" },
    responseType: "blob",
  });
  return window.URL.createObjectURL(res.data);
}

export async function savedPdfUrl(id) {
  const res = await api.get(`/contracts/${id}/download`, {
    params: { format: "pdf" },
    responseType: "blob",
  });
  return window.URL.createObjectURL(res.data);
}

export async function batchPrint(ids) {
  const res = await api.post(`/contracts/batch-print`, { ids }, { responseType: "blob" });
  const url = window.URL.createObjectURL(res.data);
  const w = window.open(url);
  if (w) w.onload = () => w.print();
}

export async function manualDuplexPrint(ids, side, backReversed = true, separators = false, orientation = "portrait", flipEdge = "long") {
  const res = await api.post(
    `/contracts/manual-duplex`,
    { ids, side, back_order: backReversed ? "reversed" : "normal", separators, orientation, flip_edge: flipEdge },
    { responseType: "blob" }
  );
  const url = window.URL.createObjectURL(res.data);
  const w = window.open(url);
  if (w) w.onload = () => w.print();
}

// Templates (built-in template is never modified)
export async function listTemplates() {
  return (await api.get("/templates")).data;
}
export async function uploadTemplate(file) {
  const fd = new FormData();
  fd.append("file", file);
  return (await api.post("/templates", fd, { headers: { "Content-Type": "multipart/form-data" } })).data;
}
export async function activateTemplate(id) {
  return (await api.post(`/templates/${id}/activate`)).data;
}
export async function deleteTemplateById(id) {
  return (await api.delete(`/templates/${id}`)).data;
}
export async function getTemplateInfo() {
  return (await api.get("/template-info")).data;
}

// Printer profiles
export async function getPrintProfiles() {
  return (await api.get("/print-profiles")).data;
}
export async function savePrintProfile(name, settings) {
  return (await api.post("/print-profiles", { name, settings })).data;
}
export async function deletePrintProfile(id) {
  return (await api.delete(`/print-profiles/${id}`)).data;
}

export async function printDuplexTest(side, orientation = "portrait") {
  const res = await api.get(`/print-test`, { params: { side, orientation }, responseType: "blob" });
  const url = window.URL.createObjectURL(res.data);
  const w = window.open(url);
  if (w) w.onload = () => w.print();
}

export async function batchDownload(ids, format) {
  const res = await api.post(`/contracts/batch-download`, { ids, format }, {
    responseType: "blob",
  });
  downloadBlob(res.data, "contracts.zip");
}

// ---------- Overlay printing (печать на готовом бланке) ----------
export async function getOverlayLayout() {
  const { data } = await api.get("/overlay/layout");
  return data;
}

// ---------- App config (Windows installer link) ----------
export async function getAppConfig() {
  const { data } = await api.get("/app-config");
  return data;
}

export async function saveAppConfig(windows_download_url) {
  const { data } = await api.post("/app-config", { windows_download_url });
  return data;
}

// ---------- Overlay placement PROFILES ----------
export async function listOverlayProfiles() {
  const { data } = await api.get("/overlay/profiles");
  return data; // { profiles: [...], active_id }
}
export async function createOverlayProfile(profile) {
  const { data } = await api.post("/overlay/profiles", profile);
  return data; // created profile
}
export async function updateOverlayProfile(id, profile) {
  const { data } = await api.put(`/overlay/profiles/${id}`, profile);
  return data;
}
export async function deleteOverlayProfile(id) {
  const { data } = await api.delete(`/overlay/profiles/${id}`);
  return data;
}
export async function setActiveOverlayProfile(id) {
  const { data } = await api.post("/overlay/active-profile", { id });
  return data;
}

export async function overlayPdfUrl(records, { layout, dx_mm = 0, dy_mm = 0, withBackground = false, withForm = false, pageSize = "card", rotate = 0, a4Position = "top-left", mode = "overlay", orientation = "portrait", perSheet = 0 } = {}) {
  const res = await api.post(
    "/overlay/generate",
    { records, layout, dx_mm, dy_mm, with_background: withBackground, with_form: withForm, page_size: pageSize, rotate, a4_position: a4Position, mode, orientation, per_sheet: perSheet },
    { responseType: "blob" }
  );
  return window.URL.createObjectURL(res.data);
}

// Render the first sheet as a PNG image for a reliable on-screen preview.
export async function overlayPreviewPngUrl(records, { layout, dx_mm = 0, dy_mm = 0, withForm = false, pageSize = "card", rotate = 0, a4Position = "top-left", mode = "overlay", orientation = "portrait", perSheet = 0 } = {}) {
  const res = await api.post(
    "/overlay/preview-png",
    { records, layout, dx_mm, dy_mm, with_form: withForm, page_size: pageSize, rotate, a4_position: a4Position, mode, orientation, per_sheet: perSheet },
    { responseType: "blob" }
  );
  return window.URL.createObjectURL(res.data);
}

// Open the overlay PDF in a NEW TAB so the user prints from the PDF viewer
// (reliable + lets them pick "Actual size / 100%"). Auto window.print() on a
// blob PDF often prints a blank page on some printers, so we avoid it.
export async function openOverlayPdf(records, { layout, dx_mm = 0, dy_mm = 0, pageSize = "card", withBackground = false, withForm = false, rotate = 0, a4Position = "top-left", mode = "overlay", orientation = "portrait", perSheet = 0 } = {}) {
  const res = await api.post(
    "/overlay/generate",
    { records, layout, dx_mm, dy_mm, with_background: withBackground, with_form: withForm, page_size: pageSize, rotate, a4_position: a4Position, mode, orientation, per_sheet: perSheet },
    { responseType: "blob" }
  );
  const url = window.URL.createObjectURL(res.data);
  window.open(url, "_blank");
}

export async function downloadOverlayPdf(records, { layout, dx_mm = 0, dy_mm = 0, pageSize = "card", withBackground = false, withForm = false, rotate = 0, a4Position = "top-left", mode = "overlay", orientation = "portrait", perSheet = 0 } = {}) {
  const res = await api.post(
    "/overlay/generate",
    { records, layout, dx_mm, dy_mm, with_background: withBackground, with_form: withForm, page_size: pageSize, rotate, a4_position: a4Position, mode, orientation, per_sheet: perSheet },
    { responseType: "blob" }
  );
  downloadBlob(res.data, "soobshenie_overlay.pdf");
}

export async function openOverlayTestSheet(dx = 0, dy = 0, pageSize = "card", rotate = 0) {
  const res = await api.get("/overlay/test-sheet", { params: { dx, dy, page_size: pageSize, rotate }, responseType: "blob" });
  const url = window.URL.createObjectURL(res.data);
  window.open(url, "_blank");
}

export async function openCarrierFrame(a4Position = "top-left") {
  const res = await api.get("/overlay/carrier-frame", { params: { a4_position: a4Position }, responseType: "blob" });
  const url = window.URL.createObjectURL(res.data);
  window.open(url, "_blank");
}

// ---------- Silent printing (desktop app only) ----------
export async function getPrinters() {
  const { data } = await api.get("/printers");
  return data; // { supported: bool, printers: [{name, default}] }
}

export async function printOverlaySilent(records, { layout, dx_mm = 0, dy_mm = 0, pageSize = "card", printerName = "", withBackground = false, withForm = false, rotate = 0, a4Position = "top-left", mode = "overlay", orientation = "portrait", perSheet = 0 } = {}) {
  const { data } = await api.post("/overlay/print-silent", {
    records,
    layout,
    dx_mm,
    dy_mm,
    page_size: pageSize,
    printer_name: printerName,
    with_background: withBackground,
    with_form: withForm,
    rotate,
    a4_position: a4Position,
    mode,
    orientation,
    per_sheet: perSheet,
  });
  return data; // { printed, printer, pages }
}

export async function exportHistory(q = "", status = "") {
  const params = {};
  if (q) params.q = q;
  if (status) params.status = status;
  const res = await api.get("/contracts/export", { params, responseType: "blob" });
  downloadBlob(res.data, parseFilename(res.headers, "Реестр_договоров.xlsx"));
}

export async function exportBase(q = "", status = "") {
  const params = {};
  if (q) params.q = q;
  if (status) params.status = status;
  const res = await api.get("/contracts/export-base", { params, responseType: "blob" });
  downloadBlob(res.data, parseFilename(res.headers, "База_данные.xlsx"));
}

export async function exportBaseSelected(ids) {
  const res = await api.post("/contracts/export-base-selected", { ids }, { responseType: "blob" });
  downloadBlob(res.data, parseFilename(res.headers, "База_выбранные.xlsx"));
}

// ---------- Встроенная таблица данных (Excel в приложении) ----------
export async function getMasterSchema() {
  const { data } = await api.get("/master-schema");
  return data; // { columns: [{key,label,section,dropdown,builtin}] }
}

export async function getContractsGrid() {
  const { data } = await api.get("/contracts/grid");
  return data; // { rows: [{id,status,created_at,contract_number,full_name,master}] }
}

export async function patchContractMaster(id, patch) {
  // Щадящее сохранение правок в базу: меняем только переданные поля master.
  const { data } = await api.patch(`/contracts/${id}/master`, { patch });
  return data;
}

export async function saveMasterBulk(rows) {
  // rows: [{ id, master }]
  const { data } = await api.put("/contracts/master-bulk", { rows });
  return data; // { updated }
}

export async function residentsOccupancyBulk(rows) {
  // rows: [{ res_id, block, room, study_group, benefit, status, note }]
  const { data } = await api.put("/residents/occupancy-bulk", { rows });
  return data; // { updated }
}

export async function addCustomColumn(label, section = "Дополнительно", dropdown = null) {
  const { data } = await api.post("/custom-columns", { label, section, dropdown });
  return data;
}

export async function deleteCustomColumn(key) {
  const { data } = await api.delete(`/custom-columns/${key}`);
  return data;
}

// ---------- Зависимости (свой столбец -> поле бланка) ----------
export async function getDependencies(document = "") {
  const params = document ? { document } : {};
  const { data } = await api.get("/dependencies", { params });
  return data; // { dependencies: [...] }
}

export async function getDocumentTargets(document) {
  const { data } = await api.get(`/document-targets/${document}`);
  return data; // { targets: [{field,label}] }
}

export async function addDependency(document, target_field, source) {
  const { data } = await api.post("/dependencies", { document, target_field, source });
  return data;
}

export async function deleteDependency(id) {
  const { data } = await api.delete(`/dependencies/${id}`);
  return data;
}

// ---------- System diagnostics ----------
export async function getDiagnostics() {
  const { data } = await api.get("/health/diagnostics");
  return data; // { checks:[{key,label,ok,detail,info?}], all_ok, is_desktop, platform }
}

// ---------- Reg-authority profile ----------
export async function getRegProfile() {
  const { data } = await api.get("/reg-profile");
  return data; // { reg_organ, chief, city }
}

export async function saveRegProfile(profile) {
  const { data } = await api.post("/reg-profile", profile);
  return data;
}

// ---------- Desktop version & auto-update ----------
export async function getAppVersion() {
  const { data } = await api.get("/app-version");
  return data; // { version, build_time, git_sha, repo, is_desktop }
}

export async function checkUpdates() {
  const { data } = await api.get("/updates/check");
  return data; // { supported, current_version, update_available, latest_version, download_url, notes, ... }
}

export async function applyUpdate(downloadUrl = "") {
  const { data } = await api.post("/updates/apply", { download_url: downloadUrl });
  return data; // { started, installer }
}

// Map a saved contract (договор найма) to the СООБЩЕНИЕ overlay field keys.
// Only the reliably-overlapping text fields are mapped; split date fields
// (day/month/year) are left for the operator to fill.
export function contractToOverlay(c = {}) {
  const f = c.fields || c || {};
  const out = {};
  if (f.full_name) out.fio = f.full_name;
  if (f.birth_date) out.birth = f.citizenship ? `${f.birth_date}, ${f.citizenship}` : f.birth_date;
  if (f.reg_address || f.registration_address) out.address = f.registration_address || f.reg_address;
  if (f.passport_number) out.passport_number = f.passport_number;
  if (f.passport_issued_by) out.issued_by = f.passport_issued_by;
  if (f.contract_number) out.number = f.contract_number;
  return out;
}

// ======================= ФОРМА 19 — Адресный листок прибытия =======================
export async function forma19Fields() {
  const { data } = await api.get("/forma19/fields");
  return data; // { groups:[{group, fields:[{key,label}]}], keys:[] }
}

export async function getForma19Defaults() {
  const { data } = await api.get("/forma19/defaults");
  return data.defaults || {};
}

export async function saveForma19Defaults(defaults) {
  const { data } = await api.post("/forma19/defaults", { defaults });
  return data;
}

// Convert student dicts (contract fields) -> Форма 19 records (split ФИО/дата/паспорт).
export async function forma19Prefill(students) {
  const { data } = await api.post("/forma19/prefill", { students });
  return data.records || [];
}

// Apply an Excel column mapping to raw rows -> field-keyed student dicts.

export async function forma19PreviewPngUrl(records, duplexFlip = "long", side = "front") {
  const res = await api.post(
    "/forma19/preview-png",
    { records, duplex_flip: duplexFlip, side },
    { responseType: "blob" }
  );
  return window.URL.createObjectURL(res.data);
}

export async function openForma19Pdf(records, duplexFlip = "long") {
  const res = await api.post(
    "/forma19/preview",
    { records, duplex_flip: duplexFlip },
    { responseType: "blob" }
  );
  const url = window.URL.createObjectURL(res.data);
  window.open(url, "_blank");
}

export async function downloadForma19Pdf(records, duplexFlip = "long") {
  const res = await api.post(
    "/forma19/preview",
    { records, duplex_flip: duplexFlip },
    { responseType: "blob" }
  );
  downloadBlob(res.data, "forma19.pdf");
}

// ======================= ФОРМА 24 — Талон миграционного учёта =======================
export async function forma24Fields() {
  const { data } = await api.get("/forma24/fields");
  return data;
}
export async function getForma24Defaults() {
  const { data } = await api.get("/forma24/defaults");
  return data.defaults || {};
}
export async function saveForma24Defaults(defaults) {
  const { data } = await api.post("/forma24/defaults", { defaults });
  return data;
}
export async function forma24Prefill(students) {
  const { data } = await api.post("/forma24/prefill", { students });
  return data.records || [];
}
export async function forma24PreviewPngUrl(records, duplexFlip = "long", side = "front") {
  const res = await api.post("/forma24/preview-png", { records, duplex_flip: duplexFlip, side }, { responseType: "blob" });
  return window.URL.createObjectURL(res.data);
}
export async function openForma24Pdf(records, duplexFlip = "long") {
  const res = await api.post("/forma24/preview", { records, duplex_flip: duplexFlip }, { responseType: "blob" });
  window.open(window.URL.createObjectURL(res.data), "_blank");
}
export async function downloadForma24Pdf(records, duplexFlip = "long") {
  const res = await api.post("/forma24/preview", { records, duplex_flip: duplexFlip }, { responseType: "blob" });
  downloadBlob(res.data, "forma24.pdf");
}

// ---- Редактируемые шаблоны Форм 19/24 и «Сообщения» (как в «Заявлении») ----
function _tplBase(which) {
  return which === "soobshenie" ? `/soobshenie` : `/forma${which}`;
}
export async function getFormaTemplate(which) {
  const { data } = await api.get(`${_tplBase(which)}/template`);
  return data; // {template, slots, is_custom, page_count, page_w_mm, page_h_mm}
}
export async function saveFormaTemplate(which, template) {
  const { data } = await api.post(`${_tplBase(which)}/template`, { template });
  return data;
}
export async function resetFormaTemplate(which) {
  const { data } = await api.post(`${_tplBase(which)}/template/reset`);
  return data;
}
// Единый источник данных: записи «Сообщения» для всех договоров из истории
export async function soobshenieForContracts(ids) {
  const { data } = await api.post(`/soobshenie/for-contracts`, { ids });
  return data; // { records, count }
}

export async function getSoobshenieFromHistory() {
  const { data } = await api.get(`/soobshenie/from-history`);
  return data; // {records, count}
}

// ---- Заявление о регистрации по месту жительства ----
export async function zayavlenieFields() {
  const { data } = await api.get("/zayavlenie/fields");
  return data;
}
export async function getZayavlenieDefaults() {
  const { data } = await api.get("/zayavlenie/defaults");
  return data.defaults || {};
}
export async function saveZayavlenieDefaults(defaults) {
  const { data } = await api.post("/zayavlenie/defaults", { defaults });
  return data;
}
export async function zayavleniePrefill(students) {
  const { data } = await api.post("/zayavlenie/prefill", { students });
  return data.records || [];
}
export async function openZayavleniePdf(records, duplexFlip = "long", twoUp = false, singleSmall = false) {
  const res = await api.post("/zayavlenie/preview", { records, duplex_flip: duplexFlip, two_up: twoUp, single_small: singleSmall }, { responseType: "blob" });
  window.open(window.URL.createObjectURL(res.data), "_blank");
}
export async function downloadZayavleniePdf(records, duplexFlip = "long", twoUp = false, singleSmall = false) {
  const res = await api.post("/zayavlenie/preview", { records, duplex_flip: duplexFlip, two_up: twoUp, single_small: singleSmall }, { responseType: "blob" });
  downloadBlob(res.data, "zayavlenie.pdf");
}
export async function getZayavlenieTemplate() {
  const { data } = await api.get("/zayavlenie/template");
  return data;
}
export async function saveZayavlenieTemplate(template) {
  const { data } = await api.post("/zayavlenie/template", { template });
  return data;
}
export async function resetZayavlenieTemplate() {
  const { data } = await api.post("/zayavlenie/template/reset");
  return data;
}
export async function getZayavlenieRecords() {
  const { data } = await api.get("/zayavlenie/records");
  return data.records || [];
}
export async function saveZayavlenieRecords(records) {
  const { data } = await api.post("/zayavlenie/records", { records });
  return data;
}

// ======================= Счётчики проживающих (Заявление, стр.2) =======================
export async function getCountersBase() {
  const { data } = await api.get("/counters/base");
  return data;
}
export async function saveCountersBase(base, recompute = true) {
  const { data } = await api.post(`/counters/base?recompute=${recompute}`, base);
  return data;
}
export async function recomputeCounters(force = false) {
  const { data } = await api.post(`/contracts/recompute-counters?force=${force}`);
  return data;
}

// ======================= ЗАСЕЛЕНИЕ — распределение по этажам =======================
export async function residentsImport(file) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/residents/import", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data; // { imported }
}
export async function residentsImportGroups(files) {
  const form = new FormData();
  for (const f of files) form.append("files", f);
  const { data } = await api.post("/residents/import-groups", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data; // { files, total_names, matched, changed, unchanged, not_found_count, not_found, groups }
}
export async function residentsFloors() {
  const { data } = await api.get("/residents/floors");
  return data; // { floors:[{floor,people,blocks_present}], total }
}
export async function residentsFloor(floor) {
  const { data } = await api.get(`/residents/floor/${floor}`);
  return data; // { floor, blocks:[{block,index,people,rooms}], total }
}
export async function residentsBlock(block) {
  const { data } = await api.get(`/residents/block/${block}`);
  return data; // { block, floor, rooms:[{room, people:[{...,checks}]}], total }
}
export async function residentsOptions() {
  const { data } = await api.get("/residents/options");
  return data; // { groups:[], benefits:[] }
}
export async function residentsFilter({ group, benefit, q } = {}) {
  const params = {};
  if (group) params.group = group;
  if (benefit) params.benefit = benefit;
  if (q) params.q = q;
  const { data } = await api.get("/residents/filter", { params });
  return data; // { residents:[{...,checks}], total }
}
export async function residentsMismatches() {
  const { data } = await api.get("/residents/mismatches");
  return data; // { mismatches:[{...,checks}], total }
}
export async function residentsNoContract() {
  const { data } = await api.get("/residents/no-contract");
  return data; // { residents:[{...,checks}], total }
}
export async function residentCreate(payload) {
  const { data } = await api.post("/residents", payload);
  return data;
}
export async function residentUpdate(id, payload) {
  const { data } = await api.patch(`/residents/${id}`, payload);
  return data;
}
export async function residentDelete(id) {
  const { data } = await api.delete(`/residents/${id}`);
  return data;
}

// ---- Полный пакет документов (договор + Ф19 + Ф24 + сообщение) ----
export async function openPackagePdf(people, duplexFlip = "long", include = {}) {
  const res = await api.post("/package", { people, duplex_flip: duplexFlip, include }, { responseType: "blob" });
  window.open(window.URL.createObjectURL(res.data), "_blank");
}
export async function downloadPackagePdf(people, duplexFlip = "long", include = {}) {
  const res = await api.post("/package", { people, duplex_flip: duplexFlip, include }, { responseType: "blob" });
  downloadBlob(res.data, "paket_dokumentov.pdf");
}

// ======================= ОЦЕНКИ ЗА ЧИСТОТУ + учётки старост =======================
const TOKEN_KEY = "bnk_starosta_token";
export function getToken() {
  try { return localStorage.getItem(TOKEN_KEY) || ""; } catch (e) { return ""; }
}
export function setToken(t) {
  try { if (t) localStorage.setItem(TOKEN_KEY, t); else localStorage.removeItem(TOKEN_KEY); } catch (e) {}
}
function authHeaders() {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

// --- Аутентификация старост ---
export async function login(username, password) {
  const { data } = await api.post("/auth/login", { username, password });
  if (data.token) setToken(data.token);
  return data; // { token, user }
}
export function logout() { setToken(""); }
export async function authMe() {
  const { data } = await api.get("/auth/me", { headers: authHeaders() });
  return data; // { id, username, role, floors, full_name }
}

// --- Учётки (кабинет заведующей) ---
export async function listAccounts() {
  const { data } = await api.get("/accounts");
  return data.accounts || [];
}
export async function createAccount(payload) {
  const { data } = await api.post("/accounts", payload);
  return data;
}
export async function updateAccount(id, payload) {
  const { data } = await api.put(`/accounts/${id}`, payload);
  return data;
}
export async function deleteAccount(id) {
  const { data } = await api.delete(`/accounts/${id}`);
  return data;
}

// --- Инспекции ---
export async function listInspections({ floor, block, date } = {}) {
  const params = {};
  if (floor != null) params.floor = floor;
  if (block) params.block = block;
  if (date) params.date = date;
  const { data } = await api.get("/inspections", { params });
  return data; // { inspections, total }
}
// Староста выставляет (нужен токен)
export async function saveInspectionStarosta(payload) {
  const { data } = await api.post("/inspections", payload, { headers: authHeaders() });
  return data;
}
// Заведующая (кабинет, без токена)
export async function saveInspectionAdmin(payload) {
  const { data } = await api.post("/inspections/save", payload);
  return data;
}
export async function deleteInspection(id) {
  const { data } = await api.delete(`/inspections/${id}`);
  return data;
}

export async function deleteInspectionStarosta(id) {
  const { data } = await api.delete(`/inspections/starosta/${id}`, { headers: authHeaders() });
  return data;
}
// --- Староста блока ---
export async function setBlockElder(block, full_name) {
  const { data } = await api.post(`/blocks/${block}/elder`, { full_name });
  return data;
}

export async function cabinetLowGrades() {
  const { data } = await api.get("/cabinet/low-grades", { headers: authHeaders() });
  return data;
}
export async function publicKitchens() {
  const { data } = await api.get("/public/kitchens");
  return data;
}
export async function publicKitchen(k) {
  const { data } = await api.get(`/public/kitchen/${k}`);
  return data;
}
export async function saveKitchenSchedule(k, rows, title) {
  const { data } = await api.post(`/kitchens/${k}/schedule`, { rows, title }, { headers: authHeaders() });
  return data;
}
export async function uploadKitchenSchedule(k, file) {
  const fd = new FormData();
  fd.append("file", file);
  const { data } = await api.post(`/kitchens/${k}/upload`, fd, { headers: authHeaders() });
  return data;
}
export async function saveKitchenInspection(payload) {
  const { data } = await api.post("/kitchen-inspections", payload, { headers: authHeaders() });
  return data;
}
export async function deleteKitchenInspection(id) {
  const { data } = await api.delete(`/kitchen-inspections/starosta/${id}`, { headers: authHeaders() });
  return data;
}
export async function cabinetKitchenLowGrades() {
  const { data } = await api.get("/cabinet/kitchen-low-grades", { headers: authHeaders() });
  return data;
}
export async function kitchenDuty(k, date) {
  const { data } = await api.get(`/kitchens/${k}/duty`, { params: { date }, headers: authHeaders() });
  return data;
}
export async function siteGate(login, password) {
  const { data } = await api.post("/site-gate", { login, password });
  return data;
}
export async function siteGateCheck() {
  const { data } = await api.get("/site-gate/check");
  return data;
}
// --- Публичные (Mini App / учащийся) ---
export async function publicFloors() {
  const { data } = await api.get("/public/floors");
  return data.floors || [];
}
export async function publicFloor(floor) {
  const { data } = await api.get(`/public/floor/${floor}`);
  return data; // { floor, blocks:[{block,latest,problem,elder}] }
}
export async function publicBlock(block) {
  const { data } = await api.get(`/public/block/${block}`);
  return data; // { block, floor, elder, inspections:[...] }
}
export async function publicSearch(q) {
  const { data } = await api.get("/public/search", { params: { q } });
  return data.results || [];
}

// --- Telegram ---
export async function telegramInfo() {
  const { data } = await api.get("/telegram/info");
  return data;
}
export async function telegramSetupMenu(url) {
  const { data } = await api.post("/telegram/setup-menu", { url });
  return data;
}

// ---- Сдвиг оборота Форм 19/24 (компенсация дуплекса принтера) ----
export async function getFormaBackOffset() {
  const { data } = await api.get("/forma/back-offset");
  return data;
}
export async function saveFormaBackOffset(upMm, rightMm = 0) {
  const { data } = await api.post("/forma/back-offset", { up_mm: upMm, right_mm: rightMm });
  return data;
}
export async function openFormaCalibration(applyOffset = false) {
  const res = await api.get(`/forma/calibration?apply_offset=${applyOffset}`, { responseType: "blob" });
  const url = window.URL.createObjectURL(res.data);
  window.open(url, "_blank");
}

// ---- Сдвиг оборота Заявления (layout: "a4" | "land") ----
export async function getZayavBackOffset(layout = "a4") {
  const { data } = await api.get(`/zayavlenie/back-offset?layout=${layout}`);
  return data;
}
export async function saveZayavBackOffset(layout, upMm, rightMm = 0) {
  const { data } = await api.post(`/zayavlenie/back-offset?layout=${layout}`, { up_mm: upMm, right_mm: rightMm });
  return data;
}
export async function openZayavCalibration(layout = "a4", applyOffset = false) {
  const res = await api.get(`/zayavlenie/calibration?layout=${layout}&apply_offset=${applyOffset}`, { responseType: "blob" });
  window.open(window.URL.createObjectURL(res.data), "_blank");
}
