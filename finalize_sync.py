#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Финальное выравнивание residents <-> contracts к 1:1 по НОМЕРУ договора.
  python3 finalize_sync.py        # предпросмотр
  python3 finalize_sync.py apply
"""
import re, sys, uuid
from datetime import datetime, timezone, date
from openpyxl import load_workbook
from pymongo import MongoClient
import master_data as md

APPLY=len(sys.argv)>1 and sys.argv[1]=="apply"
db=MongoClient("mongodb://127.0.0.1:27017")["banetskaya_db"]
def now(): return datetime.now(timezone.utc).isoformat()
def norm(f): return re.sub(r"\s+"," ",(f or "").lower().replace("ё","е").strip())
def digc(s):
    d=re.sub(r"\D","",s or ""); return d.lstrip("0") or ("0" if d else "")
def pad6(s):
    d=re.sub(r"\D","",s or ""); return d.zfill(6) if d else ""
def cl(v):
    if v is None: return ""
    if isinstance(v,(datetime,date)): return v.strftime("%d.%m.%Y")
    s=str(v).strip(); m=re.match(r"^(\d{4})-(\d{2})-(\d{2})",s)
    return f"{m.group(3)}.{m.group(2)}.{m.group(1)}" if m else s

# ---- решения по ФИО ----
USE_FILE={4788,4793,4798,4817,4889,4913,4915,4937,4974,4982,4985,5036,5102,5110,
          5156,5170,5177,5196,5244,5286, 4848,4946,5004,5260,5275}
DIFFERENT={4848,4946,5004,5260,5275}   # разные люди -> чистая карточка новому, паспорт очистить

# ---- файл ----
wb=load_workbook("/root/dlya_ivana.xlsx",data_only=True); ws=wb[wb.sheetnames[0]]
rows=list(ws.iter_rows(values_only=True))
file_by_num={}; file_people=[]; seen=set()
for r in rows[3:]:
    def g(i): return cl(r[i]) if i<len(r) else ""
    if not g(2): continue
    nk=norm(g(2))
    if nk in seen: continue
    seen.add(nk)
    num=digc(g(6))
    block=g(1); term=g(7)
    term=re.sub(r"^(\d{2})\.(\d{2})(\d{4})$",r"\1.\2.\3",term)
    if term=="12.07.202": term="12.07.2027"
    p={"name":g(2),"num":num,"block":block,"term":term}
    file_people.append(p)
    if num: file_by_num[num]=p
file_nums=set(file_by_num); file_names=set(norm(p["name"]) for p in file_people)

res=list(db.residents.find({})); con=list(db.contracts.find({}))

# ===== STEP A: выбывшие =====
res_out=[d for d in res if digc(d.get("contract_number",""))not in file_nums and norm(d.get("full_name",""))not in file_names]
con_out=[d for d in con if digc(d.get("contract_number",""))not in file_nums and norm(d.get("full_name",""))not in file_names]
res_out_ids={d["_id"] for d in res_out}; con_out_ids={d["_id"] for d in con_out}

# оставшиеся контракты после удаления выбывших
con_live=[d for d in con if d["_id"] not in con_out_ids]
con_by_num={}
for d in con_live:
    n=digc(d.get("contract_number",""))
    if n: con_by_num.setdefault(n,[]).append(d)

def official_name(cs):
    for c in cs:
        if (c.get("master") or {}).get("passport","").strip(): return c.get("full_name","")
    for c in cs:
        if c.get("status")=="final" and not c.get("needs_completion"): return c.get("full_name","")
    return cs[0].get("full_name","")

renames=[]; deletes_dup=[]; creates=[]; cleared=[]
to_delete_ids=set(con_out_ids)
updates=[]   # (id, setdict)
inserts=[]
for num,p in file_by_num.items():
    cs=con_by_num.get(num,[])
    numi=int(num) if num.isdigit() else -1
    canonical = p["name"] if numi in USE_FILE else (official_name(cs) if cs else p["name"])
    if not cs:
        m={"fio":canonical,"contract_number":pad6(num),"contract_end_date":p["term"],"room_number":p["block"]}
        inserts.append(m); creates.append(f'{p["block"]} {canonical} №{pad6(num)}')
        continue
    # keeper
    keeper=None
    for c in cs:
        if norm(c.get("full_name",""))==norm(canonical): keeper=c; break
    if keeper is None:
        for c in cs:
            if (c.get("master") or {}).get("passport","").strip(): keeper=c; break
    if keeper is None: keeper=cs[0]
    for c in cs:
        if c["_id"]!=keeper["_id"]:
            to_delete_ids.add(c["_id"]); deletes_dup.append(f'№{num} удалить дубль: {c.get("full_name")}')
    # привести keeper к canonical
    if norm(keeper.get("full_name",""))!=norm(canonical) or numi in DIFFERENT:
        if numi in DIFFERENT:
            m={"fio":canonical,"contract_number":pad6(num),"contract_end_date":p["term"],"room_number":p["block"]}
            cleared.append(f'№{num} {keeper.get("full_name")} -> {canonical} (паспорт очищен)')
            fields=md.master_to_contract(m)
            updates.append((keeper["_id"],{"full_name":canonical,"master":m,
                "fields":{k:("" if v is None else str(v)) for k,v in fields.items()},
                "contract_number":pad6(num),"status":"final","needs_completion":True,
                "source_import_2026_10":True,"updated_at":now()}))
        else:
            m=dict(keeper.get("master") or {}); m["fio"]=canonical
            if not m.get("contract_number"): m["contract_number"]=pad6(num)
            fields=md.master_to_contract(m)
            renames.append(f'{keeper.get("full_name")} -> {canonical}')
            updates.append((keeper["_id"],{"full_name":canonical,"master":m,
                "fields":{k:("" if v is None else str(v)) for k,v in fields.items()},
                "updated_at":now()}))

# ===== STEP C: имена проживающих -> canonical, по номеру/файлу =====
res_updates=[]
canon_by_num={}
for num,p in file_by_num.items():
    numi=int(num) if num.isdigit() else -1
    cs=con_by_num.get(num,[])
    canon_by_num[num]= p["name"] if numi in USE_FILE else (official_name(cs) if cs else p["name"])
for d in res:
    if d["_id"] in res_out_ids: continue
    num=digc(d.get("contract_number",""))
    canon=canon_by_num.get(num)
    if not canon:
        # по имени файла
        continue
    if norm(d.get("full_name",""))!=norm(canon):
        res_updates.append((d["_id"],canon))

# ===== STEP D: черновики -> final (пометка остаётся) =====
drafts=[d for d in con_live if d.get("status")=="draft" and d["_id"] not in to_delete_ids]

print("="*60)
print("MODE:", "APPLY" if APPLY else "DRY RUN")
print("="*60)
print("residents:",len(res)," contracts:",len(con))
print("A. Удалить выбывших: residents",len(res_out)," contracts",len(con_out))
print("B. Удалить дублей-договоров:",len(deletes_dup))
print("   Переименовать договоров (опечатки):",len(renames))
print("   Разные люди (новая карточка, паспорт очищен):",len(cleared))
print("   Создать недостающих договоров:",len(creates))
print("C. Переименовать проживающих (выровнять):",len(res_updates))
print("D. Черновиков -> final:",len(drafts))
print("-"*60)
exp_con=len(con)-len(con_out)-len(deletes_dup)+len(creates)
exp_res=len(res)-len(res_out)
print("Ожидается после: residents",exp_res," contracts",exp_con)
print("="*60)
print("\n-- РАЗНЫЕ ЛЮДИ --")
for x in cleared: print("  ",x)
print("\n-- УДАЛЕНИЕ ДУБЛЕЙ --")
for x in deletes_dup: print("  ",x)
print("\n-- СОЗДАТЬ --")
for x in creates: print("  ",x)

if APPLY:
    print("\n>>> ПРИМЕНЯЮ...")
    if res_out_ids: db.residents.delete_many({"_id":{"$in":list(res_out_ids)}})
    if to_delete_ids: db.contracts.delete_many({"_id":{"$in":list(to_delete_ids)}})
    for _id,s in updates: db.contracts.update_one({"_id":_id},{"$set":s})
    for m in inserts:
        fields=md.master_to_contract(m)
        db.contracts.insert_one({"id":str(uuid.uuid4()),"contract_number":m["contract_number"],
            "full_name":m["fio"],"fields":{k:("" if v is None else str(v)) for k,v in fields.items()},
            "master":m,"status":"final","demo":False,"counters":None,"needs_completion":True,
            "source_import_2026_10":True,"created_at":now(),"updated_at":now()})
    for _id,canon in res_updates: db.residents.update_one({"_id":_id},{"$set":{"full_name":canon,"updated_at":now()}})
    db.contracts.update_many({"status":"draft"},{"$set":{"status":"final","needs_completion":True}})
    rc=db.residents.count_documents({}); cc=db.contracts.count_documents({})
    print("ИТОГО residents:",rc," contracts:",cc)
    # сверка 1:1
    rn=set(norm(d.get("full_name","")) for d in db.residents.find({},{"full_name":1}))
    cn=set(norm(d.get("full_name","")) for d in db.contracts.find({},{"full_name":1}))
    print("ТОЛЬКО в residents:",len(rn-cn)," ТОЛЬКО в contracts:",len(cn-rn))
else:
    print("\n(DRY RUN)")
