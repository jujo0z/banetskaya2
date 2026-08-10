import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API });

export async function fetchFields() {
  const { data } = await api.get("/fields");
  return data.fields;
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

export async function saveContract(fields) {
  const { data } = await api.post("/contracts", { fields });
  return data;
}

export async function saveContractsBatch(contracts) {
  const { data } = await api.post("/contracts/batch", { contracts });
  return data;
}

export async function listContracts(q = "") {
  const { data } = await api.get("/contracts", { params: q ? { q } : {} });
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

export async function batchDownload(ids, format) {
  const res = await api.post(`/contracts/batch-download`, { ids, format }, {
    responseType: "blob",
  });
  downloadBlob(res.data, "contracts.zip");
}
