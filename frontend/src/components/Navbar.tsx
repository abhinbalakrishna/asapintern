import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ThemeToggle } from "./ThemeToggle";

export function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="flex items-center justify-between border-b border-slate-200 bg-white/80 px-6 py-4 backdrop-blur dark:border-slate-800 dark:bg-slate-900/80">
      <Link to="/" className="flex items-center gap-2 text-lg font-semibold text-slate-900 dark:text-white">
        <span className="inline-block h-2.5 w-2.5 rounded-full bg-emerald-500" />
        FocusTracker
      </Link>

      <div className="flex items-center gap-4">
        {user && (
          <>
            <Link
              to="/dashboard"
              className="text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white"
            >
              Dashboard
            </Link>
            <Link
              to="/history"
              className="text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white"
            >
              History
            </Link>
            <span className="text-sm text-slate-400 dark:text-slate-500">|</span>
            <span className="text-sm text-slate-600 dark:text-slate-300">{user.username}</span>
            <button
              onClick={handleLogout}
              className="rounded-lg bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              Log out
            </button>
          </>
        )}
        <ThemeToggle />
      </div>
    </nav>
  );
}
