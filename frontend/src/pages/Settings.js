import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Download, FileCheck2, Info, Database, Trash2, Bookmark, Loader2, RotateCcw, FileUp, FileText, Check, MonitorDown, Save, Building2, RefreshCw, DownloadCloud, Settings2 } from "lucide-react";
import { toast } from "sonner";
import { FIELDS } from "@/lib/fields";
import {
  downloadSampleTemplate, seedDemo, clearDemo, getPresets, deletePreset,
  listTemplates, uploadTemplate, activateTemplate, deleteTemplateById,
  getAppConfig, saveAppConfig, getRegProfile, saveRegProfile,
  getAppVersion, checkUpdates, applyUpdate,
  getCountersBase, saveCountersBase, recomputeCounters,
} from "@/lib/apiClient";
import { IS_DESKTOP } from "@/lib/env";
import { PageHeader } from "@/components/Page";

export default function Settings() {
  const [downloading, setDownloading] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [presets, setPresets] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [tplBusy, setTplBusy] = useState(false);
  const [winUrl, setWinUrl] = useState("");
  const [savingWin, setSavingWin] = useState(false);
  const [profile, setProfile] = useState({ reg_organ: "", chief: "", city: "" });
  const [savingProfile, setSavingProfile] = useState(false);
  const [appVer, setAppVer] = useState(null);
  const [updInfo, setUpdInfo] = useState(null);
  const [checking, setChecking] = useState(false);
  const [applying, setApplying] = useState(false);
  const [cbase, setCbase] = useState({ enabled: false, total: 0, minors: 0, adults: 0, free: 0 });
  const [savingCounters, setSavingCounters] = useState(false);
  const [recomputing, setRecomputing] = useState(false);
  const [counterMsg, setCounterMsg] = useState(null);

  useEffect(() => {
    getPresets().then(setPresets).catch(() => {});
    loadTemplates();
    getCountersBase().then(setCbase).catch(() => {});
    getAppConfig().then((c) => setWinUrl(c?.windows_download_url || "")).catch(() => {});
    getRegProfile().then((p) => setProfile({
      reg_organ: p?.reg_organ || "", chief: p?.chief || "", city: p?.city || "",
    })).catch(() => {});
    if (IS_DESKTOP) {
      getAppVersion().then(setAppVer).catch(() => {});
    }
  }, []);

  async function handleCheckUpdates() {
    setChecking(true);
    try {
      const info = await checkUpdates();
      setUpdInfo(info);
      if (info?.error) toast.error(info.error);
      else if (info?.update_available) toast.success(`Доступно обновление: ${info.latest_version || ""}`);
      else toast.success("У вас установлена последняя версия");
    } catch {
      toast.error("Не удалось проверить обновления");
    } finally {
      setChecking(false);
    }
  }

  async function handleApplyUpdate() {
    setApplying(true);
    try {
      await applyUpdate(updInfo?.download_url || "");
      toast.success("Загружаю обновление и запускаю установщик — приложение закроется");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Не удалось обновить приложение");
      setApplying(false);
    }
  }

  async function handleSaveCounters() {
    setSavingCounters(true);
    try {
      const r = await saveCountersBase({
        enabled: !!cbase.enabled,
        total: Number(cbase.total) || 0,
        minors: Number(cbase.minors) || 0,
        adults: Number(cbase.adults) || 0,
        free: Number(cbase.free) || 0,
      }, true);
      const rc = r?.recompute;
      if (rc && rc.ok === false) {
        setCounterMsg(rc.reason === "not_all_numbered"
          ? `Не запущено: у ${rc.missing_count} договоров нет номера — например: ${(rc.missing || []).slice(0, 5).join(", ")}. Пронумеруйте все и нажмите «Досчитать новые».`
          : (rc.detail || "Пересчёт не выполнен"));
        toast.warning("Сохранено, но пересчёт не выполнен");
      } else if (rc && rc.ok) {
        setCounterMsg(`Готово: пересчитано ${rc.computed} из ${rc.total} договоров.`);
        toast.success("Стартовые значения сохранены, счётчики пересчитаны");
      } else {
        setCounterMsg(cbase.enabled ? null : "Автоподсчёт выключен.");
        toast.success("Сохранено");
      }
    } catch {
      toast.error("Не удалось сохранить");
    } finally {
      setSavingCounters(false);
    }
  }

  async function handleRecompute() {
    setRecomputing(true);
    try {
      const r = await recomputeCounters(false);
      if (r && r.ok === false) {
        setCounterMsg(r.reason === "not_all_numbered"
          ? `Пока не у всех договоров есть номер (${r.missing_count}) — например: ${(r.missing || []).slice(0, 5).join(", ")}.`
          : (r.detail || "Пересчёт не выполнен"));
        toast.warning(r.detail || "Пересчёт не выполнен");
      } else {
        setCounterMsg(`Досчитано новых: ${r.computed} (всего ${r.total}).`);
        toast.success("Счётчики обновлены");
      }
    } catch {
      toast.error("Ошибка пересчёта");
    } finally {
      setRecomputing(false);
    }
  }

  async function handleSaveProfile() {
    setSavingProfile(true);
    try {
      await saveRegProfile(profile);
      toast.success("Профиль органа сохранён — подставится в бланк автоматически");
    } catch {
      toast.error("Не удалось сохранить профиль");
    } finally {
      setSavingProfile(false);
    }
  }

  async function handleSaveWin() {
    setSavingWin(true);
    try {
      await saveAppConfig(winUrl.trim());
      toast.success("Ссылка на установщик сохранена");
    } catch {
      toast.error("Не удалось сохранить ссылку");
    } finally {
      setSavingWin(false);
    }
  }

  function loadTemplates() {
    listTemplates().then(setTemplates).catch(() => {});
  }

  async function handleTemplateUpload(e) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".docx")) {
      toast.error("Нужен файл .docx");
      return;
    }
    setTplBusy(true);
    try {
      await uploadTemplate(file);
      toast.success("Шаблон загружен");
      loadTemplates();
    } catch {
      toast.error("Не удалось загрузить шаблон");
    } finally {
      setTplBusy(false);
    }
  }

  async function handleActivate(id) {
    try {
      await activateTemplate(id);
      toast.success("Шаблон выбран для генерации");
      loadTemplates();
    } catch {
      toast.error("Не удалось выбрать шаблон");
    }
  }

  async function handleDeleteTemplate(id) {
    try {
      await deleteTemplateById(id);
      loadTemplates();
    } catch {
      toast.error("Не удалось удалить шаблон");
    }
  }

  async function handleSeed() {
    setSeeding(true);
    try {
      const res = await seedDemo();
      toast.success(res.message || "Демо-данные загружены");
    } catch {
      toast.error("Не удалось загрузить демо-данные");
    } finally {
      setSeeding(false);
    }
  }

  async function handleClearDemo() {
    setClearing(true);
    try {
      const res = await clearDemo();
      toast.success(`Удалено демо-договоров: ${res.deleted}`);
    } catch {
      toast.error("Не удалось очистить демо-данные");
    } finally {
      setClearing(false);
    }
  }

  async function handleDeletePreset(id) {
    try {
      await deletePreset(id);
      setPresets((prev) => prev.filter((p) => p.id !== id));
      toast.success("Пресет удалён");
    } catch {
      toast.error("Не удалось удалить пресет");
    }
  }

  async function handleSample() {
    setDownloading(true);
    try {
      await downloadSampleTemplate();
      toast.success("Шаблон Excel скачан");
    } catch {
      toast.error("Не удалось скачать шаблон");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Система"
        title="Настройки"
        subtitle="Профиль органа, обновления, шаблон договора, поля автозаполнения и образец Excel."
        icon={Settings2}
      />

      {/* App updates (desktop app only) */}
      {IS_DESKTOP && (
        <div className="card-premium p-6" data-testid="settings-updates-card">
          <div className="flex items-start gap-4">
            <div className="h-10 w-10 bg-[#38bdf8]/10 flex items-center justify-center shrink-0 rounded-md">
              <DownloadCloud className="h-5 w-5 text-[#38bdf8]" strokeWidth={2} />
            </div>
            <div className="flex-1">
              <h2 className="font-heading text-xl font-bold tracking-tight">Обновления приложения</h2>
              <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
                Текущая версия: <b>{appVer?.version || "—"}</b>
                {appVer?.git_sha ? <span className="text-muted-foreground"> · {appVer.git_sha}</span> : null}.
                Проверьте наличие новой версии в GitHub Releases и обновитесь в один клик — приложение
                скачает установщик и перезапустится.
              </p>

              {updInfo?.update_available && (
                <div className="mt-3 rounded-md border border-[#38bdf8]/40 bg-[#38bdf8]/5 p-3 text-sm">
                  Доступна версия <b>{updInfo.latest_version}</b>
                  {updInfo.published_at ? ` от ${new Date(updInfo.published_at).toLocaleString("ru-RU")}` : ""}.
                  {updInfo.notes ? (
                    <div className="mt-1 text-xs text-muted-foreground whitespace-pre-wrap max-h-28 overflow-auto">
                      {updInfo.notes}
                    </div>
                  ) : null}
                </div>
              )}
              {updInfo && !updInfo.update_available && !updInfo.error && (
                <div className="mt-3 text-sm text-emerald-400">Установлена последняя версия.</div>
              )}

              <div className="flex flex-wrap gap-2 mt-4">
                <Button
                  onClick={handleCheckUpdates}
                  disabled={checking || applying}
                  variant="outline"
                  data-testid="btn-check-updates"
                >
                  {checking ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                  Проверить обновления
                </Button>
                <Button
                  onClick={handleApplyUpdate}
                  disabled={applying || !updInfo?.update_available}
                  className="bg-[#38bdf8] hover:bg-[#0ea5e9] text-black"
                  data-testid="btn-apply-update"
                >
                  {applying ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <DownloadCloud className="h-4 w-4 mr-2" />}
                  Обновить приложение
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reg-authority profile */}
      <div className="card-premium p-6" data-testid="settings-regprofile-card">
        <div className="flex items-start gap-4">
          <div className="h-10 w-10 bg-[#EC4899]/10 flex items-center justify-center shrink-0 rounded-md">
            <Building2 className="h-5 w-5 text-[#EC4899]" strokeWidth={2} />
          </div>
          <div className="flex-1">
            <h2 className="font-heading text-xl font-bold tracking-tight">Профиль органа регистрации</h2>
            <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
              Наименование органа, начальник и город. Эти значения автоматически подставляются
              в бланк «СООБЩЕНИЕ» (поля «Орган регистрации», «Начальник») при открытии разделов
              «Печать на бланке» и «Полная печать».
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4 max-w-2xl">
              <div className="sm:col-span-2">
                <label className="text-xs text-muted-foreground">Наименование органа регистрации</label>
                <Input
                  value={profile.reg_organ}
                  onChange={(e) => setProfile((s) => ({ ...s, reg_organ: e.target.value }))}
                  placeholder="напр. ОГиМ Мозырского РОВД"
                  data-testid="regprofile-organ"
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">Начальник</label>
                <Input
                  value={profile.chief}
                  onChange={(e) => setProfile((s) => ({ ...s, chief: e.target.value }))}
                  placeholder="напр. Ковалёв А.А."
                  data-testid="regprofile-chief"
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">Город</label>
                <Input
                  value={profile.city}
                  onChange={(e) => setProfile((s) => ({ ...s, city: e.target.value }))}
                  placeholder="напр. г. Мозырь"
                  data-testid="regprofile-city"
                />
              </div>
            </div>
            <Button
              onClick={handleSaveProfile}
              disabled={savingProfile}
              className="mt-4 bg-[#EC4899] hover:bg-[#DB2777]"
              data-testid="regprofile-save"
            >
              {savingProfile ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
              Сохранить профиль
            </Button>
          </div>
        </div>
      </div>

      {/* Счётчики проживающих (Заявление) */}
      <div className="card-premium p-6" data-testid="settings-counters-card">
        <div className="flex items-start gap-4">
          <div className="h-10 w-10 bg-[#a855f7]/10 flex items-center justify-center shrink-0 rounded-md">
            <Settings2 className="h-5 w-5 text-[#a855f7]" strokeWidth={2} />
          </div>
          <div className="flex-1">
            <h2 className="font-heading text-xl font-bold tracking-tight">Счётчики проживающих (Заявление)</h2>
            <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
              Автоподсчёт полей на стр. 2 заявления: «проживает», «несовершеннолетних»,
              «совершеннолетних», «свободных мест». Задайте состояние общежития
              <b> до первого договора</b> — далее каждый договор в порядке номера прибавляет:
              всего +1, несовершеннолетний/совершеннолетний +1 (возраст берётся из даты рождения),
              свободных −1. Уже посчитанные заявления не меняются. Пока номер есть не у всех
              договоров — счёт не запускается.
            </p>
            <label className="flex items-center gap-2 mt-4 text-sm">
              <input
                type="checkbox"
                checked={!!cbase.enabled}
                onChange={(e) => setCbase({ ...cbase, enabled: e.target.checked })}
                data-testid="counters-enabled"
              />
              Включить автоподсчёт
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 max-w-2xl">
              {[
                ["total", "Всего проживающих"],
                ["minors", "Несовершеннолетних"],
                ["adults", "Совершеннолетних"],
                ["free", "Свободных мест"],
              ].map(([k, label]) => (
                <div key={k}>
                  <label className="text-xs text-muted-foreground">{label} (старт)</label>
                  <Input
                    type="number"
                    value={cbase[k]}
                    onChange={(e) => setCbase({ ...cbase, [k]: e.target.value })}
                    data-testid={`counters-${k}`}
                  />
                </div>
              ))}
            </div>
            {counterMsg ? (
              <div className="mt-3 text-sm text-amber-400" data-testid="counters-msg">{counterMsg}</div>
            ) : null}
            <div className="flex flex-wrap gap-2 mt-4">
              <Button
                onClick={handleSaveCounters}
                disabled={savingCounters}
                className="bg-[#a855f7] hover:bg-[#9333ea]"
                data-testid="counters-save-btn"
              >
                {savingCounters ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
                Сохранить и пересчитать всё
              </Button>
              <Button
                variant="outline"
                onClick={handleRecompute}
                disabled={recomputing}
                data-testid="counters-recompute-btn"
              >
                {recomputing ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                Досчитать новые
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Windows installer link */}
      <div className="card-premium p-6" data-testid="settings-winlink-card">
        <div className="flex items-start gap-4">
          <div className="h-10 w-10 bg-[#38bdf8]/10 flex items-center justify-center shrink-0 rounded-md">
            <MonitorDown className="h-5 w-5 text-[#38bdf8]" strokeWidth={2} />
          </div>
          <div className="flex-1">
            <h2 className="font-heading text-xl font-bold tracking-tight">Установщик Windows</h2>
            <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
              Прямая ссылка на <b>BanetskayaSetup.exe</b> для кнопки «Скачать для Windows» на стартовой
              странице. Сборка публикуется в разделе <b>Releases</b> вашего GitHub-репозитория —
              удобнее всего вставить ссылку вида:
            </p>
            <code className="block text-xs bg-accent px-3 py-2 mt-2 rounded overflow-x-auto">
              https://github.com/ВАШ_ЛОГИН/ВАШ_РЕПО/releases/latest/download/BanetskayaSetup.exe
            </code>
            <div className="flex flex-wrap items-center gap-2 mt-4">
              <Input
                value={winUrl}
                onChange={(e) => setWinUrl(e.target.value)}
                placeholder="https://github.com/.../releases/latest/download/BanetskayaSetup.exe"
                className="flex-1 min-w-[260px]"
                data-testid="settings-winurl-input"
              />
              <Button
                className="rounded-none bg-[#EC4899] hover:bg-[#DB2777] text-white"
                onClick={handleSaveWin}
                disabled={savingWin}
                data-testid="settings-winurl-save"
              >
                {savingWin ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                Сохранить ссылку
              </Button>
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground bg-accent px-3 py-2 mt-3">
              <Info className="h-4 w-4 shrink-0" />
              Пока ссылка не задана, кнопка «Скачать для Windows» показывает инструкцию по сборке.
            </div>
          </div>
        </div>
      </div>

      {/* Template info */}
      <div className="card-premium p-6">
        <div className="flex items-start gap-4">
          <div className="h-10 w-10 bg-[#EC4899]/10 flex items-center justify-center shrink-0">
            <FileCheck2 className="h-5 w-5 text-[#EC4899]" strokeWidth={2} />
          </div>
          <div className="space-y-2">
            <h2 className="font-heading text-xl font-bold tracking-tight">Шаблон договора</h2>
            <p className="text-sm text-muted-foreground leading-relaxed max-w-2xl">
              Договор найма жилого помещения государственного жилищного фонда в общежитии.
              Оформление, текст, реквизиты колледжа, данные директора и начальника ОКЮР сохраняются
              один в один как в исходном Word. Автоматически подставляются только переменные поля из
              Excel — постоянная часть договора не меняется.
            </p>
            <div className="flex items-center gap-2 text-xs text-muted-foreground bg-accent px-3 py-2 mt-2">
              <Info className="h-4 w-4 shrink-0" />
              Чтобы заменить шаблон на свой, поместите новый .docx с теми же полями — обратитесь к разработчику.
            </div>
          </div>
        </div>
      </div>

      {/* Sample excel */}
      <div className="card-premium p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="font-heading text-xl font-bold tracking-tight">Образец Excel</h2>
            <p className="text-sm text-muted-foreground mt-1 max-w-xl">
              Скачайте готовый файл с нужными колонками и примером строки — заполните своими данными и
              загрузите на вкладке «Генерация».
            </p>
          </div>
          <Button
            className="rounded-none bg-[#EC4899] hover:bg-[#DB2777] text-white h-11"
            onClick={handleSample}
            disabled={downloading}
            data-testid="settings-download-sample-btn"
          >
            <Download className="h-4 w-4" />
            Скачать шаблон Excel
          </Button>
        </div>
      </div>

      {/* Demo data */}
      <div className="card-premium p-6" data-testid="settings-demo-card">
        <div className="flex items-start gap-4">
          <div className="h-10 w-10 bg-[#EC4899]/10 flex items-center justify-center shrink-0 rounded-md">
            <Database className="h-5 w-5 text-[#EC4899]" strokeWidth={2} />
          </div>
          <div className="flex-1">
            <h2 className="font-heading text-xl font-bold tracking-tight">Тестовые данные</h2>
            <p className="text-sm text-muted-foreground mt-1 max-w-xl">
              Загрузите набор демонстрационных договоров (готовые + черновики), чтобы
              посмотреть, как выглядит история, редактор и печать. Можно очистить в один клик.
            </p>
            <div className="flex flex-wrap gap-2 mt-4">
              <Button
                className="rounded-none bg-[#EC4899] hover:bg-[#DB2777] text-white"
                onClick={handleSeed}
                disabled={seeding}
                data-testid="settings-seed-btn"
              >
                {seeding ? <Loader2 className="h-4 w-4 animate-spin" /> : <Database className="h-4 w-4" />}
                Загрузить демо-договоры
              </Button>
              <Button
                variant="outline"
                className="rounded-none"
                onClick={handleClearDemo}
                disabled={clearing}
                data-testid="settings-clear-demo-btn"
              >
                {clearing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
                Очистить демо
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Templates */}
      <div className="card-premium" data-testid="settings-templates-card">
        <div className="p-4 border-b border-border flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-3">
            <FileText className="h-5 w-5 text-[#EC4899]" />
            <div>
              <h2 className="font-heading text-xl font-bold tracking-tight">Шаблоны договоров</h2>
              <p className="text-sm text-muted-foreground mt-0.5">
                Загрузите свой .docx-шаблон. Встроенный шаблон никогда не изменяется.
              </p>
            </div>
          </div>
          <label>
            <input type="file" accept=".docx" className="hidden" onChange={handleTemplateUpload} data-testid="settings-template-upload" />
            <span className={`inline-flex items-center gap-2 h-10 px-4 rounded-none text-white cursor-pointer ${tplBusy ? "bg-[#DB2777]" : "bg-[#EC4899] hover:bg-[#DB2777]"}`}>
              {tplBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileUp className="h-4 w-4" />}
              Загрузить .docx
            </span>
          </label>
        </div>
        <div>
          {templates.map((tpl) => (
            <div key={tpl.id} className="flex items-center justify-between gap-3 px-4 py-3 border-b border-border" data-testid={`settings-template-${tpl.id}`}>
              <div className="flex items-center gap-3 min-w-0">
                <FileText className="h-4 w-4 text-[#EC4899] shrink-0" />
                <span className="text-sm font-medium truncate">{tpl.name}</span>
                {tpl.builtin && <span className="text-[10px] uppercase tracking-wider text-muted-foreground border border-border px-1.5 py-0.5 rounded">встроенный</span>}
                {tpl.active && <span className="text-[10px] uppercase tracking-wider text-emerald-400 border border-emerald-500/40 px-1.5 py-0.5 rounded">активен</span>}
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {tpl.active ? (
                  <span className="inline-flex items-center gap-1 text-emerald-400 text-sm"><Check className="h-4 w-4" /> Выбран</span>
                ) : (
                  <Button variant="outline" size="sm" className="rounded-none" onClick={() => handleActivate(tpl.id)} data-testid={`settings-template-activate-${tpl.id}`}>Сделать активным</Button>
                )}
                {!tpl.builtin && (
                  <Button variant="ghost" size="sm" className="rounded-none text-[#FF3B30] hover:text-[#FF3B30] hover:bg-red-500/10" onClick={() => handleDeleteTemplate(tpl.id)} data-testid={`settings-template-delete-${tpl.id}`}><Trash2 className="h-4 w-4" /></Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Presets */}
      <div className="card-premium" data-testid="settings-presets-card">
        <div className="p-4 border-b border-border flex items-center gap-3">
          <Bookmark className="h-5 w-5 text-[#EC4899]" />
          <div>
            <h2 className="font-heading text-xl font-bold tracking-tight">
              Пресеты полей ({presets.length})
            </h2>
            <p className="text-sm text-muted-foreground mt-0.5">
              Сохранённые наборы полей для быстрого заполнения. Создаются в редакторе договора.
            </p>
          </div>
        </div>
        {presets.length === 0 ? (
          <div className="px-4 py-8 text-center text-muted-foreground text-sm">
            Пресетов пока нет. Откройте редактор договора и нажмите «Сохранить пресет».
          </div>
        ) : (
          <div>
            {presets.map((p) => (
              <div
                key={p.id}
                className="flex items-center justify-between gap-3 px-4 py-3 border-b border-border"
                data-testid={`settings-preset-${p.id}`}
              >
                <div className="flex items-center gap-3">
                  <Bookmark className="h-4 w-4 text-[#EC4899]" />
                  <span className="text-sm font-medium">{p.name}</span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="rounded-none text-[#FF3B30] hover:text-[#FF3B30] hover:bg-red-500/10"
                  onClick={() => handleDeletePreset(p.id)}
                  data-testid={`settings-preset-delete-${p.id}`}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Fields list */}
      <div className="card-premium">
        <div className="p-4 border-b border-border">
          <h2 className="font-heading text-xl font-bold tracking-tight">
            Поля автозаполнения ({FIELDS.length})
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Эти поля берутся из Excel и подставляются в договор.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          {FIELDS.map((f, i) => (
            <div
              key={f.key}
              className="flex items-center gap-3 px-4 py-3 border-b border-r border-border"
              data-testid={`settings-field-${f.key}`}
            >
              <span className="font-heading text-sm font-bold text-[#EC4899] w-6">
                {String(i + 1).padStart(2, "0")}
              </span>
              <span className="text-sm">{f.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
