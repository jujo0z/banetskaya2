#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Выравнивание residents <-> contracts до 1:1.
  python3 sync_equalize.py        # предпросмотр
  python3 sync_equalize.py apply  # применить
"""
import re, sys, uuid
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pymongo import MongoClient
import master_data as md

APPLY=len(sys.argv)>1 and sys.argv[1]=="apply"
db=MongoClient("mongodb://127.0.0.1:27017")["banetskaya_db"]
def now(): return datetime.now(timezone.utc).isoformat()
def norm(f): return re.sub(r"\s+"," ",(f or "").lower().replace("ё","е").strip())
def pad(num):
    d=re.sub(r"\D","",num or ""); return d.zfill(6) if d else ""

res=list(db.residents.find({}))
con=list(db.contracts.find({}))
con_by={}; res_by={}
for c in con: con_by.setdefault(norm(c.get("full_name","")),c)
for r in res: res_by.setdefault(norm(r.get("full_name","")),r)
exact=set(res_by)&set(con_by)
res_only=set(res_by)-set(con_by)
con_only=set(con_by)-set(res_by)

def fuzzy(an, pool):
    at=an.split(); asur=at[0] if at else ""; af=at[1] if len(at)>1 else ""; ap=at[2] if len(at)>2 else ""
    best=None; bs=0
    for bn in pool:
        bt=bn.split(); bsur=bt[0] if bt else ""; bf=bt[1] if len(bt)>1 else ""; bp=bt[2] if len(bt)>2 else ""
        fr=SequenceMatcher(None,an,bn).ratio(); sr=SequenceMatcher(None,asur,bsur).ratio()
        sc=0
        if af and af==bf and sr>=0.72:
            if not(ap and bp and SequenceMatcher(None,ap,bp).ratio()<0.6): sc=1.5+sr
        elif fr>=0.9: sc=fr
        if sc>bs: best,bs=bn,sc
    return best

# 1) пары разного написания -> переименуем resident в имя из договора
pairs=[]; used_con=set()
for an in list(res_only):
    bn=fuzzy(an,[x for x in con_only if x not in used_con])
    if bn:
        used_con.add(bn); pairs.append((an,bn))
renamed=[]
for an,bn in pairs:
    r=res_by[an]; c=con_by[bn]
    renamed.append((r.get("full_name"),c.get("full_name")))

# пересчёт оставшихся
res_only2=[a for a in res_only if a not in {p[0] for p in pairs}]
con_only2=[b for b in con_only if b not in used_con]

# 2) создать договор-черновик для ТЕКУЩИХ проживающих без договора (не помеченных выбывшими)
to_create=[]
for a in res_only2:
    r=res_by[a]
    if r.get("not_in_list_2026_10"): continue
    m={"fio":r.get("full_name",""),"contract_number":pad(r.get("contract_number","")),
       "contract_end_date":r.get("term",""),"room_number":r.get("block","")+("/"+r.get("room","") if r.get("room") else "")}
    to_create.append((r,m))

print("="*60)
print("MODE:", "APPLY" if APPLY else "DRY RUN")
print("="*60)
print("residents:",len(res)," contracts:",len(con))
print("Переименовать residents (выровнять с договором):",len(renamed))
print("Создать договоров-черновиков (текущим без договора):",len(to_create))
print("Останется residents без договора (выбывшие):",len([a for a in res_only2 if res_by[a].get("not_in_list_2026_10")]))
print("Останется договоров без проживающего:",len(con_only2))
print("="*60)
print("\n--- ПЕРЕИМЕНОВАНИЯ residents (было -> станет как в договоре) ---")
for a,b in renamed: print(f'  {a}  ->  {b}')
print("\n--- НОВЫЕ ЧЕРНОВИКИ ДОГОВОРОВ ---")
for r,m in to_create: print(f'  {m["room_number"]:8} {m["fio"]}  дог:{m["contract_number"]}')
print("\n--- ОСТАНУТСЯ: residents без договора (выбывшие) ---")
for a in res_only2:
    r=res_by[a]
    if r.get("not_in_list_2026_10"): print(f'  {r.get("block")}/{r.get("room")}  {r.get("full_name")}')
print("\n--- ОСТАНУТСЯ: договоры без проживающего ---")
for b in con_only2:
    c=con_by[b]; print(f'  {c.get("full_name")}  дог:{c.get("contract_number")}  flagged={c.get("not_in_list_2026_10",False)}')

if APPLY:
    print("\n>>> ПРИМЕНЯЮ...")
    n=0
    for an,bn in pairs:
        r=res_by[an]; c=con_by[bn]
        db.residents.update_one({"_id":r["_id"]},{"$set":{"full_name":c.get("full_name",""),"updated_at":now()}})
        n+=1
    print("Переименовано residents:",n)
    docs=[]
    for r,m in to_create:
        fields=md.master_to_contract(m)
        docs.append({"id":str(uuid.uuid4()),"contract_number":m["contract_number"],
            "full_name":m["fio"],"fields":{k:("" if v is None else str(v)) for k,v in fields.items()},
            "master":m,"status":"draft","demo":False,"counters":None,
            "needs_completion":True,"source_import_2026_10":True,
            "created_at":now(),"updated_at":now()})
    if docs: db.contracts.insert_many(docs)
    print("Создано договоров:",len(docs))
    print("ИТОГО residents:",db.residents.count_documents({})," contracts:",db.contracts.count_documents({}))
else:
    print("\n(DRY RUN — без записи)")
