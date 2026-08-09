import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FIELDS } from "@/lib/fields";
import { saveContract, downloadSavedContract, api } from "@/lib/apiClient";
import { toast } from "sonner";
import { FileText, FileType, Printer, Save, Loader2 } from "lucide-react";

export default function EditContractDialog({ open, student, onClose, onSaved }) {
  const [fields, setFields] = useState(student || {});
  const [savedId, setSavedId] = useState(null);
  const [busy, setBusy] = useState("");

  // Reset when a new student is opened
  const [lastStudent, setLastStudent] = useState(student);
  if (student !== lastStudent) {
    setLastStudent(student);
    setFields(student || {});
    setSavedId(null);
  }

  const update = (key, value) => setFields((prev) => ({ ...prev, [key]: value }));

  async function ensureSaved() {
    if (savedId) return savedId;
    const created = await saveContract(fields);
    setSavedId(created.id);
    onSaved && onSaved();
    return created.id;
  }

  async function handleSave() {
    try {
      setBusy("save");
      await ensureSaved();
      toast.success("Договор сохранён в историю");
    } catch (e) {
      toast.error("Не удалось сохранить договор");
    } finally {
      setBusy("");
    }
  }

  async function handleDownload(format) {
    try {
      setBusy(format);
      const id = await ensureSaved();
      await downloadSavedContract(id, format, `Договор.${format}`);
      toast.success(format === "pdf" ? "PDF готов" : "Word-документ готов");
    } catch (e) {
      toast.error("Ошибка при формировании документа");
    } finally {
      setBusy("");
    }
  }

  async function handlePrint() {
    try {
      setBusy("print");
      const id = await ensureSaved();
      const res = await api.get(`/contracts/${id}/download`, {
        params: { format: "pdf" },
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(res.data);
      const w = window.open(url);
      if (w) w.onload = () => w.print();
      toast.success("Документ открыт для печати");
    } catch (e) {
      toast.error("Не удалось открыть для печати");
    } finally {
      setBusy("");
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto rounded-none" data-testid="edit-contract-dialog">
        <DialogHeader>
          <DialogTitle className="font-heading text-2xl tracking-tight">
            Ручная правка договора
          </DialogTitle>
        </DialogHeader>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 py-2">
          {FIELDS.map((f) => (
            <div key={f.key} className="space-y-1.5">
              <Label className="text-xs uppercase tracking-[0.1em] text-muted-foreground">
                {f.label}
              </Label>
              <Input
                className="rounded-none"
                value={fields[f.key] || ""}
                onChange={(e) => update(f.key, e.target.value)}
                data-testid={`field-${f.key}`}
              />
            </div>
          ))}
        </div>
        <DialogFooter className="flex-col sm:flex-row gap-2 sm:justify-between border-t border-border pt-4">
          <Button
            variant="outline"
            className="rounded-none"
            onClick={handleSave}
            disabled={!!busy}
            data-testid="save-history-btn"
          >
            {busy === "save" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            В историю
          </Button>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              className="rounded-none"
              onClick={handlePrint}
              disabled={!!busy}
              data-testid="print-btn"
            >
              {busy === "print" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Printer className="h-4 w-4" />}
              Печать
            </Button>
            <Button
              variant="outline"
              className="rounded-none"
              onClick={() => handleDownload("pdf")}
              disabled={!!busy}
              data-testid="download-pdf-btn"
            >
              {busy === "pdf" ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileType className="h-4 w-4" />}
              PDF
            </Button>
            <Button
              className="rounded-none bg-[#002FA7] hover:bg-[#00207A] text-white"
              onClick={() => handleDownload("docx")}
              disabled={!!busy}
              data-testid="download-docx-btn"
            >
              {busy === "docx" ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
              Скачать Word
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
