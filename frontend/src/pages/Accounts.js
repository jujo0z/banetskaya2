import React, { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { KeyRound, Trash2, Plus, Send, Users } from "lucide-react";
import {
  listAccounts, createAccount, updateAccount, deleteAccount,
  residentsFloors, telegramInfo, telegramSetupMenu,
} from "@/lib/apiClient";

const DEFAULT_FLOORS = [1, 2, 3, 4, 5, 6, 7, 8, 9];

function FloorToggles({ floors, selected, onToggle }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {floors.map((f) => (
        <button
          key={f}
          type="button"
          onClick={() => onToggle(f)}
          className={`h-9 w-11 rounded-lg border text-sm font-semibold transition-all ${
            selected.includes(f)
              ? "bg-gradient-to-r from-[#F43F5E] to-[#DB2777] text-white border-transparent"
              : "bg-white text-slate-600 border-slate-200 hover:border-pink-300"
          }`}
        >
          {f}
        </button>
      ))}
    </div>
  );
}

export default function Accounts() {
  const [accounts, setAccounts] = useState([]);
  const [availFloors, setAvailFloors] = useState(DEFAULT_FLOORS);
  // new account form
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [floors, setFloors] = useState([]);
  // telegram
  const [botName, setBotName] = useState("");
  const [miniUrl, setMiniUrl] = useState("");

  const load = useCallback(async () => {
    try { setAccounts(await listAccounts()); } catch (e) {}
    try {
      const d = await residentsFloors();
      const fl = (d.floors || []).map((x) => x.floor).filter((x) => x > 0);
      if (fl.length) setAvailFloors(fl);
    } catch (e) {}
  }, []);

  useEffect(() => {
    load();
    setMiniUrl(`${window.location.origin}/tg`);
    telegramInfo().then((d) => {
      if (d?.ok && d?.result?.username) setBotName("@" + d.result.username);
    }).catch(() => {});
  }, [load]);

  const toggleFloor = (f) => setFloors((s) => (s.includes(f) ? s.filter((x) => x !== f) : [...s, f]));

  const create = async () => {
    if (!username.trim() || !password.trim()) { toast.error("Укажите логин и пароль"); return; }
    if (floors.length === 0) { toast.error("Выберите хотя бы один этаж"); return; }
    try {
      await createAccount({ username: username.trim(), password: password.trim(), full_name: fullName.trim(), floors });
      toast.success("Учётка создана");
      setUsername(""); setPassword(""); setFullName(""); setFloors([]);
      await load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Не удалось создать"); }
  };

  const del = async (id) => {
    try { await deleteAccount(id); toast.success("Учётка удалена"); await load(); }
    catch (e) { toast.error("Не удалось удалить"); }
  };

  const setupBot = async () => {
    try {
      await telegramSetupMenu(miniUrl);
      toast.success("Кнопка бота настроена — открывайте Mini App в Telegram");
    } catch (e) { toast.error(e?.response?.data?.detail || "Не удалось настроить бота"); }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-bold tracking-tight">Доступы старост</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Учётные записи для старост: логин, пароль и этажи, где они могут выставлять оценки.
        </p>
      </div>

      {/* Telegram card */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-3">
        <h3 className="font-semibold flex items-center gap-2"><Send className="h-4 w-4 text-sky-500" /> Telegram Mini App</h3>
        <p className="text-sm text-muted-foreground">
          Бот: <span className="font-mono font-semibold text-slate-700">{botName || "—"}</span>. Старосты и учащиеся открывают приложение через кнопку-меню бота.
        </p>
        <div className="flex flex-col sm:flex-row gap-2">
          <input
            value={miniUrl}
            onChange={(e) => setMiniUrl(e.target.value)}
            className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono"
          />
          <button onClick={setupBot} data-testid="telegram-setup-btn" className="px-4 py-2 rounded-lg bg-sky-500 text-white text-sm font-semibold hover:bg-sky-600">
            Настроить кнопку бота
          </button>
        </div>
        <p className="text-[11px] text-slate-400">
          URL должен быть публичным https-адресом (боевой сервер banetskaya.duckdns.org/tg).
        </p>
      </div>

      {/* New account */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-4">
        <h3 className="font-semibold flex items-center gap-2"><Plus className="h-4 w-4 text-pink-500" /> Новая учётка старосты</h3>
        <div className="grid sm:grid-cols-3 gap-3">
          <div>
            <label className="text-xs text-muted-foreground">Логин</label>
            <input data-testid="acc-username" value={username} onChange={(e) => setUsername(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" placeholder="starosta9" />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Пароль</label>
            <input data-testid="acc-password" value={password} onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" placeholder="••••••" />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">ФИО (необязательно)</label>
            <input value={fullName} onChange={(e) => setFullName(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" placeholder="Иванова А.А." />
          </div>
        </div>
        <div>
          <label className="text-xs text-muted-foreground">Доступ к этажам</label>
          <div className="mt-1"><FloorToggles floors={availFloors} selected={floors} onToggle={toggleFloor} /></div>
        </div>
        <button data-testid="acc-create-btn" onClick={create}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#F43F5E] to-[#DB2777] text-white font-semibold">
          Создать учётку
        </button>
      </div>

      {/* Accounts list */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <h3 className="font-semibold mb-3 flex items-center gap-2"><Users className="h-4 w-4 text-slate-500" /> Учётные записи</h3>
        {accounts.length === 0 && <div className="text-sm text-muted-foreground">Пока нет учёток.</div>}
        <div className="space-y-2" data-testid="accounts-list">
          {accounts.map((a) => (
            <AccountRow key={a.id} acc={a} availFloors={availFloors} onDelete={del} onSaved={load} />
          ))}
        </div>
      </div>
    </div>
  );
}

function AccountRow({ acc, availFloors, onDelete, onSaved }) {
  const [editing, setEditing] = useState(false);
  const [floors, setFloors] = useState(acc.floors || []);
  const [pass, setPass] = useState("");

  const toggle = (f) => setFloors((s) => (s.includes(f) ? s.filter((x) => x !== f) : [...s, f]));

  const save = async () => {
    try {
      const payload = { floors };
      if (pass.trim()) payload.password = pass.trim();
      await updateAccount(acc.id, payload);
      toast.success("Сохранено");
      setEditing(false); setPass("");
      onSaved();
    } catch (e) { toast.error("Не удалось сохранить"); }
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <KeyRound className="h-4 w-4 text-slate-400" />
          <div>
            <div className="font-semibold text-sm">{acc.username}
              {acc.role === "admin" && <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-white">админ</span>}
            </div>
            <div className="text-xs text-muted-foreground">
              {acc.full_name || "—"} · этажи: {(acc.floors || []).join(", ") || "нет"}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => setEditing((v) => !v)} className="text-xs text-pink-600 hover:underline">
            {editing ? "Отмена" : "Изменить"}
          </button>
          <button onClick={() => onDelete(acc.id)} className="text-slate-400 hover:text-red-500">
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
      {editing && (
        <div className="mt-3 pt-3 border-t border-slate-200 space-y-3">
          <div>
            <label className="text-xs text-muted-foreground">Этажи</label>
            <div className="mt-1"><FloorToggles floors={availFloors} selected={floors} onToggle={toggle} /></div>
          </div>
          <div className="flex gap-2 items-end">
            <div className="flex-1">
              <label className="text-xs text-muted-foreground">Новый пароль (пусто — не менять)</label>
              <input value={pass} onChange={(e) => setPass(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" placeholder="••••••" />
            </div>
            <button onClick={save} className="px-4 py-2 rounded-lg bg-slate-800 text-white text-sm font-semibold">Сохранить</button>
          </div>
        </div>
      )}
    </div>
  );
}
