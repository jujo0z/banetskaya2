#!/usr/bin/env python3
# Idempotent patch: add starosta-scoped delete endpoint + apiClient wrapper.

SERVER = "/opt/banetskaya/backend/server.py"
API = "/opt/banetskaya/frontend/src/lib/apiClient.js"

# ---- 1. backend endpoint ----
with open(SERVER, encoding="utf-8") as f:
    src = f.read()

if "inspections_delete_starosta" in src:
    print("backend: already patched")
else:
    anchor = "# ---------- Блок: староста блока ----------"
    if anchor not in src:
        raise SystemExit("backend anchor not found")
    endpoint = '''@api_router.delete("/inspections/starosta/{insp_id}")
async def inspections_delete_starosta(insp_id: str, user: dict = Depends(get_current_user)):
    """Староста удаляет проверку. Доступ только к своим этажам."""
    doc = await db.inspections.find_one({"id": insp_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Проверка не найдена")
    floor = doc.get("floor") or ressvc._floor_of(doc.get("block", ""))
    if user.get("role") != "admin" and floor not in (user.get("floors") or []):
        raise HTTPException(status_code=403, detail="Нет доступа к этому этажу")
    await db.inspections.delete_one({"id": insp_id})
    return {"deleted": True}


'''
    src = src.replace(anchor, endpoint + anchor, 1)
    with open(SERVER, "w", encoding="utf-8") as f:
        f.write(src)
    print("backend: patched OK")

# ---- 2. apiClient wrapper ----
with open(API, encoding="utf-8") as f:
    api = f.read()

if "deleteInspectionStarosta" in api:
    print("apiClient: already patched")
else:
    anchor = "// --- Староста блока ---"
    if anchor not in api:
        raise SystemExit("apiClient anchor not found")
    wrapper = '''export async function deleteInspectionStarosta(id) {
  const { data } = await api.delete(`/inspections/starosta/${id}`, { headers: authHeaders() });
  return data;
}
'''
    api = api.replace(anchor, wrapper + anchor, 1)
    with open(API, "w", encoding="utf-8") as f:
        f.write(api)
    print("apiClient: patched OK")
