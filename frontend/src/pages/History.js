import { useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Search, FileText, FileType, Printer, Trash2, FileArchive, Loader2, Eye, Pencil, FileClock, FileSpreadsheet, Layers, Stamp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import {
  listContracts,
  deleteContract,
  downloadSavedContract,
  batchDownload,
  batchPrint,
  savedPdfUrl,
  exportHistory,
  api,
  contractToOverlay,
  openOverlayPdf,
  printOverlaySilent,
} from "@/lib/apiClient";
import { IS_DESKTOP } from "@/lib/env";
import DocumentPreviewDialog from "@/components/DocumentPreviewDialog";
import DocumentEditor from "@/components/DocumentEditor";
import ManualDuplexDialog from "@/components/ManualDuplexDialog";

export default function History() {
  const navigate = useNavigate();
  const [contracts, setContracts] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(new Set());
  const [batchFormat, setBatchFormat] = useState("docx");
  const [busyId, setBusyId] = useState("");
  const [batching, setBatching] = useState(false);
  const [batchPrinting, setBatchPrinting] = useState(false);
  const [blankPrinting, setBlankPrinting] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [toDelete, setToDelete] = useState(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [editing, setEditing] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [duplexOpen, setDuplexOpen] = useState(false);

  async function handleExport() {
    setExporting(true);
    try {
      await exportHistory(search, statusFilter);
      toast.success("Реестр Excel сформирован");
    } catch (e) {
      toast.error("Не удалось сформировать реестр");
    } finally {
      setExporting(false);
    }
  }

  async function load(q = "", status = statusFilter) {
    setLoading(true);
    try {
      const data = await listContracts(q, status);
      setContracts(data);
    } catch (e) {
      toast.error("Не удалось загрузить историю");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line
  }, []);

  useEffect(() => {
    const t = setTimeout(() => load(search, statusFilter), 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line
  }, [search, statusFilter]);

  function toggle(id) {
    setSelected((prev) => {
      const n = new Set(prev);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });
  }

  const allSelected = contracts.length > 0 && contracts.every((c) => selected.has(c.id));
  function toggleAll() {
    setSelected(allSelected ? new Set() : new Set(contracts.map((c) => c.id)));
  }

  async function handleDownload(c, format) {
    setBusyId(`${c.id}-${format}`);
    try {
      await downloadSavedContract(c.id, format, `Договор.${format}`);
    } catch (e) {
      toast.error("Ошибка при формировании документа");
    } finally {
      setBusyId("");
    }
  }

  async function handlePrint(c) {
    setBusyId(`${c.id}-print`);
    try {
      const res = await api.get(`/contracts/${c.id}/download`, {
        params: { format: "pdf" },
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(res.data);
      const w = window.open(url);
      if (w) w.onload = () => w.print();
    } catch (e) {
      toast.error("Не удалось открыть для печати");
    } finally {
      setBusyId("");
    }
  }

  async function handlePreview(c) {
    setBusyId(`${c.id}-preview`);
    try {
      const url = await savedPdfUrl(c.id);
      setPreviewUrl(url);
    } catch (e) {
      toast.error("Не удалось открыть просмотр");
    } finally {
      setBusyId("");
    }
  }

  async function handleDelete() {
    if (!toDelete) return;
    try {
      await deleteContract(toDelete.id);
      toast.success("Договор удалён");
      setSelected((prev) => {
        const n = new Set(prev);
        n.delete(toDelete.id);
        return n;
      });
      load(search);
    } catch (e) {
      toast.error("Не удалось удалить");
    } finally {
      setToDelete(null);
    }
  }

  async function handleBatch() {
    if (selected.size === 0) return;
    setBatching(true);
    try {
      await batchDownload([...selected], batchFormat);
      toast.success("Архив сформирован");
    } catch (e) {
      toast.error("Ошибка пакетной выгрузки");
    } finally {
      setBatching(false);
    }
  }

  async function handleBatchPrint() {
    if (selected.size === 0) return;
    setBatchPrinting(true);
    try {
      await batchPrint([...selected]);
      toast.success(`Открыто на печать: ${selected.size}`);
    } catch (e) {
      toast.error("Не удалось открыть на печать");
    } finally {
      setBatchPrinting(false);
    }
  }

  // Open the СООБЩЕНИЕ blank (overlay or full print) with this contract prefilled.
  function openBlank(c, path) {
    navigate(path, { state: { prefill: contractToOverlay(c) } });
  }

  // Batch-print СООБЩЕНИЕ blanks (147×103) for all selected contracts, one job.
  async function handleBatchBlankPrint() {
    if (selected.size === 0) return;
    const records = contracts
      .filter((c) => selected.has(c.id))
      .map((c) => contractToOverlay(c));
    if (records.length === 0) return;
    setBlankPrinting(true);
    try {
      if (IS_DESKTOP) {
        const res = await printOverlaySilent(records, { pageSize: "card" });
        toast.success(`Бланки отправлены на печать (147×103 мм): ${res.pages}`);
      } else {
        await openOverlayPdf(records, { pageSize: "card" });
        toast(`PDF из ${records.length} бланков (147×103) открыт — печатайте «Фактический размер» (100%)`);
      }
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Не удалось напечатать бланки");
    } finally {
      setBlankPrinting(false);
    }
  }

  function fmtDate(iso) {
    try {
      return new Date(iso).toLocaleString("ru-RU", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-4xl sm:text-5xl font-black tracking-tighter">
          История договоров
        </h1>
        <p className="text-muted-foreground mt-2">
          Поиск по ФИО и номеру договора, повторная печать и выгрузка.
        </p>
      </div>

      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-1 bg-card border border-border p-1 w-fit rounded-md" data-testid="history-status-tabs">
          {[
            { k: "", label: "Все" },
            { k: "final", label: "Готовые" },
            { k: "draft", label: "Черновики" },
          ].map((t) => (
            <button
              key={t.k}
              onClick={() => setStatusFilter(t.k)}
              className={`px-4 py-1.5 text-sm rounded-sm transition-colors ${
                statusFilter === t.k
                  ? "bg-[#E11D48] text-white"
                  : "text-muted-foreground hover:text-white"
              }`}
              data-testid={`history-filter-${t.k || "all"}`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <Button
          variant="outline"
          className="rounded-none border-white/15"
          onClick={handleExport}
          disabled={exporting}
          data-testid="history-export-excel-btn"
        >
          {exporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileSpreadsheet className="h-4 w-4" />}
          Экспорт в Excel
        </Button>
      </div>

      <div className="bg-card border border-border">
        <div className="flex flex-wrap items-center gap-3 p-4 border-b border-border">
          <div className="relative flex-1 min-w-[220px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              className="rounded-none pl-9"
              placeholder="Поиск по ФИО или номеру договора"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              data-testid="history-search"
            />
          </div>
          <Select value={batchFormat} onValueChange={setBatchFormat}>
            <SelectTrigger className="rounded-none w-[140px]" data-testid="history-batch-format">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="docx">Word (.docx)</SelectItem>
              <SelectItem value="pdf">PDF</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            className="rounded-none"
            onClick={handleBatch}
            disabled={selected.size === 0 || batching}
            data-testid="history-batch-download-btn"
          >
            {batching ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileArchive className="h-4 w-4" />}
            Скачать ZIP ({selected.size})
          </Button>
          <Button
            className="rounded-none bg-[#E11D48] hover:bg-[#BE123C] text-white"
            onClick={handleBatchPrint}
            disabled={selected.size === 0 || batchPrinting}
            data-testid="history-batch-print-btn"
          >
            {batchPrinting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Printer className="h-4 w-4" />}
            Печать выбранных ({selected.size})
          </Button>
          <Button
            variant="outline"
            className="rounded-none border-white/15"
            onClick={() => setDuplexOpen(true)}
            disabled={selected.size === 0}
            title="Двусторонняя печать вручную для принтера без дуплекса"
            data-testid="history-duplex-btn"
          >
            <Layers className="h-4 w-4" />
            Двусторонняя вручную ({selected.size})
          </Button>
          <Button
            variant="outline"
            className="rounded-none border-[#E11D48]/40 text-[#E11D48] hover:bg-[#E11D48]/10"
            onClick={handleBatchBlankPrint}
            disabled={selected.size === 0 || blankPrinting}
            title="Печать бланков «СООБЩЕНИЕ» 147×103 для выбранных договоров"
            data-testid="history-batch-blank-btn"
          >
            {blankPrinting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Stamp className="h-4 w-4" />}
            Печать бланков 147×103 ({selected.size})
          </Button>
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-10">
                <Checkbox checked={allSelected} onCheckedChange={toggleAll} data-testid="history-select-all" />
              </TableHead>
              <TableHead>№ договора</TableHead>
              <TableHead>ФИО</TableHead>
              <TableHead>Статус</TableHead>
              <TableHead>Дата создания</TableHead>
              <TableHead className="text-right">Действия</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-10 text-muted-foreground">
                  <Loader2 className="h-5 w-5 animate-spin inline" /> Загрузка…
                </TableCell>
              </TableRow>
            )}
            {!loading && contracts.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-10 text-muted-foreground">
                  Договоры не найдены
                </TableCell>
              </TableRow>
            )}
            {!loading &&
              contracts.map((c) => (
                <TableRow key={c.id} className="data-row" data-testid={`history-row-${c.id}`}>
                  <TableCell>
                    <Checkbox
                      checked={selected.has(c.id)}
                      onCheckedChange={() => toggle(c.id)}
                      data-testid={`history-select-${c.id}`}
                    />
                  </TableCell>
                  <TableCell className="font-medium">{c.contract_number || "—"}</TableCell>
                  <TableCell>{c.full_name || "—"}</TableCell>
                  <TableCell>
                    {c.status === "draft" ? (
                      <Badge className="rounded-full border-0 bg-amber-500/15 text-amber-400">
                        <FileClock className="h-3 w-3 mr-1" /> Черновик
                      </Badge>
                    ) : (
                      <Badge className="rounded-full border-0 bg-emerald-500/15 text-emerald-400">
                        Готов
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{fmtDate(c.created_at)}</TableCell>
                  <TableCell>
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="rounded-none"
                        onClick={() => setEditing(c)}
                        title="Редактировать"
                        data-testid={`edit-${c.id}`}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="rounded-none"
                        onClick={() => handleDownload(c, "docx")}
                        disabled={busyId === `${c.id}-docx`}
                        title="Word"
                        data-testid={`dl-docx-${c.id}`}
                      >
                        {busyId === `${c.id}-docx` ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="rounded-none"
                        onClick={() => handleDownload(c, "pdf")}
                        disabled={busyId === `${c.id}-pdf`}
                        title="PDF"
                        data-testid={`dl-pdf-${c.id}`}
                      >
                        {busyId === `${c.id}-pdf` ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileType className="h-4 w-4" />}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="rounded-none"
                        onClick={() => handlePreview(c)}
                        disabled={busyId === `${c.id}-preview`}
                        title="Просмотр"
                        data-testid={`preview-${c.id}`}
                      >
                        {busyId === `${c.id}-preview` ? <Loader2 className="h-4 w-4 animate-spin" /> : <Eye className="h-4 w-4" />}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="rounded-none"
                        onClick={() => handlePrint(c)}
                        disabled={busyId === `${c.id}-print`}
                        title="Печать"
                        data-testid={`print-${c.id}`}
                      >
                        {busyId === `${c.id}-print` ? <Loader2 className="h-4 w-4 animate-spin" /> : <Printer className="h-4 w-4" />}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="rounded-none text-[#E11D48] hover:text-[#E11D48] hover:bg-[#E11D48]/10"
                        onClick={() => openBlank(c, "/blank")}
                        title="Заполнить бланк «СООБЩЕНИЕ» данными договора"
                        data-testid={`toblank-${c.id}`}
                      >
                        <Stamp className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="rounded-none text-[#E11D48] hover:text-[#E11D48] hover:bg-[#E11D48]/10"
                        onClick={() => openBlank(c, "/full-print")}
                        title="Полная печать бланка с данными договора"
                        data-testid={`tofull-${c.id}`}
                      >
                        <FileText className="h-4 w-4" strokeWidth={2.4} />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="rounded-none text-[#FF3B30] hover:text-[#FF3B30] hover:bg-red-500/10"
                        onClick={() => setToDelete(c)}
                        title="Удалить"
                        data-testid={`delete-${c.id}`}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </div>

      <AlertDialog open={!!toDelete} onOpenChange={(v) => !v && setToDelete(null)}>
        <AlertDialogContent className="rounded-none">
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить договор?</AlertDialogTitle>
            <AlertDialogDescription>
              Договор {toDelete?.contract_number} ({toDelete?.full_name}) будет удалён из истории. Это действие нельзя отменить.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-none">Отмена</AlertDialogCancel>
            <AlertDialogAction
              className="rounded-none bg-[#FF3B30] hover:bg-red-700"
              onClick={handleDelete}
              data-testid="confirm-delete-btn"
            >
              Удалить
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <DocumentPreviewDialog
        open={!!previewUrl}
        url={previewUrl}
        title="Просмотр договора"
        onClose={() => {
          if (previewUrl) window.URL.revokeObjectURL(previewUrl);
          setPreviewUrl(null);
        }}
      />

      <DocumentEditor
        open={!!editing}
        initial={editing ? editing.fields : null}
        contractId={editing ? editing.id : null}
        initialStatus={editing ? editing.status || "final" : "final"}
        onClose={() => setEditing(null)}
        onSaved={() => load(search, statusFilter)}
      />

      <ManualDuplexDialog
        open={duplexOpen}
        ids={[...selected]}
        onClose={() => setDuplexOpen(false)}
      />
    </div>
  );
}
