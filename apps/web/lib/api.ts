import type { ArtifactRead, PipelineRead, RunRead, RunTaskRead, TokenRead } from "@rnaseq/contracts";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem("rnaseq_token");
}

export function setToken(token: string): void {
  window.localStorage.setItem("rnaseq_token", token);
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(`${API_URL}${path}`, { ...init, headers, cache: "no-store" });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return (await response.json()) as T;
}

export async function login(email: string, password: string): Promise<TokenRead> {
  return apiFetch<TokenRead>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
}

export async function pipelines(): Promise<PipelineRead[]> {
  return apiFetch<PipelineRead[]>("/api/pipelines");
}

export async function createRun(payload: unknown): Promise<RunRead> {
  return apiFetch<RunRead>("/api/runs", { method: "POST", body: JSON.stringify(payload) });
}

export async function runDetail(id: string): Promise<RunRead> {
  return apiFetch<RunRead>(`/api/runs/${id}`);
}

export async function runTasks(id: string): Promise<RunTaskRead[]> {
  return apiFetch<RunTaskRead[]>(`/api/runs/${id}/tasks`);
}

export async function runArtifacts(id: string): Promise<ArtifactRead[]> {
  return apiFetch<ArtifactRead[]>(`/api/runs/${id}/artifacts`);
}

export async function runLog(id: string, type: "stdout" | "stderr" | "nextflow"): Promise<string> {
  const response = await apiFetch<{ content: string }>(`/api/runs/${id}/logs/${type}`);
  return response.content;
}

