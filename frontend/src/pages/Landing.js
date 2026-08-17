import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  MonitorDown,
  Download,
  ArrowRight,
  Printer,
  WifiOff,
  Check,
  FileSignature,
} from "lucide-react";
import { WINDOWS_DOWNLOAD_URL } from "@/lib/env";
import { getAppConfig } from "@/lib/apiClient";

export default function Landing() {
  const navigate = useNavigate();
  const [downloadUrl, setDownloadUrl] = useState(WINDOWS_DOWNLOAD_URL || "");

  useEffect(() => {
    getAppConfig()
      .then((c) => {
        if (c && c.windows_download_url) setDownloadUrl(c.windows_download_url);
      })
      .catch(() => {});
  }, []);

  const enter = () => {
    try {
      sessionStorage.setItem("bnk_entered", "1");
    } catch (e) {
      // ignore
    }
    navigate("/");
  };

  const download = () => {
    if (downloadUrl) {
      window.location.href = downloadUrl;
    } else {
      toast(
        "Прямая ссылка ещё не задана. Соберите .exe на GitHub (Actions → Build Windows Installer), затем вставьте ссылку в Настройках → «Установщик Windows»."
      );
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#0a0a12] text-white relative overflow-hidden">
      {/* ambient glow */}
      <div className="pointer-events-none absolute -top-40 -right-40 h-[520px] w-[520px] rounded-full bg-[#E11D48]/20 blur-[120px]" />
      <div className="pointer-events-none absolute -bottom-40 -left-40 h-[520px] w-[520px] rounded-full bg-[#7c1d3c]/20 blur-[120px]" />

      <div className="relative mx-auto max-w-3xl px-6 py-14 flex flex-col items-center">
        {/* brand */}
        <div className="flex items-center gap-3 mb-3">
          <div className="h-11 w-11 rounded-xl bg-[#E11D48] flex items-center justify-center shadow-lg shadow-[#E11D48]/30">
            <FileSignature className="h-6 w-6 text-white" />
          </div>
          <div className="leading-tight">
            <div className="font-heading text-2xl font-bold">Banetskaya.by</div>
            <div className="text-[11px] uppercase tracking-[0.2em] text-white/50">Document Engine</div>
          </div>
        </div>
        <h1 className="font-heading text-4xl md:text-5xl font-bold text-center mt-4">
          Автозаполнение и печать документов
        </h1>
        <p className="text-white/60 text-center mt-3 max-w-xl">
          Договоры найма и бланки из Excel — заполняются автоматически, печатаются ровно
          по строкам. Работайте в браузере или установите приложение для печати без лишних окон.
        </p>

        {/* TOP: Windows installer */}
        <div className="w-full mt-10 rounded-2xl border border-white/10 bg-white/[0.04] p-6 md:p-8 shadow-2xl"
             data-testid="landing-download-block">
          <div className="flex items-start gap-4">
            <div className="h-12 w-12 shrink-0 rounded-xl bg-[#1e293b] flex items-center justify-center">
              <MonitorDown className="h-7 w-7 text-[#38bdf8]" />
            </div>
            <div className="flex-1">
              <div className="text-xl font-semibold">Приложение для Windows</div>
              <p className="text-white/55 text-sm mt-1">
                Печать сразу на принтер — без выбора формата и лишних окон. Работает офлайн,
                LibreOffice уже встроен.
              </p>
              <div className="flex flex-wrap gap-x-5 gap-y-1.5 mt-3 text-sm text-white/70">
                <span className="inline-flex items-center gap-1.5"><Printer className="h-4 w-4 text-[#E11D48]" /> Печать в один клик</span>
                <span className="inline-flex items-center gap-1.5"><WifiOff className="h-4 w-4 text-[#E11D48]" /> Работает офлайн</span>
                <span className="inline-flex items-center gap-1.5"><Check className="h-4 w-4 text-[#E11D48]" /> Всё в одном установщике</span>
              </div>
              <Button
                onClick={download}
                className="mt-5 bg-[#38bdf8] hover:bg-[#0ea5e9] text-[#0a0a12] font-semibold"
                data-testid="btn-download-windows"
              >
                <Download className="h-4 w-4 mr-2" /> Скачать для Windows
              </Button>
            </div>
          </div>
        </div>

        {/* divider */}
        <div className="flex items-center gap-3 w-full my-8 text-white/30 text-sm">
          <div className="h-px flex-1 bg-white/10" />
          или
          <div className="h-px flex-1 bg-white/10" />
        </div>

        {/* BOTTOM: start in browser */}
        <div className="w-full rounded-2xl border border-[#E11D48]/30 bg-[#E11D48]/[0.06] p-6 md:p-8 flex flex-col md:flex-row md:items-center gap-4"
             data-testid="landing-start-block">
          <div className="flex-1">
            <div className="text-xl font-semibold">Начать работу в браузере</div>
            <p className="text-white/55 text-sm mt-1">
              Полный функционал без установки. Печать — через окно печати браузера.
            </p>
          </div>
          <Button
            onClick={enter}
            size="lg"
            className="bg-[#E11D48] hover:bg-[#BE123C] text-white font-semibold shrink-0"
            data-testid="btn-start-work"
          >
            Начать работу <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </div>

        <p className="text-white/30 text-xs mt-8 text-center">
          © Banetskaya.by · Автозаполнение договоров найма из Excel · для администратора
        </p>
      </div>
    </div>
  );
}
