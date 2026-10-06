#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Слияние файла заселения с главной базой contracts.
  python3 merge_contracts.py        # DRY RUN
  python3 merge_contracts.py apply  # применить
Запускать с cwd=/opt/banetskaya/backend (нужен import master_data).
"""
import re, sys, uuid
from datetime import datetime, timezone, date
from difflib import SequenceMatcher
from openpyxl import load_workbook
from pymongo import MongoClient
import master_data as md

XLSX="/root/dlya_ivana.xlsx"
APPLY=len(sys.argv)>1 and sys.argv[1]=="apply"
db=MongoClient("mongodb://127.0.0.1:27017")["banetskaya_db"]

def now(): return datetime.now(timezone.utc).isoformat()
def cl(v):
    if v is None: return ""
    if isinstance(v,(datetime,date)): return v.strftime("%d.%m.%Y")
    s=str(v).strip(); m=re.match(r"^(\d{4})-(\d{2})-(\d{2})",s)
    return f"{m.group(3)}.{m.group(2)}.{m.group(1)}" if m else s
def norm(f): return re.sub(r"\s+"," ",(f or "").lower().replace("ё","е").strip())
def digits(s): return re.sub(r"\D","",s or "")
def pad(num):
    d=digits(num)
    return d.zfill(6) if d else ""
def fix_date(s):
    s=(s or "").strip()
    m=re.match(r"^(\d{2})\.(\d{2})(\d{4})$",s)        # пропущена точка: 30.062027
    if m: return f"{m.group(1)}.{m.group(2)}.{m.group(3)}"
    if s=="12.07.202": return "12.07.2027"            # обрезанный год
    return s
def toks(n): return norm(n).split()

# ---- файл ----
wb=load_workbook(XLSX,data_only=True); ws=wb[wb.sheetnames[0]]
rows=list(ws.iter_rows(values_only=True))
people=[]; seen=set()
for r in rows[3:]:
    def g(i): return cl(r[i]) if i<len(r) else ""
    fio=g(2)
    if not fio: continue
    nkey=norm(fio)
    if nkey in seen: continue
    seen.add(nkey)
    people.append({"fio":fio,"block":g(1),"group":g(4),"status":g(3),
                   "move_in":g(5),"num":pad(g(6)),"term":fix_date(g(7))})

docs=list(db.contracts.find({}))
by_norm={}
for d in docs: by_norm.setdefault(norm(d.get("full_name","")),[]).append(d)

def fuzzy(fio, free):
    pt=toks(fio); ps=pt[0] if pt else ""; pf=pt[1] if len(pt)>1 else ""
    pp=pt[2] if len(pt)>2 else ""
    best=None; bs=0
    for d in free:
        dt=toks(d.get("full_name","")); ds=dt[0] if dt else ""; df=dt[1] if len(dt)>1 else ""
        dp=dt[2] if len(dt)>2 else ""
        fr=SequenceMatcher(None,norm(fio),norm(d.get("full_name",""))).ratio()
        sr=SequenceMatcher(None,ps,ds).ratio()
        sc=0
        # строго: то же имя + похожая фамилия(>=0.72) + не противоречит отчество
        if pf and pf==df and sr>=0.72:
            patr_ok = True
            if pp and dp and SequenceMatcher(None,pp,dp).ratio()<0.6:
                patr_ok=False
            if patr_ok: sc=1.5+sr
        elif fr>=0.92:
            sc=fr
        if sc>bs: best,bs=d,sc
    return best

used=set()
upd_term=upd_room=upd_name=upd_padnum=0
new_cards=[]; updates=[]; name_fixes=[]
for p in people:
    cands=[d for d in by_norm.get(norm(p["fio"]),[]) if d["_id"] not in used]
    d=cands[0] if cands else fuzzy(p["fio"],[x for x in docs if x["_id"] not in used])
    if d is None:
        # новая частичная карточка (черновик)
        m={"fio":p["fio"],"contract_number":p["num"],
           "contract_end_date":p["term"],"room_number":p["block"],
           "reg_to_date":p["term"]}
        fields=md.master_to_contract(m)
        doc={"id":str(uuid.uuid4()),"contract_number":p["num"],"full_name":p["fio"],
             "fields":{k:("" if v is None else str(v)) for k,v in fields.items()},
             "master":m,"status":"draft","demo":False,"counters":None,
             "needs_completion":True,"source_import_2026_10":True,
             "study_group":p["group"],"status_note":p["status"],
             "created_at":now(),"updated_at":now()}
        new_cards.append(doc)
        continue
    used.add(d["_id"])
    m=dict(d.get("master") or {})
    if not any(str(v).strip() for v in m.values()):
        m=md.contract_to_master(d.get("fields",{}) or {})
    changed=False
    # номер: привести к 6 цифрам с ведущими нулями
    base_num_padded=pad(d.get("contract_number") or m.get("contract_number",""))
    if base_num_padded and (d.get("contract_number")!=base_num_padded or m.get("contract_number")!=base_num_padded):
        m["contract_number"]=base_num_padded; changed=True; upd_padnum+=1
    # срок
    if p["term"] and m.get("contract_end_date","")!=p["term"]:
        m["contract_end_date"]=p["term"]; changed=True; upd_term+=1
    # комната
    if p["block"] and m.get("room_number","")!=p["block"]:
        m["room_number"]=p["block"]; changed=True; upd_room+=1
    # имя НЕ меняем (ФИО в юр.карточке — официальное; в файле встречаются опечатки).
    # Фиксируем лишь расхождение для отчёта.
    if d.get("full_name","")!=p["fio"]:
        name_fixes.append(f'{d.get("full_name")}  (файл: {p["fio"]})')
    if changed:
        fields=md.master_to_contract(m)
        updates.append((d["_id"],{
            "master":m,
            "fields":{k:("" if v is None else str(v)) for k,v in fields.items()},
            "full_name":m.get("fio",d.get("full_name","")),
            "contract_number":base_num_padded or d.get("contract_number",""),
            "updated_at":now()}))

not_in_file=[d for d in docs if d["_id"] not in used]

print("="*60)
print("MODE:", "APPLY" if APPLY else "DRY RUN")
print("="*60)
print("Студентов в файле:            ", len(people))
print("Записей в базе contracts:     ", len(docs))
print("Обновлений (совпали):         ", len(updates))
print("  - срок:", upd_term, " комната:", upd_room, " имя:", upd_name, " формат номера:", upd_padnum)
print("Новых частичных карточек:     ", len(new_cards))
print("В базе, нет в файле (пометим): ", len(not_in_file))
print("="*60)
print("\n--- ИСПРАВЛЕНИЯ ИМЁН [до 25] ---")
for x in name_fixes[:25]: print("  ",x)
print("\n--- НОВЫЕ ЧАСТИЧНЫЕ (черновики) [до 20] ---")
for d in new_cards[:20]: print(f'  {d["master"]["room_number"]:8} {d["full_name"]}  дог:{d["contract_number"]} срок:{d["master"]["contract_end_date"]}')
print("  всего:",len(new_cards))
print("\n--- В БАЗЕ, НЕТ В ФАЙЛЕ ---")
for d in not_in_file: print(f'  {d.get("full_name")}  дог:{d.get("contract_number")}')

if APPLY:
    print("\n>>> ПРИМЕНЯЮ...")
    for _id,vals in updates:
        db.contracts.update_one({"_id":_id},{"$set":vals})
    if new_cards:
        db.contracts.insert_many(new_cards)
    if not_in_file:
        db.contracts.update_many({"_id":{"$in":[d["_id"] for d in not_in_file]}},
            {"$set":{"not_in_list_2026_10":True,"updated_at":now()}})
    print("Готово. contracts в базе теперь:", db.contracts.count_documents({}))
    print("draft (частичные):", db.contracts.count_documents({"status":"draft"}))
else:
    print("\n(DRY RUN — без записи. Применить: python3 merge_contracts.py apply)")
