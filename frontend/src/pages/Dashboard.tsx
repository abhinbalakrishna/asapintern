import { useEffect, useRef, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { addReading, analyzeFrame, endSession, startSession, type SessionDetail } from "../api/client";

const CAPTURE_INTERVAL_MS = 1500;

interface LivePoint {
  t: number;
  score: number;
}

function statusColor(status: string) {
  if (status === "Focused") return "text-emerald-500";
  if (status === "No face detected") return "text-slate-400";
  if (status === "Eyes closed / drowsy") return "text-red-500";
  return "text-amber-500";
}

export function Dashboard() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const intervalRef = useRef<number | null>(null);
  const sessionIdRef = useRef<number | null>(null);

  const [tracking, setTracking] = useState(false);
  const [starting, setStarting] = useState(false);
  const [permissionError, setPermissionError] = useState<string | null>(null);
  const [currentScore, setCurrentScore] = useState<number | null>(null);
  const [currentStatus, setCurrentStatus] = useState<string>("Idle");
  const [points, setPoints] = useState<LivePoint[]>([]);
  const [summary, setSummary] = useState<SessionDetail | null>(null);

  useEffect(() => {
    return () => stopCamera();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stopCamera = () => {
    if (intervalRef.current) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  };

  const captureAndAnalyze = async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || !sessionIdRef.current) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      async (blob) => {
        if (!blob || !sessionIdRef.current) return;
        try {
          const result = await analyzeFrame(blob);
          setCurrentScore(result.score);
          setCurrentStatus(result.status);
          setPoints((prev) => [...prev.slice(-29), { t: Date.now(), score: result.score }]);
          await addReading(sessionIdRef.current, {
            score: result.score,
            status: result.status,
            yaw: result.yaw,
            pitch: result.pitch,
            eyes_closed: result.eyes_closed,
          });
        } catch {
          // transient frame failures are fine to skip
        }
      },
      "image/jpeg",
      0.8
    );
  };

  const handleStart = async () => {
    setPermissionError(null);
    setSummary(null);
    setStarting(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      const session = await startSession(`Session ${new Date().toLocaleString()}`);
      sessionIdRef.current = session.id;
      setPoints([]);
      setTracking(true);
      intervalRef.current = window.setInterval(captureAndAnalyze, CAPTURE_INTERVAL_MS);
    } catch {
      setPermissionError("Could not access webcam. Please allow camera permission and try again.");
      stopCamera();
    } finally {
      setStarting(false);
    }
  };

  const handleStop = async () => {
    stopCamera();
    setTracking(false);
    if (sessionIdRef.current) {
      const finished = await endSession(sessionIdRef.current);
      setSummary(finished);
      sessionIdRef.current = null;
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="mb-1 text-2xl font-semibold text-slate-900 dark:text-white">Focus Session</h1>
      <p className="mb-6 text-sm text-slate-500 dark:text-slate-400">
        Start your webcam and we'll estimate your attention in real time using head pose and eye
        tracking.
      </p>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <div className="relative aspect-video overflow-hidden rounded-xl bg-slate-950">
            <video ref={videoRef} muted playsInline className="h-full w-full object-cover" />
            {!tracking && (
              <div className="absolute inset-0 flex items-center justify-center text-sm text-slate-400">
                Camera preview will appear here
              </div>
            )}
          </div>
          <canvas ref={canvasRef} className="hidden" />

          <div className="mt-4 flex items-center gap-3">
            {!tracking ? (
              <button
                onClick={handleStart}
                disabled={starting}
                className="rounded-lg bg-emerald-600 px-4 py-2 font-medium text-white transition hover:bg-emerald-700 disabled:opacity-60"
              >
                {starting ? "Starting..." : "Start tracking"}
              </button>
            ) : (
              <button
                onClick={handleStop}
                className="rounded-lg bg-red-600 px-4 py-2 font-medium text-white transition hover:bg-red-700"
              >
                Stop session
              </button>
            )}
          </div>
          {permissionError && <p className="mt-2 text-sm text-red-500">{permissionError}</p>}
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Current attention score</p>
          <p className="mt-1 text-5xl font-bold text-slate-900 dark:text-white">
            {currentScore !== null ? currentScore.toFixed(0) : "--"}
          </p>
          <p className={`mt-1 text-sm font-medium ${statusColor(currentStatus)}`}>{currentStatus}</p>

          <div className="mt-6 h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={points}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-800" />
                <XAxis dataKey="t" tick={false} />
                <YAxis domain={[0, 100]} width={30} tick={{ fontSize: 12 }} />
                <Tooltip
                  formatter={(value) => (typeof value === "number" ? value.toFixed(0) : value)}
                  labelFormatter={() => ""}
                />
                <Line type="monotone" dataKey="score" stroke="#10b981" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {summary && (
        <div className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50 p-6 dark:border-emerald-900 dark:bg-emerald-950/40">
          <h2 className="text-lg font-semibold text-emerald-800 dark:text-emerald-300">
            Session complete
          </h2>
          <p className="mt-1 text-sm text-emerald-700 dark:text-emerald-400">
            Average attention score:{" "}
            <span className="font-semibold">
              {summary.average_score !== null ? summary.average_score.toFixed(1) : "N/A"}
            </span>{" "}
            across {summary.readings.length} readings.
          </p>
        </div>
      )}
    </div>
  );
}
