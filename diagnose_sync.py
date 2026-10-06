#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Диагностика: сопоставление residents <-> contracts по ФИО."""
import re
from difflib import SequenceMatcher
from pymongo import MongoClient
db=MongoClient("mongodb://127.0.0.1:27017")["banetskaya_db"]
def norm(f): return re.sub(r"\s+"," ",(f or "").lower().replace("ё","е").strip())
def toks(n): return norm(n).split()

res=list(db.residents.find({}))
con=list(db.contracts.find({}))
con_by=dict()
for c in con: con_by.setdefault(norm(c.get("full_name","")),[]).append(c)
res_by=dict()
for r in res: res_by.setdefault(norm(r.get("full_name","")),[]).append(r)

# точное совпадение
res_norms=set(res_by); con_norms=set(con_by)
exact=res_norms & con_norms
res_only=res_norms - con_norms
con_only=con_norms - res_norms

def fuzzy_pairs(a_names, b_by):
    pairs=[]; rest=[]
    used=set()
    for an in a_names:
        at=an.split(); asur=at[0] if at else ""; af=at[1] if len(at)>1 else ""
        ap=at[2] if len(at)>2 else ""
        best=None; bs=0
        for bn in b_by:
            if bn in used: continue
            bt=bn.split(); bsur=bt[0] if bt else ""; bf=bt[1] if len(bt)>1 else ""
            bp=bt[2] if len(bt)>2 else ""
            fr=SequenceMatcher(None,an,bn).ratio()
            sr=SequenceMatcher(None,asur,bsur).ratio()
            sc=0
            if af and af==bf and sr>=0.72:
                if not(ap and bp and SequenceMatcher(None,ap,bp).ratio()<0.6):
                    sc=1.5+sr
            elif fr>=0.9: sc=fr
            if sc>bs: best,bs=bn,sc
        if best: used.add(best); pairs.append((an,best))
        else: rest.append(an)
    return pairs,rest

# residents без договора -> попробуем нечётко найти договор
r_pairs,r_rest=fuzzy_pairs(res_only, {c:1 for c in con_only})
# contracts без проживающего, оставшиеся
c_rest=[c for c in con_only if c not in {b for _,b in r_pairs}]

print("residents:",len(res)," contracts:",len(con))
print("точное совпадение ФИО:",len(exact))
print("residents без точного договора:",len(res_only))
print("contracts без точного проживающего:",len(con_only))
print("-- из них нечётко это ОДИН человек (разное написание):",len(r_pairs))
print("-- residents реально БЕЗ договора:",len(r_rest))
print("-- contracts реально БЕЗ проживающего:",len(c_rest))
print("\n=== ПАРЫ РАЗНОГО НАПИСАНИЯ (resident ФИО <-> contract ФИО) ===")
for a,b in r_pairs:
    rn=res_by[a][0].get("full_name"); cn=con_by[b][0].get("full_name")
    print(f'  RES: {rn}   <->   CON: {cn}')
print("\n=== RESIDENTS без договора (реально нет карточки) ===")
for a in r_rest:
    d=res_by[a][0]; print(f'  {d.get("block")}/{d.get("room")}  {d.get("full_name")}  flagged={d.get("not_in_list_2026_10",False)}')
print("\n=== CONTRACTS без проживающего (реально нет в заселении) ===")
for a in c_rest:
    d=con_by[a][0]; print(f'  {d.get("full_name")}  дог:{d.get("contract_number")}  flagged={d.get("not_in_list_2026_10",False)}  status={d.get("status")}')
