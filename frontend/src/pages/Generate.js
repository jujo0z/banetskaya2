import { useState, useMemo, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
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
  Upload,
  Search,
  Settings2,
  Pencil,
  FileArchive,
  Loader2,
  FileSpreadsheet,
  Download,
  Printer,
  Layers,
  History,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { FIELDS, mapRowsToStudents } from "@/lib/fields";
import { generateUpload, saveContractsBatch, batchDownload, batchPrint, downloadMasterTemplate } from "@/lib/apiClient";
import EditContractDialog from "@/components/DocumentEditor";
import ManualDuplexDialog from "@/components/ManualDuplexDialog";
import { PageHeader } from "@/components/Page";

const NONE = "__none__";

export default function Generate() {
  const [dataset, setDataset] = useState(null);
  const [mapping, setMapping] = useState({});
  const [mode, setMode] = useState("contract");
  const [masterStudents, setMasterStudents] = useState([]);
  const [masters, setMasters] = useState([]);
  const [fileInfo, setFileInfo] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [showMapping, setShowMapping] = useState(false);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState(new Set());
  const [editIndex, setEditIndex] = useState(null);
  const [batchFormat, setBatchFormat] = useState("docx");
  const [batching, setBatching] = useState(false);
  const [batchPrinting, setBatchPrinting] = useState(false);
  const [duplexOpen, setDuplexOpen] = useState(false);
  const [duplexIds, setDuplexIds] = useState([]);
  const [preparingDuplex, setPreparingDuplex] = useState(false);
  const [savingAll, setSavingAll] = useState(false);
  const fileRef = useRef();
  const navigate = useNavigate();

  const students = useMemo(
    () =>
      mode === "master"
        ? masterStudents
        : dataset
        ? mapRowsToStudents(dataset.rows, mapping)
        : [],
    [mode, masterStudents, dataset, mapping]
  );

  const loaded = !!fileInfo;

  const filtered = useMemo(() => {
    if (!search.trim()) return students.map((s, i) => ({ s, i }));
    const q = search.toLowerCase();
    return students
      .map((s, i) => ({ s, i }))
      .filter(({ s }) =>
        [s.full_name, s.contract_number, s.room_number]
          .filter(Boolean)
          .some((v) => String(v).toLowerCase().includes(q))
      );
  }, [students, search]);

  async function handleFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const data = await generateUpload(file);
      setSelected(new Set());
      setFileInfo({ filename: file.name, count: data.count });
      if (data.mode === "master") {
        setMode("master");
        setMasterStudents(data.students || []);
        setMasters(data.masters || []);
        setDataset(null);
        setMapping({});
        setShowMapping(false);
        toast.success(`Загружено (единый шаблон): ${data.count}`);
      } else {
        setMode("contract");
        setDataset({ filename: file.name, columns: data.columns, rows: data.rows, mapping: data.mapping });
        setMapping(data.mapping || {});
        setMasterStudents([]);
        setMasters([]);
        toast.success(`Загружено: ${data.count}`);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || "Ошибка загрузки файла");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  function toggle(i) {
    setSelected((prev) => {
      const n = new Set(prev);
      n.has(i) ? n.delete(i) : n.add(i);
      return n;
    });
  }

  function toggleAll() {
    const allIdx = filtered.map(({ i }) => i);
    const allSelected = allIdx.every((i) => selected.has(i));
    setSelected((prev) => {
      const n = new Set(prev);
      allIdx.forEach((i) => (allSelected ? n.delete(i) : n.add(i)));
      return n;
    });
  }

  async function handleBatch() {
    const idxs = [...selected];
    const items = idxs.map((i) => students[i]);
    const ms = idxs.map((i) => masters[i] || {});
    if (items.length === 0) return;
    setBatching(true);
    try {
      const res = await saveContractsBatch(items, ms);
      const ids = res.created.map((c) => c.id);
      toast.success(`Сформировано договоров: ${res.count}. Загрузка архива…`);
      await batchDownload(ids, batchFormat);
    } catch (err) {
      toast.error("Ошибка пакетного формирования");
    } finally {
      setBatching(false);
    }
  }

  async function handleBatchPrint() {
    const idxs = [...selected];
    const items = idxs.map((i) => students[i]);
    const ms = idxs.map((i) => masters[i] || {});
    if (items.length === 0) return;
    setBatchPrinting(true);
    try {
      const res = await saveContractsBatch(items, ms);
      const ids = res.created.map((c) => c.id);
      await batchPrint(ids);
      toast.success(`Открыто на печать: ${res.count}`);
    } catch (err) {
      toast.error("Не удалось открыть на печать");
    } finally {
      setBatchPrinting(false);
    }
  }

  // «Сформировать всё → в историю»: массово сохранить выделенные (или все, если
  // ничего не отмечено) договоры в Историю, без скачивания архива.
  async function handleGenerateAllToHistory() {
    let idxs = [...selected];
    const usingAll = idxs.length === 0;
    if (usingAll) idxs = students.map((_, i) => i);
    const items = idxs.map((i) => students[i]);
    const ms = idxs.map((i) => masters[i] || {});
    if (items.length === 0) return;
    setSavingAll(true);
    try {
      const res = await saveContractsBatch(items, ms);
      setSelected(new Set());
      toast.success(
        `Сформировано и записано в историю: ${res.count}${usingAll ? " (все записи)" : ""}.`,
        {
          action: {
            label: "Открыть историю",
            onClick: () => navigate("/history"),
          },
          duration: 6000,
        }
      );
    } catch (err) {
      toast.error("Ошибка формирования в историю");
    } finally {
      setSavingAll(false);
    }
  }

  async function handleManualDuplex() {
    const idxs = [...selected];
    const items = idxs.map((i) => students[i]);
    const ms = idxs.map((i) => masters[i] || {});
    if (items.length === 0) return;
    setPreparingDuplex(true);
    try {
      const res = await saveContractsBatch(items, ms);
      setDuplexIds(res.created.map((c) => c.id));
      setDuplexOpen(true);
    } catch (err) {
      toast.error("Не удалось подготовить документы");
    } finally {
      setPreparingDuplex(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Договоры найма"
        title="Генерация из Excel"
        subtitle="Загрузите Excel-таблицу студентов, выберите нужных и сформируйте договоры найма."
        icon={FileSpreadsheet}
      />

      {/* Upload */}
      <div className="card-premium p-6">
        <input
          ref={fileRef}
          type="file"
          accept=".xlsx,.xlsm"
          className="hidden"
          onChange={handleFile}
          data-testid="excel-file-input"
        />
        <div className="flex flex-wrap items-center gap-4">
          <Button
            className="rounded-none bg-[#EC4899] hover:bg-[#DB2777] text-white h-11"
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            data-testid="upload-excel-btn"
          >
            {uploading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Upload className="h-4 w-4" />
            )}
            Загрузить Excel (.xlsx)
          </Button>
          <Button
            variant="outline"
            className="rounded-none h-11"
            onClick={() => downloadMasterTemplate()}
            data-testid="download-sample-btn"
          >
            <Download className="h-4 w-4" />
            Скачать единый шаблон
          </Button>
          {fileInfo && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <FileSpreadsheet className="h-4 w-4" />
              <span className="font-medium text-foreground">{fileInfo.filename}</span>
              <span>· записей: {fileInfo.count}</span>
              {mode === "master" && (
                <span className="px-2 py-0.5 rounded bg-[#EC4899]/15 text-[#EC4899] text-[11px]">
                  единый шаблон
                </span>
              )}
            </div>
          )}
          {dataset && mode === "contract" && (
            <Button
              variant="outline"
              className="rounded-none ml-auto"
              onClick={() => setShowMapping((v) => !v)}
              data-testid="toggle-mapping-btn"
            >
              <Settings2 className="h-4 w-4" />
              Сопоставление колонок
            </Button>
          )}
        </div>

        {/* Column mapping editor */}
        {dataset && mode === "contract" && showMapping && (
          <div className="mt-6 border-t border-border pt-6">
            <p className="text-xs uppercase tracking-[0.2em] font-semibold text-muted-foreground mb-4">
              Сопоставьте поля договора с колонками таблицы
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {FIELDS.map((f) => (
                <div key={f.key} className="space-y-1.5">
                  <Label className="text-xs text-muted-foreground">{f.label}</Label>
                  <Select
                    value={mapping[f.key] || NONE}
                    onValueChange={(v) =>
                      setMapping((prev) => ({ ...prev, [f.key]: v === NONE ? "" : v }))
                    }
                  >
                    <SelectTrigger className="rounded-none h-9" data-testid={`map-${f.key}`}>
                      <SelectValue placeholder="— не выбрано —" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={NONE}>— не выбрано —</SelectItem>
                      {dataset.columns.map((c) => (
                        <SelectItem key={c} value={c}>
                          {c}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Students */}
      {loaded && (
        <div className="card-premium overflow-hidden">
          <div className="flex flex-wrap items-center gap-3 p-4 border-b border-border">
            <div className="relative flex-1 min-w-[220px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                className="rounded-none pl-9"
                placeholder="Поиск по ФИО, номеру договора, комнате"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                data-testid="student-search"
              />
            </div>
            <Select value={batchFormat} onValueChange={setBatchFormat}>
              <SelectTrigger className="rounded-none w-[140px]" data-testid="batch-format-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="docx">Word (.docx)</SelectItem>
                <SelectItem value="pdf">PDF</SelectItem>
              </SelectContent>
            </Select>
            <Button
              className="rounded-none bg-[#EC4899] hover:bg-[#DB2777] text-white"
              onClick={handleGenerateAllToHistory}
              disabled={savingAll || students.length === 0}
              title="Сформировать выделенные договоры (или все, если ничего не отмечено) и записать в Историю"
              data-testid="generate-all-history-btn"
            >
              {savingAll ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <History className="h-4 w-4" />
              )}
              Сформировать всё → в историю ({selected.size || students.length})
            </Button>
            <Button
              variant="outline"
              className="rounded-none bg-[#EC4899]/10 border-[#EC4899]/40 hover:bg-[#EC4899]/20 text-foreground"
              onClick={handleBatch}
              disabled={selected.size === 0 || batching}
              title="Сформировать выбранные и скачать архив (docx/pdf). Также пишутся в историю."
              data-testid="batch-generate-btn"
            >
              {batching ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <FileArchive className="h-4 w-4" />
              )}
              Скачать архив выбранных ({selected.size})
            </Button>
            <Button
              variant="outline"
              className="rounded-none"
              onClick={handleBatchPrint}
              disabled={selected.size === 0 || batchPrinting}
              data-testid="batch-print-btn"
            >
              {batchPrinting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Printer className="h-4 w-4" />
              )}
              Печать выбранных ({selected.size})
            </Button>
            <Button
              variant="outline"
              className="rounded-none"
              onClick={handleManualDuplex}
              disabled={selected.size === 0 || preparingDuplex}
              title="Двусторонняя печать вручную для принтера без дуплекса"
              data-testid="duplex-print-btn"
            >
              {preparingDuplex ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Layers className="h-4 w-4" />
              )}
              Двусторонняя вручную ({selected.size})
            </Button>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10">
                  <Checkbox
                    checked={filtered.length > 0 && filtered.every(({ i }) => selected.has(i))}
                    onCheckedChange={toggleAll}
                    data-testid="select-all-checkbox"
                  />
                </TableHead>
                <TableHead>ФИО</TableHead>
                <TableHead>№ договора</TableHead>
                <TableHead>Комната</TableHead>
                <TableHead>Срок до</TableHead>
                <TableHead className="text-right">Действие</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted-foreground py-10">
                    Нет данных
                  </TableCell>
                </TableRow>
              )}
              {filtered.map(({ s, i }) => (
                <TableRow key={i} className="data-row" data-testid={`student-row-${i}`}>
                  <TableCell>
                    <Checkbox
                      checked={selected.has(i)}
                      onCheckedChange={() => toggle(i)}
                      data-testid={`select-student-${i}`}
                    />
                  </TableCell>
                  <TableCell className="font-medium">{s.full_name || "—"}</TableCell>
                  <TableCell>{s.contract_number || "—"}</TableCell>
                  <TableCell>{s.room_number || "—"}</TableCell>
                  <TableCell>{s.contract_end_date || "—"}</TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="outline"
                      size="sm"
                      className="rounded-none"
                      onClick={() => setEditIndex(i)}
                      data-testid={`edit-student-${i}`}
                    >
                      <Pencil className="h-3.5 w-3.5" />
                      Сформировать
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <EditContractDialog
        open={editIndex !== null}
        initial={editIndex !== null ? students[editIndex] : null}
        onClose={() => setEditIndex(null)}
      />

      <ManualDuplexDialog
        open={duplexOpen}
        ids={duplexIds}
        onClose={() => setDuplexOpen(false)}
      />
    </div>
  );
}
