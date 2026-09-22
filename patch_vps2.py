#!/usr/bin/env python3
# Idempotent patch #2: mandatory reasons for grade 1-2 + personal cabinet endpoint.
SERVER = "/opt/banetskaya/backend/server.py"
API = "/opt/banetskaya/frontend/src/lib/apiClient.js"


def patch(path, repls, marker):
    with open(path, encoding="utf-8") as f:
        src = f.read()
    if marker in src:
        print(f"{path}: already patched")
        return
    for old, new in repls:
        c = src.count(old)
        if c != 1:
            raise SystemExit(f"[{path}] expected 1 match, got {c} for:\n{old[:90]}")
        src = src.replace(old, new, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"{path}: patched OK")


# ---------------- server.py ----------------
server_repls = []

# 1) Inspection model: add reasons dict
server_repls.append((
    '    common: int = 0\n    note: str = ""\n    created_by: str = ""',
    '    common: int = 0\n    note: str = ""\n    reasons: dict = Field(default_factory=dict)\n    created_by: str = ""',
))

# 2) InspectionRequest: add reasons
server_repls.append((
    '    common: int = 0\n    note: Optional[str] = ""\n',
    '    common: int = 0\n    note: Optional[str] = ""\n    reasons: Optional[dict] = None\n',
))

# 3) _upsert_inspection signature
server_repls.append((
    'async def _upsert_inspection(block: str, dt: str, small: int, big: int,\n'
    '                             common: int, note: str, by: str) -> dict:',
    'async def _upsert_inspection(block: str, dt: str, small: int, big: int,\n'
    '                             common: int, note: str, by: str,\n'
    '                             reasons: dict = None) -> dict:',
))

# 4) validation + payload with reasons
server_repls.append((
    '    now = datetime.now(timezone.utc).isoformat()\n'
    '    floor = ressvc._floor_of(block)\n'
    '    payload = {"small_room": _clamp(small), "big_room": _clamp(big),\n'
    '               "common": _clamp(common), "note": note or "",\n'
    '               "created_by": by, "updated_at": now, "floor": floor}',
    '    now = datetime.now(timezone.utc).isoformat()\n'
    '    floor = ressvc._floor_of(block)\n'
    '    _grades = {"small_room": _clamp(small), "big_room": _clamp(big),\n'
    '               "common": _clamp(common)}\n'
    '    _reasons = {k: str((reasons or {}).get(k, "") or "").strip() for k in _grades}\n'
    '    _missing = [k for k, v in _grades.items() if 1 <= v <= 2 and not _reasons.get(k)]\n'
    '    if _missing:\n'
    '        raise HTTPException(status_code=400,\n'
    '                            detail="Для оценки 1\u20132 укажите причину (что и почему)")\n'
    '    _reasons = {k: v for k, v in _reasons.items() if v}\n'
    '    payload = {"small_room": _grades["small_room"], "big_room": _grades["big_room"],\n'
    '               "common": _grades["common"], "note": note or "", "reasons": _reasons,\n'
    '               "created_by": by, "updated_at": now, "floor": floor}',
))

# 5) Inspection(...) constructor add reasons
server_repls.append((
    '    doc = Inspection(block=block, date=dt, floor=floor,\n'
    '                     small_room=payload["small_room"], big_room=payload["big_room"],\n'
    '                     common=payload["common"], note=payload["note"],\n'
    '                     created_by=by).model_dump()',
    '    doc = Inspection(block=block, date=dt, floor=floor,\n'
    '                     small_room=payload["small_room"], big_room=payload["big_room"],\n'
    '                     common=payload["common"], note=payload["note"],\n'
    '                     reasons=payload["reasons"], created_by=by).model_dump()',
))

# 6) caller: starosta create
server_repls.append((
    '    return await _upsert_inspection(req.block, req.date, req.small_room,\n'
    '                                    req.big_room, req.common, req.note or "", by)',
    '    return await _upsert_inspection(req.block, req.date, req.small_room,\n'
    '                                    req.big_room, req.common, req.note or "", by,\n'
    '                                    req.reasons)',
))

