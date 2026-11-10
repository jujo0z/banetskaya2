import { useEffect, useState, useMemo, useRef, useDeferredValue, memo } from "react";
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
import { Search, FileText, FileType, Printer, Trash2, FileArchive, Loader2, Eye, Pencil, FileClock, FileSpreadsheet, Layers, Stamp, ClipboardList, Database, Users, ArrowUp, ArrowDown, ArrowUpDown, AlertTriangle } from "lucide-react";
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
  exportBase,
  exportBaseSelected,
  api,
  contractToOverlay,
  openOverlayPdf,
  printOverlaySilent,
  openContractPackage,
  openContractsPackage,
} from "@/lib/apiClient";
import { IS_DESKTOP } from "@/lib/env";
import DocumentPreviewDialog from "@/components/DocumentPreviewDialog";
import DocumentEditor from "@/components/DocumentEditor";
import ManualDuplexDialog from "@/components/ManualDuplexDialog";
import { PageHeader } from "@/components/Page";

const PAGE = 100;

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

const HistoryRow = memo(function HistoryRow({ c, checked, dupName, dupNum, busy, pkgBusy, act }) {
  return (
    <TableRow
      key={c.id}
      className={`data-row ${(dupName || dupNum) ? "bg-amber-50/70 hover:bg-amber-50" : ""}`}
      data-testid={`history-row-${c.id}`}
    >
      <TableCell>
        <Checkbox
          checked={checked}
          onCheckedChange={() => act.toggle(c.id)}
          data-testid={`history-select-${c.id}`}
        />
      </TableCell>
      <TableCell className="font-medium">
        <span className={dupNum ? "inline-flex items-center gap-1 text-amber-700 font-semibold" : ""}>
          {dupNum && <AlertTriangle className="h-3.5 w-3.5" />}
          {c.contract_number || "—"}
        </span>
      </TableCell>
      <TableCell>
        <span className={dupName ? "inline-flex items-center gap-1 text-amber-700 font-semibold" : ""}>
          {dupName && <AlertTriangle className="h-3.5 w-3.5" />}
          {c.full_name || "—"}
        </span>
      </TableCell>
      <TableCell className="text-muted-foreground">{c.fields?.room_number || "—"}</TableCell>
      <TableCell className="text-muted-foreground">{c.fields?.phone || "—"}</TableCell>
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
            onClick={() => act.edit(c)}
            title="Редактировать"
            data-testid={`edit-${c.id}`}
          >
            <Pencil className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="rounded-none"
            onClick={() => act.download(c, "docx")}
            disabled={busy === `${c.id}-docx`}
            title="Word"
            data-testid={`dl-docx-${c.id}`}
          >
            {busy === `${c.id}-docx` ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="rounded-none"
            onClick={() => act.download(c, "pdf")}
            disabled={busy === `${c.id}-pdf`}
            title="PDF"
            data-testid={`dl-pdf-${c.id}`}
          >
            {busy === `${c.id}-pdf` ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileType className="h-4 w-4" />}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="rounded-none"
            onClick={() => act.preview(c)}
            disabled={busy === `${c.id}-preview`}
            title="Просмотр"
            data-testid={`preview-${c.id}`}
          >
            {busy === `${c.id}-preview` ? <Loader2 className="h-4 w-4 animate-spin" /> : <Eye className="h-4 w-4" />}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="rounded-none"
            onClick={() => act.print(c)}
            disabled={busy === `${c.id}-print`}
            title="Печать"
            data-testid={`print-${c.id}`}
          >
            {busy === `${c.id}-print` ? <Loader2 className="h-4 w-4 animate-spin" /> : <Printer className="h-4 w-4" />}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="rounded-none text-[#EC4899] hover:text-[#EC4899] hover:bg-[#EC4899]/10"
            onClick={() => act.pkg(c)}
            disabled={pkgBusy}
            title="Печать полного пакета (договор + Форма 19 + Форма 24 + Сообщение)"
            data-testid={`package-${c.id}`}
          >
            {pkgBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <ClipboardList className="h-4 w-4" />}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="rounded-none text-[#EC4899] hover:text-[#EC4899] hover:bg-[#EC4899]/10"
            onClick={() => act.blank(c, "/blank")}
            title="Заполнить бланк «СООБЩЕНИЕ» данными договора"
            data-testid={`toblank-${c.id}`}
          >
            <Stamp className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="rounded-none text-[#EC4899] hover:text-[#EC4899] hover:bg-[#EC4899]/10"
            onClick={() => act.blank(c, "/full-print")}
            title="Полная печать бланка с данными договора"
            data-testid={`tofull-${c.id}`}
          >
            <FileText className="h-4 w-4" strokeWidth={2.4} />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="rounded-none text-[#FF3B30] hover:text-[#FF3B30] hover:bg-red-500/10"
            onClick={() => act.del(c)}
            title="Удалить"
            data-testid={`delete-${c.id}`}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </TableCell>
    </TableRow>
  );
});

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
  const [packageBusyId, setPackageBusyId] = useState("");
  const [batchPackaging, setBatchPackaging] = useState(false);
  const [blankPrinting, setBlankPrinting] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [toDelete, setToDelete] = useState(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [editing, setEditing] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [exportingBase, setExportingBase] = useState(false);
  const [duplexOpen, setDuplexOpen] = useState(false);
  const [sort, setSort] = useState({ key: "created_at", dir: "desc" });

  function changeSort(key) {
    setSort((p) =>
      p.key === key
        ? { key, dir: p.dir === "asc" ? "desc" : "asc" }
        : { key, dir: key === "created_at" ? "desc" : "asc" }
    );
  }

  const deferredSearch = useDeferredValue(search);
  const [shown, setShown] = useState(PAGE);

  const filteredContracts = useMemo(() => {
    const q = deferredSearch.trim().toLowerCase();
    return contracts.filter((c) => {
      if (statusFilter === "draft" && c.status !== "draft") return false;
      if (statusFilter === "final" && c.status === "draft") return false;
      if (!q) return true;
      return (
        String(c.full_name || "").toLowerCase().includes(q) ||
        String(c.contract_number || "").toLowerCase().includes(q)
      );
    });
  }, [contracts, deferredSearch, statusFilter]);

  const sortedContracts = useMemo(() => {
    const arr = [...filteredContracts];
    const { key, dir } = sort;
    const mul = dir === "asc" ? 1 : -1;
    const numOf = (v) => {
      const n = parseInt(String(v ?? "").replace(/\D/g, ""), 10);
      return Number.isNaN(n) ? null : n;
    };
    arr.sort((a, b) => {
      if (key === "full_name") {
        return String(a.full_name || "").localeCompare(String(b.full_name || ""), "ru", { sensitivity: "base" }) * mul;
      }
      if (key === "contract_number" || key === "room_number") {
        const av = key === "room_number" ? a.fields?.room_number : a.contract_number;
        const bv = key === "room_number" ? b.fields?.room_number : b.contract_number;
        const na = numOf(av);
        const nb = numOf(bv);
        if (na !== null && nb !== null && na !== nb) return (na - nb) * mul;
        return String(av || "").localeCompare(String(bv || ""), "ru", { numeric: true }) * mul;
      }
      // created_at
      const ta = new Date(a.created_at).getTime() || 0;
      const tb = new Date(b.created_at).getTime() || 0;
      return (ta - tb) * mul;
    });
    return arr;
  }, [filteredContracts, sort]);

  const [exportingSelected, setExportingSelected] = useState(false);
  const [onlyDup, setOnlyDup] = useState(false);

  const { dupNames, dupNumbers } = useMemo(() => {
    const nameCount = {};
    const numCount = {};
    contracts.forEach((c) => {
      const nm = (c.full_name || "").trim().toLowerCase();
      const num = (c.contract_number || "").trim();
      if (nm) nameCount[nm] = (nameCount[nm] || 0) + 1;
      if (num) numCount[num] = (numCount[num] || 0) + 1;
    });
    return {
      dupNames: new Set(Object.keys(nameCount).filter((k) => nameCount[k] > 1)),
      dupNumbers: new Set(Object.keys(numCount).filter((k) => numCount[k] > 1)),
    };
  }, [contracts]);

  const isDupName = (c) => dupNames.has((c.full_name || "").trim().toLowerCase());
  const isDupNumber = (c) => dupNumbers.has((c.contract_number || "").trim());
  const isDup = (c) => isDupName(c) || isDupNumber(c);
  const dupCount = useMemo(
    () => contracts.filter((c) => isDup(c)).length,
    // eslint-disable-next-line
    [contracts, dupNames, dupNumbers]
  );

  const visibleContracts = useMemo(
    () => (onlyDup ? sortedContracts.filter((c) => isDup(c)) : sortedContracts),
    // eslint-disable-next-line
    [sortedContracts, onlyDup, dupNames, dupNumbers]
  );

  async function handleExportBaseSelected() {
    if (selected.size === 0) return;
    setExportingSelected(true);
    try {
      await exportBaseSelected([...selected]);
      toast.success(`Выгружено выбранных: ${selected.size}`);
    } catch (e) {
      toast.error("Не удалось выгрузить выбранные");
    } finally {
      setExportingSelected(false);
    }
  }

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

  async function handleExportBase() {
    setExportingBase(true);
    try {
      await exportBase(search, statusFilter);
      toast.success("База выгружена — файл можно снова загрузить в «Генерация из Excel»");
    } catch (e) {
      toast.error("Не удалось выгрузить базу");
    } finally {
      setExportingBase(false);
    }
  }

  async function load() {
    setLoading((v) => v || contracts.length === 0);
    try {
      const data = await listContracts();
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
    setShown(PAGE);
  }, [deferredSearch, statusFilter, onlyDup, sort]);

  function toggle(id) {
    setSelected((prev) => {
      const n = new Set(prev);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });
  }

  const allSelected = visibleContracts.length > 0 && visibleContracts.every((c) => selected.has(c.id));
  function toggleAll() {
    setSelected(allSelected ? new Set() : new Set(visibleContracts.map((c) => c.id)));
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
      load();
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

  // Полный пакет документов (договор + Форма 19 + Форма 24 + Сообщение)
  async function handlePackage(c) {
    setPackageBusyId(c.id);
    try {
      await openContractPackage(c.id, "long");
      toast.success("Пакет сформирован");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Не удалось сформировать пакет");
    } finally {
      setPackageBusyId("");
    }
  }

  async function handleBatchPackage() {
    if (selected.size === 0) return;
    setBatchPackaging(true);
    try {
      await openContractsPackage([...selected], "long");
      toast.success(`Пакет сформирован: ${selected.size}`);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Не удалось сформировать пакет");
    } finally {
      setBatchPackaging(false);
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

  // Send selected contracts to «Полная печать» (multiple messages per A4 sheet).
  function sendSelectedToFullPrint() {
    if (selected.size === 0) return;
    const prefillList = contracts
      .filter((c) => selected.has(c.id))
      .map((c) => contractToOverlay(c));
    if (prefillList.length === 0) return;
    navigate("/full-print", { state: { prefillList } });
  }


  const actRef = useRef(null);
  actRef.current = {
    edit: setEditing, download: handleDownload, preview: handlePreview, print: handlePrint,
    pkg: handlePackage, blank: openBlank, del: setToDelete, toggle,
  };
  const act = useMemo(() => {
    const call = (k) => (...a) => actRef.current[k](...a);
    return { edit: call("edit"), download: call("download"), preview: call("preview"), print: call("print"),
      pkg: call("pkg"), blank: call("blank"), del: call("del"), toggle: call("toggle") };
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Договоры найма"
        title="База проживающих"
        subtitle="Единая база всех проживающих: поиск, сортировка, редактирование, печать и выгрузка."
        icon={Users}
        actions={
          <div className="flex items-center gap-2 flex-wrap">
            <Button
              className="h-11 bg-[#EC4899] hover:bg-[#DB2777] text-white font-semibold"
              onClick={() => navigate("/data")}
              title="Открыть всю базу как Excel-таблицу и редактировать прямо здесь"
              data-testid="history-edit-data-btn"
            >
              <Pencil className="h-4 w-4" />
              Редактировать данные
            </Button>
            <Button
              className="h-11 bg-gradient-to-r from-rose-400 to-pink-500 hover:from-rose-500 hover:to-pink-600 text-white font-semibold"
              onClick={handleExportBase}
              disabled={exportingBase}
              title="Скачать всю текущую базу одним Excel в том же виде, как загружали (все поля). Такой файл можно снова загрузить в «Генерация из Excel»."
              data-testid="history-export-base-btn"
            >
              {exportingBase ? <Loader2 className="h-4 w-4 animate-spin" /> : <Database className="h-4 w-4" />}
              Скачать базу
            </Button>
            <Button
              variant="outline"
              className="h-11 border-pink-200"
              onClick={handleExport}
              disabled={exporting}
              data-testid="history-export-excel-btn"
            >
              {exporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileSpreadsheet className="h-4 w-4" />}
              Реестр в Excel
            </Button>
          </div>
        }
      />

      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-1 card-premium p-1 w-fit" data-testid="history-status-tabs">
          {[
            { k: "", label: "Все" },
            { k: "final", label: "Готовые" },
            { k: "draft", label: "Черновики" },
          ].map((t) => (
            <button
              key={t.k}
              onClick={() => setStatusFilter(t.k)}
              className={`px-4 py-1.5 text-sm rounded-lg transition-colors ${
                statusFilter === t.k
                  ? "bg-[#EC4899] text-white"
                  : "text-muted-foreground hover:text-slate-900"
              }`}
              data-testid={`history-filter-${t.k || "all"}`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          {dupCount > 0 && (
            <button
              onClick={() => setOnlyDup((v) => !v)}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                onlyDup
                  ? "bg-amber-500 text-white border-amber-500"
                  : "bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100"
              }`}
              title="Показать только записи с повторяющимися ФИО или номером договора"
              data-testid="history-dup-toggle"
            >
              <AlertTriangle className="h-4 w-4" />
              {onlyDup ? "Показать все" : `Дубликаты: ${dupCount}`}
            </button>
          )}
          <div className="flex items-center gap-2 text-sm text-muted-foreground" data-testid="history-total">
            <Users className="h-4 w-4 text-[#EC4899]" />
            {onlyDup ? "Дубликатов" : "Всего проживающих"}: <span className="font-semibold text-slate-900">{loading ? "…" : visibleContracts.length}</span>
          </div>
        </div>
      </div>

      <div className="card-premium overflow-hidden">
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
            className="rounded-none bg-gradient-to-r from-rose-400 to-pink-500 hover:from-rose-500 hover:to-pink-600 text-white"
            onClick={handleExportBaseSelected}
            disabled={selected.size === 0 || exportingSelected}
            title="Выгрузить выбранных в Excel (формат «Данные» — такой файл можно снова загрузить в «Генерация из Excel»)"
            data-testid="history-export-selected-btn"
          >
            {exportingSelected ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileSpreadsheet className="h-4 w-4" />}
            Выбранные в Excel ({selected.size})
          </Button>
          <Button
            className="rounded-none bg-[#EC4899] hover:bg-[#DB2777] text-white"
            onClick={handleBatchPrint}
            disabled={selected.size === 0 || batchPrinting}
            data-testid="history-batch-print-btn"
          >
            {batchPrinting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Printer className="h-4 w-4" />}
            Печать выбранных ({selected.size})
          </Button>
          <Button
            className="rounded-none bg-[#EC4899] hover:bg-[#DB2777] text-white"
            onClick={handleBatchPackage}
            disabled={selected.size === 0 || batchPackaging}
            title="Полный пакет (договор + Форма 19 + Форма 24 + Сообщение) для выбранных"
            data-testid="history-batch-package-btn"
          >
            {batchPackaging ? <Loader2 className="h-4 w-4 animate-spin" /> : <ClipboardList className="h-4 w-4" />}
            Печать пакета ({selected.size})
          </Button>
          <Button
            variant="outline"
            className="rounded-none border-pink-200"
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
            className="rounded-none border-[#EC4899]/40 text-[#EC4899] hover:bg-[#EC4899]/10"
            onClick={handleBatchBlankPrint}
            disabled={selected.size === 0 || blankPrinting}
            title="Печать бланков «СООБЩЕНИЕ» 147×103 для выбранных договоров"
            data-testid="history-batch-blank-btn"
          >
            {blankPrinting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Stamp className="h-4 w-4" />}
            Печать бланков 147×103 ({selected.size})
          </Button>
          <Button
            variant="outline"
            className="rounded-none border-pink-200"
            onClick={sendSelectedToFullPrint}
            disabled={selected.size === 0}
            title="Собрать выбранные договоры на листах A4 (несколько сообщений на лист)"
            data-testid="history-fullprint-btn"
          >
            <FileText className="h-4 w-4" />
            На листы A4 ({selected.size})
          </Button>
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-10">
                <Checkbox checked={allSelected} onCheckedChange={toggleAll} data-testid="history-select-all" />
              </TableHead>
              <TableHead>
                <button
                  className="inline-flex items-center gap-1 hover:text-slate-900 transition-colors"
                  onClick={() => changeSort("contract_number")}
                  data-testid="sort-contract_number"
                >
                  № договора
                  {sort.key === "contract_number"
                    ? (sort.dir === "asc" ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />)
                    : <ArrowUpDown className="h-3 w-3 opacity-40" />}
                </button>
              </TableHead>
              <TableHead>
                <button
                  className="inline-flex items-center gap-1 hover:text-slate-900 transition-colors"
                  onClick={() => changeSort("full_name")}
                  data-testid="sort-full_name"
                >
                  ФИО (А→Я)
                  {sort.key === "full_name"
                    ? (sort.dir === "asc" ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />)
                    : <ArrowUpDown className="h-3 w-3 opacity-40" />}
                </button>
              </TableHead>
              <TableHead>
                <button
                  className="inline-flex items-center gap-1 hover:text-slate-900 transition-colors"
                  onClick={() => changeSort("room_number")}
                  data-testid="sort-room_number"
                >
                  Комната
                  {sort.key === "room_number"
                    ? (sort.dir === "asc" ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />)
                    : <ArrowUpDown className="h-3 w-3 opacity-40" />}
                </button>
              </TableHead>
              <TableHead>Телефон</TableHead>
              <TableHead>Статус</TableHead>
              <TableHead>
                <button
                  className="inline-flex items-center gap-1 hover:text-slate-900 transition-colors"
                  onClick={() => changeSort("created_at")}
                  data-testid="sort-created_at"
                >
                  Дата создания
                  {sort.key === "created_at"
                    ? (sort.dir === "asc" ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />)
                    : <ArrowUpDown className="h-3 w-3 opacity-40" />}
                </button>
              </TableHead>
              <TableHead className="text-right">Действия</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && (
              <TableRow>
                <TableCell colSpan={8} className="text-center py-10 text-muted-foreground">
                  <Loader2 className="h-5 w-5 animate-spin inline" /> Загрузка…
                </TableCell>
              </TableRow>
            )}
            {!loading && visibleContracts.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} className="text-center py-12 text-muted-foreground">
                  <Users className="h-8 w-8 mx-auto mb-2 opacity-30" />
                  {onlyDup
                    ? "Дубликаты не найдены — повторяющихся записей нет"
                    : search || statusFilter
                    ? "По вашему запросу никого не найдено"
                    : "В базе пока нет проживающих — добавьте их через «Генерация из Excel»"}
                </TableCell>
              </TableRow>
            )}
            {!loading &&
              visibleContracts.slice(0, shown).map((c) => (
                <HistoryRow
                  key={c.id}
                  c={c}
                  checked={selected.has(c.id)}
                  dupName={isDupName(c)}
                  dupNum={isDupNumber(c)}
                  busy={busyId.startsWith(`${c.id}-`) ? busyId : ""}
                  pkgBusy={packageBusyId === c.id}
                  act={act}
                />
              ))}
          </TableBody>
        </Table>
        {!loading && visibleContracts.length > shown && (
          <div className="flex items-center justify-center gap-3 p-4 border-t border-border text-sm text-muted-foreground" data-testid="history-pager">
            Показано {shown} из {visibleContracts.length}
            <Button variant="outline" className="rounded-none" onClick={() => setShown((n) => n + PAGE)} data-testid="history-show-more">
              Показать ещё {Math.min(PAGE, visibleContracts.length - shown)}
            </Button>
            <Button variant="ghost" className="rounded-none" onClick={() => setShown(visibleContracts.length)} data-testid="history-show-all">
              Показать всех
            </Button>
          </div>
        )}
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
        onSaved={() => load()}
      />

      <ManualDuplexDialog
        open={duplexOpen}
        ids={[...selected]}
        onClose={() => setDuplexOpen(false)}
      />
    </div>
  );
}
