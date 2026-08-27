import axios from "axios";

export const api = axios.create({
  baseURL: "/api",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface User {
  id: number;
  username: string;
  email: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface TrackingSession {
  id: number;
  started_at: string;
  ended_at: string | null;
  average_score: number | null;
  label: string;
}

export interface Reading {
  id: number;
  timestamp: string;
  score: number;
  status: string;
  yaw: number | null;
  pitch: number | null;
  eyes_closed: number;
}

export interface SessionDetail extends TrackingSession {
  readings: Reading[];
}

export interface FrameAnalysis {
  score: number;
  status: string;
  yaw: number | null;
  pitch: number | null;
  eyes_closed: boolean;
  face_detected: boolean;
}

export async function registerUser(username: string, email: string, password: string) {
  const { data } = await api.post<AuthResponse>("/auth/register", { username, email, password });
  return data;
}

export async function loginUser(username: string, password: string) {
  const form = new URLSearchParams();
  form.append("username", username);
  form.append("password", password);
  const { data } = await api.post<AuthResponse>("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}

export async function fetchMe() {
  const { data } = await api.get<User>("/auth/me");
  return data;
}

export async function startSession(label: string) {
  const { data } = await api.post<TrackingSession>("/sessions", { label });
  return data;
}

export async function addReading(sessionId: number, reading: Omit<FrameAnalysis, "face_detected">) {
  const { data } = await api.post<Reading>(`/sessions/${sessionId}/readings`, reading);
  return data;
}

export async function endSession(sessionId: number) {
  const { data } = await api.post<SessionDetail>(`/sessions/${sessionId}/end`);
  return data;
}

export async function listSessions() {
  const { data } = await api.get<TrackingSession[]>("/sessions");
  return data;
}

export async function getSession(sessionId: number) {
  const { data } = await api.get<SessionDetail>(`/sessions/${sessionId}`);
  return data;
}

export async function analyzeFrame(blob: Blob) {
  const form = new FormData();
  form.append("frame", blob, "frame.jpg");
  const { data } = await api.post<FrameAnalysis>("/attention/analyze", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
