import React, { useEffect, useMemo, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Search, Users, Loader2 } from "lucide-react";
import { listContracts } from "@/lib/apiClient";
import { toast } from "sonner";

// Общий выбор человека(-ей) из единой базы проживающих.
// onPick получает массив выбранных договоров (с полями .id, .full_name, .contract_number, .fields, .master).
export default function ResidentPicker({
  open,
  onClose,
  onPick,
  multiple = true,
  title = "Выбрать из базы проживающих",
}) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [q, setQ] = useState("");
  const [sel, setSel] = useState(new Set());

  useEffect(() => {
    if (!open) return;
    setSel(new Set());
    setQ("");
    setLoading(true);
    listContracts("", "")
      .then((d) => setRows(d || []))
      .catch(() => toast.error("Не удалось загрузить базу проживающих"))
      .finally(() => setLoading(false));
  }, [open]);

  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    if (!s) return rows;
    return rows.filter(
      (r) =>
        (r.full_name || "").toLowerCase().includes(s) ||
        (r.contract_number || "").toLowerCase().includes(s) ||
        String(r.fields?.room_number || "").toLowerCase().includes(s)
    );
  }, [rows, q]);

  const toggle = (id) =>
    setSel((p) => {
      const n = new Set(multiple ? p : []);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });

  const confirm = () => {
    const picked = rows.filter((r) => sel.has(r.id));
    if (!picked.length) {
      toast.error("Никто не выбран");
      return;
    }
    onPick(picked);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Users className="h-5 w-5 text-[#EC4899]" /> {title}
          </DialogTitle>
        </DialogHeader>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Поиск по ФИО, номеру договора или комнате"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            data-testid="picker-search"
            autoFocus
          />
        </div>

        <div className="max-h-[50vh] overflow-y-auto border rounded-lg divide-y">
          {loading && (
            <div className="p-6 text-center text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin inline" /> Загрузка…
            </div>
          )}
          {!loading && filtered.length === 0 && (
            <div className="p-6 text-center text-muted-foreground">
              Никого не найдено
            </div>
          )}
          {!loading &&
            filtered.map((r) => (
              <label
                key={r.id}
                className="flex items-center gap-3 px-3 py-2 hover:bg-pink-50 cursor-pointer"
                data-testid={`picker-row-${r.id}`}
              >
                <Checkbox
                  checked={sel.has(r.id)}
                  onCheckedChange={() => toggle(r.id)}
                />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">
                    {r.full_name || "—"}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    № {r.contract_number || "—"} · комн.{" "}
                    {r.fields?.room_number || "—"}
                  </div>
                </div>
              </label>
            ))}
        </div>

        <DialogFooter className="flex items-center justify-between sm:justify-between">
          <div className="text-sm text-muted-foreground">Выбрано: {sel.size}</div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose}>
              Отмена
            </Button>
            <Button
              className="bg-[#EC4899] hover:bg-[#DB2777] text-white"
              onClick={confirm}
              data-testid="picker-confirm"
            >
              Подставить{sel.size ? ` (${sel.size})` : ""}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
