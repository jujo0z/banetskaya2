import { useEffect, useState, useMemo } from "react";
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
import { Search, FileText, FileType, Printer, Trash2, FileArchive, Loader2, Eye } from "lucide-react";
import { toast } from "sonner";
import {
  listContracts,
  deleteContract,
  downloadSavedContract,
  batchDownload,
  batchPrint,
  savedPdfUrl,
  api,
} from "@/lib/apiClient";
import DocumentPreviewDialog from "@/components/DocumentPreviewDialog";

export default function History() {
  const [contracts, setContracts] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(new Set());
  const [batchFormat, setBatchFormat] = useState("docx");
  const [busyId, setBusyId] = useState("");
  const [batching, setBatching] = useState(false);
  const [batchPrinting, setBatchPrinting] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [toDelete, setToDelete] = useState(null);

  async function load(q = "") {
    setLoading(true);
    try {
      const data = await listContracts(q);
      setContracts(data);
    } catch (e) {
      toast.error("Не удалось загрузить историю");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    const t = setTimeout(() => load(search), 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line
  }, [search]);

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
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-10">
                <Checkbox checked={allSelected} onCheckedChange={toggleAll} data-testid="history-select-all" />
              </TableHead>
              <TableHead>№ договора</TableHead>
              <TableHead>ФИО</TableHead>
              <TableHead>Дата создания</TableHead>
              <TableHead className="text-right">Действия</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-10 text-muted-foreground">
                  <Loader2 className="h-5 w-5 animate-spin inline" /> Загрузка…
                </TableCell>
              </TableRow>
            )}
            {!loading && contracts.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-10 text-muted-foreground">
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
                  <TableCell className="text-muted-foreground">{fmtDate(c.created_at)}</TableCell>
                  <TableCell>
                    <div className="flex items-center justify-end gap-1">
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
    </div>
  );
}
