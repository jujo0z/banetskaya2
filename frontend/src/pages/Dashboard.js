import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  FileText, FileType, Upload, History as HistoryIcon, FileSpreadsheet,
  ArrowUpRight, Loader2, FileClock, Stamp, LayoutDashboard, FilePlus2,
} from "lucide-react";
import { toast } from "sonner";
import { getStats, downloadSavedContract } from "@/lib/apiClient";
import { PageHeader, StatTile, ActionTile } from "@/components/Page";

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [busyId, setBusyId] = useState("");

  useEffect(() => {
    getStats().then(setStats).catch(() => toast.error("Не удалось загрузить статистику"));
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
        day: "2-digit", month: "2-digit", year: "numeric",
        hour: "2-digit", minute: "2-digit",
      });
    } catch {
      return iso;
    }
  }

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Обзор"
        title="Дашборд"
        subtitle="Центр управления: статистика, быстрые действия и последние договоры."
        icon={LayoutDashboard}
        actions={
          <Button
            className="bg-[#EC4899] hover:bg-[#DB2777] text-white h-11 px-5"
            onClick={() => navigate("/generate")}
            data-testid="dashboard-new-contract-btn"
          >
            <Upload className="h-4 w-4 mr-2" />
            Загрузить Excel
          </Button>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatTile label="Всего договоров" value={stats ? stats.total : "—"} icon={FileText} />
        <StatTile label="За этот месяц" value={stats ? stats.this_month : "—"} icon={HistoryIcon} />
        <StatTile label="Черновики" value={stats ? stats.drafts : "—"} icon={FileClock} />
        <StatTile label="Загрузок Excel" value={stats ? stats.datasets : "—"} icon={FileSpreadsheet} />
      </div>

      {/* Quick actions */}
      <div>
        <div className="eyebrow mb-3">Быстрые действия</div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <ActionTile
            primary
            title="Новый договор"
            description="Загрузить Excel со студентами и сформировать договоры найма."
            icon={FilePlus2}
            onClick={() => navigate("/generate")}
            testid="action-generate"
          />
          <ActionTile
            title="Печать на бланке"
            description="Печать данных поверх готового бланка «СООБЩЕНИЕ» 147×103."
            icon={Stamp}
            onClick={() => navigate("/blank")}
            testid="action-blank"
          />
          <ActionTile
            title="Полная печать"
            description="Печать всего бланка «СООБЩЕНИЕ» на чистом белом листе."
            icon={FileText}
            onClick={() => navigate("/full-print")}
            testid="action-full"
          />
          <ActionTile
            title="История"
            description="Поиск, повторная печать и пакетная выгрузка договоров."
            icon={HistoryIcon}
            onClick={() => navigate("/history")}
            testid="action-history"
          />
        </div>
      </div>

      {/* Recent */}
      <div className="card-premium overflow-hidden">
        <div className="flex items-center justify-between p-5 border-b border-pink-100">
          <div className="flex items-center gap-3">
            <div className="chip-muted h-9 w-9 rounded-lg flex items-center justify-center">
              <FileClock className="h-4 w-4 text-[#F43F5E]" />
            </div>
            <h2 className="font-heading text-2xl font-bold tracking-tight leading-none">Последние договоры</h2>
          </div>
          <Button
            variant="ghost" size="sm"
            className="text-[#F43F5E] hover:text-[#F43F5E] hover:bg-[#EC4899]/10"
            onClick={() => navigate("/history")}
            data-testid="dashboard-open-history-btn"
          >
            Вся история <ArrowUpRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent border-pink-100">
              <TableHead>№ договора</TableHead>
              <TableHead>ФИО</TableHead>
              <TableHead>Дата создания</TableHead>
              <TableHead className="text-right">Скачать</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!stats && (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-12 text-muted-foreground">
                  <Loader2 className="h-5 w-5 animate-spin inline mr-2" /> Загрузка…
                </TableCell>
              </TableRow>
            )}
            {stats && stats.recent.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-12 text-muted-foreground">
                  Пока нет договоров. Начните с загрузки Excel.
                </TableCell>
              </TableRow>
            )}
            {stats && stats.recent.map((c) => (
              <TableRow key={c.id} className="data-row border-pink-100" data-testid={`dashboard-row-${c.id}`}>
                <TableCell className="font-medium">{c.contract_number || "—"}</TableCell>
                <TableCell>{c.full_name || "—"}</TableCell>
                <TableCell className="text-muted-foreground">{fmtDate(c.created_at)}</TableCell>
                <TableCell>
                  <div className="flex items-center justify-end gap-1">
                    <Button variant="ghost" size="icon" className="h-8 w-8 rounded-lg" title="Word"
                      onClick={() => dl(c, "docx")} disabled={busyId === `${c.id}-docx`} data-testid={`dash-dl-docx-${c.id}`}>
                      {busyId === `${c.id}-docx` ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
                    </Button>
                    <Button variant="ghost" size="icon" className="h-8 w-8 rounded-lg" title="PDF"
                      onClick={() => dl(c, "pdf")} disabled={busyId === `${c.id}-pdf`} data-testid={`dash-dl-pdf-${c.id}`}>
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
