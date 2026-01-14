import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../../auth/hooks";
import logo from "../../assets/ITAS-logo.png";

export type NavItem = {
  label: string;
  to: string;
  meta?: string;
};

const getInitials = (name: string) => {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  const initials = parts.slice(0, 2).map((part) => part[0]?.toUpperCase() || "").join("");
  return initials || "U";
};

export default function AppShell({ nav }: { nav: NavItem[] }) {
  const { user, logout } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const name = user?.name || "User";
  const roleLabel = user?.role === "PM" ? "Project Manager" : "Employee";

  return (
    <div className="app-shell">
      {/* Mobile Top Bar */}
      <div className="mobile-header">
        <div className="brand-mark">
          <img className="brand-logo" src={logo} alt="ITAS logo" />
        </div>
        <button
          className="btn btn-ghost btn-icon"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>
      </div>

      <aside className={`sidebar ${isMobileMenuOpen ? "is-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark">
            <img className="brand-logo" src={logo} alt="ITAS logo" />
          </div>
          <div className="status-pill">
            <span className="status-dot" />
            Live insights
          </div>
        </div>

        <div className="nav-section">Workspace</div>
        <nav className="nav">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setIsMobileMenuOpen(false)}
              className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
            >
              <span>{item.label}</span>
              {item.meta && <span className="nav-meta">{item.meta}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-card">
            <div className="avatar">{getInitials(name)}</div>
            <div className="user-info">
              <div className="user-name">{name}</div>
              <div className="user-role">{roleLabel}</div>
            </div>
          </div>
          <button type="button" className="btn btn-ghost" onClick={logout}>
            Sign out
          </button>
          <div style={{ marginTop: "8px", fontSize: "0.7rem", color: "var(--muted)", textAlign: "center" }}>
            &copy; {new Date().getFullYear()} <a href="https://github.com/Abumarar" target="_blank" rel="noopener noreferrer" className="hover:text-[var(--accent)]">Mohammad Abumarar</a>
          </div>
        </div>
      </aside>

      {isMobileMenuOpen && (
        <div className="sidebar-backdrop" onClick={() => setIsMobileMenuOpen(false)} />
      )}

      <div className="main">
        <header className="topbar">
          <div className="topbar-left">
            <div className="topbar-title">ITAS Command Center</div>
            <div className="topbar-subtitle">
              Align tasks to skills with confident recommendations.
            </div>
          </div>
          <div className="topbar-right">
            <div className="search">
              <input
                className="search-input"
                type="search"
                placeholder="Search tasks, people, or skills"
                aria-label="Search"
              />
            </div>
            {user?.role === "PM" && (
              <NavLink to="/pm/tasks/new" className="btn btn-primary">
                New Task
              </NavLink>
            )}
          </div>
        </header>
        <Outlet />
      </div>
    </div>
  );
}