# 7) caller: admin save
server_repls.append((
    '    return await _upsert_inspection(req.block, req.date, req.small_room,\n'
    '                                    req.big_room, req.common, req.note or "",\n'
    '                                    "\u0417\u0430\u0432\u0435\u0434\u0443\u044e\u0449\u0430\u044f")',
    '    return await _upsert_inspection(req.block, req.date, req.small_room,\n'
    '                                    req.big_room, req.common, req.note or "",\n'
    '                                    "\u0417\u0430\u0432\u0435\u0434\u0443\u044e\u0449\u0430\u044f", req.reasons)',
))

# 8) caller: update (PUT)
server_repls.append((
    '                                    req.note or "", existing.get("created_by", "\u0417\u0430\u0432\u0435\u0434\u0443\u044e\u0449\u0430\u044f"))',
    '                                    req.note or "", existing.get("created_by", "\u0417\u0430\u0432\u0435\u0434\u0443\u044e\u0449\u0430\u044f"),\n'
    '                                    req.reasons)',
))

# 9) cabinet endpoint before the "староста блока" anchor
cabinet_ep = '''@api_router.get("/cabinet/low-grades")
async def cabinet_low_grades(user: dict = Depends(get_current_user)):
    """\u041b\u0438\u0447\u043d\u044b\u0439 \u043a\u0430\u0431\u0438\u043d\u0435\u0442: \u0431\u043b\u043e\u043a\u0438 \u0441 \u043d\u0438\u0437\u043a\u0438\u043c\u0438 \u043e\u0446\u0435\u043d\u043a\u0430\u043c\u0438 (1\u20132)."""
    labels = {"small_room": "\u041c\u0430\u043b\u0430\u044f \u043a\u043e\u043c\u043d\u0430\u0442\u0430",
              "big_room": "\u0411\u043e\u043b\u044c\u0448\u0430\u044f \u043a\u043e\u043c\u043d\u0430\u0442\u0430",
              "common": "\u041e\u0431\u0449\u0435\u0435 \u043f\u0440\u043e\u0441\u0442\u0440\u0430\u043d\u0441\u0442\u0432\u043e"}
    query = {}
    if user.get("role") != "admin":
        query["floor"] = {"$in": user.get("floors") or []}
    docs = await db.inspections.find(query, {"_id": 0}).to_list(100000)
    by_block = {}
    for i in docs:
        low = []
        for k, lab in labels.items():
            g = int(i.get(k, 0) or 0)
            if 1 <= g <= 2:
                low.append({"key": k, "label": lab, "grade": g,
                            "reason": (i.get("reasons") or {}).get(k, "")})
        if not low:
            continue
        b = i.get("block", "")
        e = by_block.setdefault(b, {"block": b, "floor": i.get("floor", 0),
                                    "count": 0, "dates": 0, "items": []})
        e["count"] += len(low)
        e["dates"] += 1
        e["items"].append({"date": i.get("date", ""), "areas": low,
                           "note": i.get("note", "")})
    blocks = list(by_block.values())
    for e in blocks:
        e["warning"] = e["count"] >= 3
        e["items"].sort(key=lambda x: _date_key(x["date"]), reverse=True)
    blocks.sort(key=lambda e: (not e["warning"], -e["count"], e["block"]))
    return {"blocks": blocks, "threshold": 3,
            "total_warnings": sum(1 for e in blocks if e["warning"])}


'''
anchor = '# ---------- \u0411\u043b\u043e\u043a: \u0441\u0442\u0430\u0440\u043e\u0441\u0442\u0430 \u0431\u043b\u043e\u043a\u0430 ----------'
server_repls.append((anchor, cabinet_ep + anchor))

patch(SERVER, server_repls, marker="/cabinet/low-grades")

# ---------------- apiClient.js ----------------
api_anchor = '// --- \u041f\u0443\u0431\u043b\u0438\u0447\u043d\u044b\u0435 (Mini App / \u0443\u0447\u0430\u0449\u0438\u0439\u0441\u044f) ---'
api_wrapper = '''export async function cabinetLowGrades() {
  const { data } = await api.get("/cabinet/low-grades", { headers: authHeaders() });
  return data;
}
'''
patch(API, [(api_anchor, api_wrapper + api_anchor)], marker="cabinetLowGrades")
