import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getSession, type SessionDetail as SessionDetailType } from "../api/client";

export function SessionDetail() {
  const { id } = useParams();
  const [session, setSession] = useState<SessionDetailType | null>(null);

  useEffect(() => {
    if (id) getSession(Number(id)).then(setSession);
  }, [id]);

  if (!session) {
    return <p className="mx-auto max-w-4xl px-4 py-8 text-slate-500 dark:text-slate-400">Loading...</p>;
  }

  const chartData = session.readings.map((r) => ({
    time: new Date(r.timestamp).toLocaleTimeString(),
    score: r.score,
  }));

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <Link to="/history" className="text-sm text-emerald-600 hover:underline dark:text-emerald-400">
        ← Back to history
      </Link>

      <h1 className="mt-2 mb-1 text-2xl font-semibold text-slate-900 dark:text-white">{session.label}</h1>
      <p className="mb-6 text-sm text-slate-500 dark:text-slate-400">
        {new Date(session.started_at).toLocaleString()}
        {session.ended_at && ` — ${new Date(session.ended_at).toLocaleString()}`}
      </p>

      <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <p className="text-sm text-slate-500 dark:text-slate-400">Average score</p>
          <p className="text-2xl font-semibold text-slate-900 dark:text-white">
            {session.average_score !== null ? session.average_score.toFixed(1) : "N/A"}
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <p className="text-sm text-slate-500 dark:text-slate-400">Readings</p>
          <p className="text-2xl font-semibold text-slate-900 dark:text-white">{session.readings.length}</p>
        </div>
      </div>

      <div className="h-64 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-800" />
            <XAxis dataKey="time" tick={{ fontSize: 11 }} />
            <YAxis domain={[0, 100]} width={30} tick={{ fontSize: 12 }} />
            <Tooltip />
            <Line type="monotone" dataKey="score" stroke="#10b981" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
