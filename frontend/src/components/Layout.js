import { NavLink, Outlet } from "react-router-dom";
import { FileSignature } from "lucide-react";

const tabClass = ({ isActive }) =>
  `px-4 py-3 text-sm font-semibold uppercase tracking-[0.15em] border-b-2 transition-colors ${
    isActive
      ? "border-[#002FA7] text-[#002FA7]"
      : "border-transparent text-muted-foreground hover:text-[#0A0A0A]"
  }`;

export default function Layout() {
  return (
    <div className="App min-h-screen bg-background">
      <header className="no-print bg-white border-b border-border sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 bg-[#002FA7] flex items-center justify-center">
                <FileSignature className="h-5 w-5 text-white" strokeWidth={2} />
              </div>
              <div>
                <div className="font-heading font-black tracking-tighter text-lg leading-none">
                  Договоры найма
                </div>
                <div className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
                  Автозаполнение из Excel
                </div>
              </div>
            </div>
            <nav className="flex items-center gap-1" data-testid="main-nav">
              <NavLink to="/" end className={tabClass} data-testid="nav-generate">
                Генерация
              </NavLink>
              <NavLink to="/history" className={tabClass} data-testid="nav-history">
                История
              </NavLink>
            </nav>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
