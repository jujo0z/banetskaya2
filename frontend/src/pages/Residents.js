import React, { useEffect, useState, useCallback, useRef } from "react";
import {
  residentsFloors,
  residentsFloor,
  residentsBlock,
  residentsImport,
  residentUpdate,
  residentCreate,
  residentDelete,
} from "@/lib/apiClient";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Building2,
  Upload,
  Users,
  DoorClosed,
  AlertTriangle,
  Pencil,
  Trash2,
  UserPlus,
  X,
  BadgeCheck,
} from "lucide-react";
import { toast } from "sonner";

const EMPTY = {
  full_name: "",
  block: "",
  room: "",
  status: "",
  study_group: "",
  benefit: "",
  contract_number: "",
  move_in_date: "",
  term: "",
  note: "",
};

export default function Residents() {
  const [floors, setFloors] = useState([]);
  const [total, setTotal] = useState(0);
  const [activeFloor, setActiveFloor] = useState(null);
  const [floorData, setFloorData] = useState(null);
  const [blockData, setBlockData] = useState(null);
  const [blockOpen, setBlockOpen] = useState(false);
  const [loadingBlock, setLoadingBlock] = useState(false);
  const [importing, setImporting] = useState(false);
  const [editing, setEditing] = useState(null); // resident being edited (or new)
  const fileRef = useRef(null);

  const loadFloors = useCallback(async () => {
    try {
      const data = await residentsFloors();
      setFloors(data.floors || []);
      setTotal(data.total || 0);
      if (data.floors && data.floors.length && activeFloor === null) {
        setActiveFloor(data.floors[0].floor);
      }
    } catch (e) {
      toast.error("Не удалось загрузить этажи");
    }
  }, [activeFloor]);

  const loadFloor = useCallback(async (floor) => {
    if (floor === null || floor === undefined) return;
    try {
      const data = await residentsFloor(floor);
      setFloorData(data);
    } catch (e) {
      toast.error("Не удалось загрузить этаж");
    }
  }, []);

  useEffect(() => {
    loadFloors();
  }, [loadFloors]);

  useEffect(() => {
    if (activeFloor !== null) loadFloor(activeFloor);
  }, [activeFloor, loadFloor]);

  const openBlock = async (block) => {
    setLoadingBlock(true);
    setBlockOpen(true);
    try {
      const data = await residentsBlock(block);
      setBlockData(data);
    } catch (e) {
      toast.error("Не удалось загрузить блок");
    } finally {
      setLoadingBlock(false);
    }
  };

  const refreshAll = async () => {
    await loadFloors();
    if (activeFloor !== null) await loadFloor(activeFloor);
    if (blockData) {
      const data = await residentsBlock(blockData.block);
      setBlockData(data);
    }
  };

  const handleImportFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    try {
      const res = await residentsImport(file);
      toast.success(`Импортировано жильцов: ${res.imported}`);
      setActiveFloor(null);
      await loadFloors();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Ошибка импорта Excel");
    } finally {
      setImporting(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const saveResident = async (form) => {
    try {
      if (form.id) {
        await residentUpdate(form.id, form);
        toast.success("Изменения сохранены");
      } else {
        await residentCreate(form);
        toast.success("Жилец добавлен");
      }
      setEditing(null);
      await refreshAll();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Не удалось сохранить");
    }
  };

  const removeResident = async (id) => {
    try {
      await residentDelete(id);
      toast.success("Удалено");
      await refreshAll();
    } catch (err) {
      toast.error("Не удалось удалить");
    }
  };

  return (
    <div className="space-y-8" data-testid="residents-page">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="font-heading text-3xl font-bold tracking-tight flex items-center gap-3">
            <span className="h-11 w-11 rounded-2xl bg-gradient-to-br from-[#F43F5E] to-[#DB2777] flex items-center justify-center glow-crimson">
              <Building2 className="h-6 w-6 text-white" />
            </span>
            Заселение по этажам
          </h1>
          <p className="text-muted-foreground mt-2">
            Распределение жильцов · этаж → 15 блоков → люди. Несовпадения с базой договоров подсвечиваются.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="secondary" className="text-sm px-3 py-1.5">
            <Users className="h-4 w-4 mr-1.5" /> Всего: {total}
          </Badge>
          <input
            ref={fileRef}
            type="file"
            accept=".xlsx,.xls"
            className="hidden"
            onChange={handleImportFile}
            data-testid="residents-import-input"
          />
          <Button
            onClick={() => fileRef.current?.click()}
            disabled={importing}
            data-testid="residents-import-btn"
          >
            <Upload className="h-4 w-4 mr-2" />
            {importing ? "Импорт..." : "Загрузить Excel заселения"}
          </Button>
        </div>
      </div>

      {total === 0 ? (
        <EmptyState onImport={() => fileRef.current?.click()} />
      ) : (
        <>
          {/* Floor selector */}
          <div className="flex flex-wrap gap-2" data-testid="floor-selector">
            {floors.map((f) => (
              <button
                key={f.floor}
                onClick={() => setActiveFloor(f.floor)}
                data-testid={`floor-btn-${f.floor}`}
                className={`px-4 py-2 rounded-xl text-sm font-semibold border transition-all ${
                  activeFloor === f.floor
                    ? "bg-gradient-to-r from-[#F43F5E] to-[#DB2777] text-white border-transparent shadow-lg"
                    : "bg-white/70 border-pink-100 text-slate-700 hover:bg-white"
                }`}
              >
                {f.floor} этаж
                <span className="ml-2 opacity-70 font-normal">{f.people}</span>
              </button>
            ))}
          </div>

          {/* Blocks grid */}
          <div
            className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4"
            data-testid="blocks-grid"
          >
            {floorData?.blocks?.map((b) => (
              <button
                key={b.block}
                onClick={() => b.people > 0 && openBlock(b.block)}
                disabled={b.people === 0}
                data-testid={`block-card-${b.block}`}
                className={`group relative rounded-2xl border p-5 text-left transition-all ${
                  b.people > 0
                    ? "glass border-pink-100 hover:border-[#EC4899]/50 hover:shadow-xl cursor-pointer"
                    : "bg-slate-50 border-slate-100 opacity-60 cursor-default"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-heading text-2xl font-bold tracking-tight">
                    {b.block}
                  </span>
                  <DoorClosed
                    className={`h-5 w-5 ${
                      b.people > 0 ? "text-[#EC4899]" : "text-slate-300"
                    }`}
                  />
                </div>
                <div className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
                  <Users className="h-4 w-4" />
                  {b.people > 0 ? `${b.people} чел.` : "пусто"}
                </div>
                {b.rooms?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {b.rooms.map((r) => (
                      <span
                        key={r}
                        className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-pink-50 text-[#DB2777] border border-pink-100"
                      >
                        /{r}
                      </span>
                    ))}
                  </div>
                )}
              </button>
            ))}
          </div>
        </>
      )}

      {/* Block dialog */}
      <Dialog open={blockOpen} onOpenChange={setBlockOpen}>
        <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              <Building2 className="h-5 w-5 text-[#EC4899]" />
              Блок {blockData?.block}
              <span className="text-sm font-normal text-muted-foreground">
                · {blockData?.total || 0} чел.
              </span>
            </DialogTitle>
          </DialogHeader>

          {loadingBlock ? (
            <div className="py-10 text-center text-muted-foreground">Загрузка...</div>
          ) : (
            <div className="space-y-6">
              {blockData?.rooms?.map((r) => (
                <div key={r.room || "no-room"}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono uppercase tracking-[0.2em] text-slate-400">
                        Комната
                      </span>
                      <Badge className="bg-pink-100 text-[#DB2777] hover:bg-pink-100">
                        {blockData.block}/{r.room || "—"}
                      </Badge>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        setEditing({ ...EMPTY, block: blockData.block, room: r.room })
                      }
                      data-testid={`add-person-${r.room}`}
                    >
                      <UserPlus className="h-4 w-4 mr-1.5" /> Добавить
                    </Button>
                  </div>
                  <div className="space-y-2">
                    {r.people.map((p) => (
                      <PersonCard
                        key={p.id}
                        p={p}
                        onEdit={() => setEditing(p)}
                        onDelete={() => removeResident(p.id)}
                      />
                    ))}
                  </div>
                </div>
              ))}
              <Button
                variant="outline"
                className="w-full"
                onClick={() => setEditing({ ...EMPTY, block: blockData.block, room: "" })}
                data-testid="add-person-block"
              >
                <UserPlus className="h-4 w-4 mr-2" /> Добавить человека в блок
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit dialog */}
      <EditResidentDialog
        resident={editing}
        onClose={() => setEditing(null)}
        onSave={saveResident}
      />
    </div>
  );
}

function PersonCard({ p, onEdit, onDelete }) {
  const c = p.checks || {};
  const hasIssue = (c.mismatches || []).length > 0;
  return (
    <div
      data-testid={`person-${p.id}`}
      className={`rounded-xl border p-3.5 transition-all ${
        hasIssue
          ? "border-amber-300 bg-amber-50/60"
          : "border-slate-100 bg-white/70"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="font-semibold text-slate-900 flex items-center gap-2 flex-wrap">
            {p.full_name}
            {c.has_contract && !hasIssue && (
              <BadgeCheck className="h-4 w-4 text-emerald-500" title="Совпадает с договором" />
            )}
          </div>
          <div className="mt-1.5 flex flex-wrap gap-1.5 text-xs">
            <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-mono">
              {p.block}/{p.room || "—"}
            </span>
            {p.status && (
              <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                {p.status}
              </span>
            )}
            {p.study_group && (
              <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-600 border border-indigo-100">
                {p.study_group}
              </span>
            )}
            {p.benefit && (
              <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-100">
                Льгота: {p.benefit}
              </span>
            )}
            {p.contract_number && (
              <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-mono">
                № {p.contract_number}
              </span>
            )}
          </div>
          {p.note && (
            <div className="mt-1.5 text-xs text-slate-400 italic">{p.note}</div>
          )}
          {hasIssue && (
            <div className="mt-2 space-y-1">
              {c.mismatches.map((m, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 text-xs text-amber-800 bg-amber-100/70 rounded px-2 py-1"
                >
                  <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                  <span>
                    <b>{m.label}:</b> заселение «{m.accommodation}» ≠ договор «{m.contract}»
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="flex flex-col gap-1.5 shrink-0">
          <Button size="icon" variant="ghost" className="h-8 w-8" onClick={onEdit}
            data-testid={`edit-${p.id}`}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button size="icon" variant="ghost" className="h-8 w-8 text-rose-500 hover:text-rose-600"
            onClick={onDelete} data-testid={`delete-${p.id}`}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

function EditResidentDialog({ resident, onClose, onSave }) {
  const [form, setForm] = useState(EMPTY);
  useEffect(() => {
    if (resident) {
      setForm({ ...EMPTY, ...resident });
    }
  }, [resident]);

  if (!resident) return null;
  const isNew = !resident.id;
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const fields = [
    { k: "full_name", label: "ФИО", col: 2 },
    { k: "block", label: "Блок (напр. 902)" },
    { k: "room", label: "Комната (напр. 2)" },
    { k: "status", label: "Статус" },
    { k: "study_group", label: "Учебная группа" },
    { k: "benefit", label: "ЛЬГОТА" },
    { k: "contract_number", label: "Номер договора" },
    { k: "move_in_date", label: "Дата заселения" },
    { k: "term", label: "Срок действия" },
  ];

  return (
    <Dialog open={!!resident} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-lg max-h-[88vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isNew ? "Новый жилец" : "Редактирование жильца"}
          </DialogTitle>
        </DialogHeader>
        <div className="grid grid-cols-2 gap-3 py-2">
          {fields.map((f) => (
            <div key={f.k} className={f.col === 2 ? "col-span-2" : ""}>
              <Label className="text-xs text-slate-500">{f.label}</Label>
              <Input
                value={form[f.k] || ""}
                onChange={set(f.k)}
                data-testid={`field-${f.k}`}
                className="mt-1"
              />
            </div>
          ))}
          <div className="col-span-2">
            <Label className="text-xs text-slate-500">Примечание</Label>
            <Textarea
              value={form.note || ""}
              onChange={set("note")}
              data-testid="field-note"
              className="mt-1"
              rows={2}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            <X className="h-4 w-4 mr-1.5" /> Отмена
          </Button>
          <Button onClick={() => onSave(form)} data-testid="save-resident">
            Сохранить
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function EmptyState({ onImport }) {
  return (
    <div className="rounded-3xl border border-dashed border-pink-200 bg-white/50 py-16 px-8 text-center">
      <div className="mx-auto h-16 w-16 rounded-2xl bg-gradient-to-br from-[#F43F5E] to-[#DB2777] flex items-center justify-center glow-crimson">
        <Building2 className="h-8 w-8 text-white" />
      </div>
      <h3 className="mt-5 font-heading text-xl font-bold">Пока нет данных о заселении</h3>
      <p className="mt-2 text-muted-foreground max-w-md mx-auto">
        Загрузите Excel-файл заселения (с колонками «Блок», «Ф.И.О», «Статус», «Группа»…),
        и мы разложим всех жильцов по этажам и блокам.
      </p>
      <Button className="mt-6" onClick={onImport} data-testid="empty-import-btn">
        <Upload className="h-4 w-4 mr-2" /> Загрузить Excel заселения
      </Button>
    </div>
  );
}
