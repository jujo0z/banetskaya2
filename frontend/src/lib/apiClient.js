import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API });

export async function fetchFields() {
  const { data } = await api.get("/fields");
  return data.fields;
}

export async function getStats() {
  const { data } = await api.get("/stats");
  return data;
}

export async function downloadSampleTemplate() {
  const res = await api.get("/sample-template", { responseType: "blob" });
  downloadBlob(res.data, "sample_students.xlsx");
}

export async function uploadExcel(file) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function saveContract(fields, status = "final") {
  const { data } = await api.post("/contracts", { fields, status });
  return data;
}

export async function updateContract(id, fields, status) {
  const { data } = await api.put(`/contracts/${id}`, { fields, status });
  return data;
}

export async function saveContractsBatch(contracts) {
  const { data } = await api.post("/contracts/batch", { contracts });
  return data;
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

export async function saveOverlayLayout(layout, dx_mm, dy_mm) {
  const { data } = await api.post("/overlay/layout", { layout, dx_mm, dy_mm });
  return data;
}

export async function overlayPdfUrl(records, { layout, dx_mm = 0, dy_mm = 0, withBackground = false, withForm = false, pageSize = "card" } = {}) {
  const res = await api.post(
    "/overlay/generate",
    { records, layout, dx_mm, dy_mm, with_background: withBackground, with_form: withForm, page_size: pageSize },
    { responseType: "blob" }
  );
  return window.URL.createObjectURL(res.data);
}

// Open the overlay PDF in a NEW TAB so the user prints from the PDF viewer
// (reliable + lets them pick "Actual size / 100%"). Auto window.print() on a
// blob PDF often prints a blank page on some printers, so we avoid it.
export async function openOverlayPdf(records, { layout, dx_mm = 0, dy_mm = 0, pageSize = "card", withBackground = false, withForm = false } = {}) {
  const res = await api.post(
    "/overlay/generate",
    { records, layout, dx_mm, dy_mm, with_background: withBackground, with_form: withForm, page_size: pageSize },
    { responseType: "blob" }
  );
  const url = window.URL.createObjectURL(res.data);
  window.open(url, "_blank");
}

export async function downloadOverlayPdf(records, { layout, dx_mm = 0, dy_mm = 0, pageSize = "card", withBackground = false, withForm = false } = {}) {
  const res = await api.post(
    "/overlay/generate",
    { records, layout, dx_mm, dy_mm, with_background: withBackground, with_form: withForm, page_size: pageSize },
    { responseType: "blob" }
  );
  downloadBlob(res.data, "soobshenie_overlay.pdf");
}

export async function openOverlayTestSheet(dx = 0, dy = 0, pageSize = "card") {
  const res = await api.get("/overlay/test-sheet", { params: { dx, dy, page_size: pageSize }, responseType: "blob" });
  const url = window.URL.createObjectURL(res.data);
  window.open(url, "_blank");
}

// ---------- Silent printing (desktop app only) ----------
export async function getPrinters() {
  const { data } = await api.get("/printers");
  return data; // { supported: bool, printers: [{name, default}] }
}

export async function printOverlaySilent(records, { layout, dx_mm = 0, dy_mm = 0, pageSize = "card", printerName = "", withBackground = false, withForm = false } = {}) {
  const { data } = await api.post("/overlay/print-silent", {
    records,
    layout,
    dx_mm,
    dy_mm,
    page_size: pageSize,
    printer_name: printerName,
    with_background: withBackground,
    with_form: withForm,
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
