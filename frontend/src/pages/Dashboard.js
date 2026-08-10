import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  FileText,
  FileType,
  Upload,
  History as HistoryIcon,
  FileSpreadsheet,
  ArrowUpRight,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
import { getStats, downloadSavedContract } from "@/lib/apiClient";

function StatCard({ label, value, icon: Icon, testid }) {
  return (
    <div className="bg-white border border-border p-6" data-testid={testid}>
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs uppercase tracking-[0.2em] font-semibold text-muted-foreground">
            {label}
          </div>
          <div className="font-heading text-4xl font-black tracking-tighter mt-3">{value}</div>
        </div>
        <div className="h-10 w-10 bg-[#F0F4FF] flex items-center justify-center">
          <Icon className="h-5 w-5 text-[#002FA7]" strokeWidth={2} />
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [busyId, setBusyId] = useState("");

  useEffect(() => {
    getStats()
      .then(setStats)
      .catch(() => toast.error("Не удалось загрузить статистику"));
  }, []);

  async function dl(c, format) {
    setBusyId(`${c.id}-${format}`);
    try {
      await downloadSavedContract(c.id, format, `Договор.${format}`);
    } catch {
      toast.error("Ошибка при формировании документа");
    } finally {
      setBusyId("");
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
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-heading text-4xl sm:text-5xl font-black tracking-tighter">Дашборд</h1>
          <p className="text-muted-foreground mt-2">
            Обзор работы: сформированные договоры и быстрые действия.
          </p>
        </div>
        <Button
          className="rounded-none bg-[#002FA7] hover:bg-[#00207A] text-white h-11"
          onClick={() => navigate("/generate")}
          data-testid="dashboard-new-contract-btn"
        >
          <Upload className="h-4 w-4" />
          Загрузить Excel и сформировать
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          label="Всего договоров"
          value={stats ? stats.total : "—"}
          icon={FileText}
          testid="stat-total"
        />
        <StatCard
          label="За этот месяц"
          value={stats ? stats.this_month : "—"}
          icon={HistoryIcon}
          testid="stat-month"
        />
        <StatCard
          label="Загрузок Excel"
          value={stats ? stats.datasets : "—"}
          icon={FileSpreadsheet}
          testid="stat-datasets"
        />
      </div>

      <div className="bg-white border border-border">
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h2 className="font-heading text-xl font-bold tracking-tight">Последние договоры</h2>
          <Button
            variant="ghost"
            size="sm"
            className="rounded-none text-[#002FA7]"
            onClick={() => navigate("/history")}
            data-testid="dashboard-open-history-btn"
          >
            Вся история
            <ArrowUpRight className="h-4 w-4" />
          </Button>
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>№ договора</TableHead>
              <TableHead>ФИО</TableHead>
              <TableHead>Дата создания</TableHead>
              <TableHead className="text-right">Скачать</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!stats && (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-10 text-muted-foreground">
                  <Loader2 className="h-5 w-5 animate-spin inline" /> Загрузка…
                </TableCell>
              </TableRow>
            )}
            {stats && stats.recent.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-10 text-muted-foreground">
                  Пока нет договоров. Начните с загрузки Excel.
                </TableCell>
              </TableRow>
            )}
            {stats &&
              stats.recent.map((c) => (
                <TableRow key={c.id} className="data-row" data-testid={`dashboard-row-${c.id}`}>
                  <TableCell className="font-medium">{c.contract_number || "—"}</TableCell>
                  <TableCell>{c.full_name || "—"}</TableCell>
                  <TableCell className="text-muted-foreground">{fmtDate(c.created_at)}</TableCell>
                  <TableCell>
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="rounded-none"
                        title="Word"
                        onClick={() => dl(c, "docx")}
                        disabled={busyId === `${c.id}-docx`}
                        data-testid={`dash-dl-docx-${c.id}`}
                      >
                        {busyId === `${c.id}-docx` ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="rounded-none"
                        title="PDF"
                        onClick={() => dl(c, "pdf")}
                        disabled={busyId === `${c.id}-pdf`}
                        data-testid={`dash-dl-pdf-${c.id}`}
                      >
                        {busyId === `${c.id}-pdf` ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileType className="h-4 w-4" />}
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
