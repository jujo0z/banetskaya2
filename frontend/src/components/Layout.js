import { NavLink, Outlet } from "react-router-dom";
import { FileSignature, LayoutDashboard, FilePlus2, History, Settings, Stamp, FileText } from "lucide-react";

const NAV_GROUPS = [
  {
    title: "Обзор",
    items: [
      { to: "/", end: true, label: "Дашборд", icon: LayoutDashboard, testid: "nav-dashboard" },
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
    title: "Система",
    items: [
      { to: "/settings", label: "Настройки", icon: Settings, testid: "nav-settings" },
    ],
  },
];

const itemClass = ({ isActive }) =>
  `group flex items-center gap-3 px-5 py-2.5 text-sm font-medium border-l-2 transition-colors duration-200 ${
    isActive
      ? "border-[#E11D48] text-white bg-white/5"
      : "border-transparent text-muted-foreground hover:text-white hover:bg-white/5"
  }`;

export default function Layout() {
  return (
    <div className="App min-h-screen bg-background flex">
      <aside className="no-print w-64 shrink-0 bg-[#0A0A0C]/80 backdrop-blur-xl border-r border-white/10 flex flex-col sticky top-0 h-screen z-30">
        <div className="flex items-center gap-3 px-5 h-20 border-b border-white/10">
          <div className="h-10 w-10 bg-gradient-to-br from-[#F43F5E] to-[#BE123C] flex items-center justify-center rounded-md glow-crimson">
            <FileSignature className="h-5 w-5 text-white" strokeWidth={2} />
          </div>
          <div>
            <div className="font-heading font-bold text-xl leading-none tracking-tight">
              Banetskaya<span className="text-[#E11D48]">.by</span>
            </div>
            <div className="text-[10px] font-mono uppercase tracking-[0.25em] text-muted-foreground mt-1">
              Document Engine
            </div>
          </div>
        </div>
        <nav className="flex flex-col py-4 overflow-y-auto" data-testid="sidebar-nav">
          {NAV_GROUPS.map((group) => (
            <div key={group.title} className="mb-2">
              <div className="px-5 pt-3 pb-1.5 text-[10px] font-mono uppercase tracking-[0.2em] text-white/35">
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
        <div className="mt-auto px-5 py-5 border-t border-white/10">
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
