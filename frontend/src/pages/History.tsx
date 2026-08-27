import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listSessions, type TrackingSession } from "../api/client";

export function History() {
  const [sessions, setSessions] = useState<TrackingSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listSessions()
      .then(setSessions)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-semibold text-slate-900 dark:text-white">Session history</h1>

      {loading && <p className="text-slate-500 dark:text-slate-400">Loading...</p>}

      {!loading && sessions.length === 0 && (
        <p className="text-slate-500 dark:text-slate-400">
          No sessions yet. Start one from the Dashboard.
        </p>
      )}

      <div className="space-y-3">
        {sessions.map((s) => (
          <Link
            key={s.id}
            to={`/history/${s.id}`}
            className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4 transition hover:border-emerald-400 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-emerald-600"
          >
            <div>
              <p className="font-medium text-slate-900 dark:text-white">{s.label}</p>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                {new Date(s.started_at).toLocaleString()}
                {s.ended_at ? "" : " · in progress"}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-slate-500 dark:text-slate-400">Avg score</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                {s.average_score !== null ? s.average_score.toFixed(0) : "--"}
              </p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
