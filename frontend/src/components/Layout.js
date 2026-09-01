import { NavLink, Outlet } from "react-router-dom";
import { FileSignature, LayoutDashboard, FilePlus2, History, Settings, Stamp, FileText, Activity, ClipboardList, Printer, Building2 } from "lucide-react";

const NAV_GROUPS = [
  {
    title: "Обзор",
    items: [
      { to: "/", end: true, label: "Дашборд", icon: LayoutDashboard, testid: "nav-dashboard" },
      { to: "/package", label: "Полный пакет", icon: Printer, testid: "nav-package" },
      { to: "/residents", label: "Заселение по этажам", icon: Building2, testid: "nav-residents" },
    ],
  },
  {
    title: "Договоры найма",
    items: [
      { to: "/generate", label: "Генерация из Excel", icon: FilePlus2, testid: "nav-generate" },
      { to: "/history", label: "История договоров", icon: History, testid: "nav-history" },
    ],
  },
  {
    title: "Бланк «СООБЩЕНИЕ»",
    items: [
      { to: "/blank", label: "Печать на бланке", icon: Stamp, testid: "nav-blank" },
      { to: "/full-print", label: "Полная печать", icon: FileText, testid: "nav-full-print" },
    ],
  },
  {
    title: "Адресный листок",
    items: [
      { to: "/forma19", label: "Форма 19 (прибытие)", icon: ClipboardList, testid: "nav-forma19" },
      { to: "/forma24", label: "Талон учёта (Форма 24)", icon: ClipboardList, testid: "nav-forma24" },
    ],
  },
  {
    title: "Регистрация по месту жительства",
    items: [
      { to: "/zayavlenie", label: "Заявление о регистрации", icon: FileSignature, testid: "nav-zayavlenie" },
    ],
  },
  {
    title: "Система",
    items: [
      { to: "/diagnostics", label: "Проверка системы", icon: Activity, testid: "nav-diagnostics" },
      { to: "/settings", label: "Настройки", icon: Settings, testid: "nav-settings" },
    ],
  },
];

const itemClass = ({ isActive }) =>
  `group relative flex items-center gap-3 mx-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
    isActive
      ? "text-white bg-gradient-to-r from-[#EC4899]/25 to-[#EC4899]/5 border border-[#EC4899]/30 shadow-[0_8px_24px_-16px_rgba(225,29,72,0.8)]"
      : "text-muted-foreground border border-transparent hover:text-slate-900 hover:bg-white/80"
  }`;

export default function Layout() {
  return (
    <div className="App min-h-screen bg-background flex">
      <aside className="no-print w-64 shrink-0 glass border-r border-pink-100 flex flex-col sticky top-0 h-screen z-30">
        <div className="flex items-center gap-3 px-5 h-20 border-b border-pink-100">
          <div className="h-10 w-10 bg-gradient-to-br from-[#F43F5E] to-[#DB2777] flex items-center justify-center rounded-xl glow-crimson">
            <FileSignature className="h-5 w-5 text-slate-800" strokeWidth={2} />
          </div>
          <div>
            <div className="font-heading font-bold text-xl leading-none tracking-tight">
              Banetskaya<span className="text-[#EC4899]">.by</span>
            </div>
            <div className="text-[10px] font-mono uppercase tracking-[0.25em] text-muted-foreground mt-1">
              Document Engine
            </div>
          </div>
        </div>
        <nav className="flex flex-col py-4 overflow-y-auto" data-testid="sidebar-nav">
          {NAV_GROUPS.map((group) => (
            <div key={group.title} className="mb-3">
              <div className="px-5 pt-2 pb-2 text-[10px] font-mono uppercase tracking-[0.2em] text-slate-400">
                {group.title}
              </div>
              {group.items.map(({ to, end, label, icon: Icon, testid }) => (
                <NavLink key={to} to={to} end={end} className={itemClass} data-testid={testid}>
                  <Icon className="h-4 w-4" strokeWidth={2} />
                  {label}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div className="mt-auto px-5 py-5 border-t border-pink-100">
          <p className="text-[11px] text-muted-foreground leading-relaxed">
            Автозаполнение договоров найма из Excel · для администратора
          </p>
        </div>
      </aside>
      <div className="flex-1 min-w-0 bg-grid">
        <main className="max-w-6xl mx-auto px-8 py-10 page-enter">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
