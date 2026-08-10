import { NavLink, Outlet } from "react-router-dom";
import { FileSignature, LayoutDashboard, FilePlus2, History, Settings } from "lucide-react";

const NAV = [
  { to: "/", end: true, label: "Дашборд", icon: LayoutDashboard, testid: "nav-dashboard" },
  { to: "/generate", label: "Генерация", icon: FilePlus2, testid: "nav-generate" },
  { to: "/history", label: "История", icon: History, testid: "nav-history" },
  { to: "/settings", label: "Настройки", icon: Settings, testid: "nav-settings" },
];

const itemClass = ({ isActive }) =>
  `flex items-center gap-3 px-4 py-3 text-sm font-medium border-l-2 transition-colors ${
    isActive
      ? "border-[#002FA7] text-[#002FA7] bg-[#F0F4FF]"
      : "border-transparent text-muted-foreground hover:text-[#0A0A0A] hover:bg-accent"
  }`;

export default function Layout() {
  return (
    <div className="App min-h-screen bg-background flex">
      <aside className="no-print w-60 shrink-0 bg-white border-r border-border flex flex-col sticky top-0 h-screen">
        <div className="flex items-center gap-3 px-5 h-16 border-b border-border">
          <div className="h-9 w-9 bg-[#002FA7] flex items-center justify-center">
            <FileSignature className="h-5 w-5 text-white" strokeWidth={2} />
          </div>
          <div>
            <div className="font-heading font-black tracking-tighter text-base leading-none">
              Договоры найма
            </div>
            <div className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground mt-0.5">
              из Excel
            </div>
          </div>
        </div>
        <nav className="flex flex-col py-3" data-testid="sidebar-nav">
          {NAV.map(({ to, end, label, icon: Icon, testid }) => (
            <NavLink key={to} to={to} end={end} className={itemClass} data-testid={testid}>
              <Icon className="h-4 w-4" strokeWidth={2} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto px-5 py-4 border-t border-border">
          <p className="text-[11px] text-muted-foreground leading-relaxed">
            Администратор колледжа · автозаполнение договоров найма
          </p>
        </div>
      </aside>
      <div className="flex-1 min-w-0">
        <main className="max-w-6xl mx-auto px-8 py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
