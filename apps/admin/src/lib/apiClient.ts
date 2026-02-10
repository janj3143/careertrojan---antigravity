export type ApiOk<T> = { ok: true; data: T; meta?: Record<string, unknown> };
export type ApiErr = { ok: false; error: { code: string; message: string; details?: unknown } };
export type ApiResponse<T> = ApiOk<T> | ApiErr;

const BASE =
  (import.meta as any).env?.VITE_API_BASE_URL || "/api/v1";

function join(base: string, path: string) {
  if (!path.startsWith("/")) path = "/" + path;
  return base.replace(/\/+$/, "") + path;
}

function token(): string | null {
  return localStorage.getItem("access_token");
}

function headers(): HeadersInit {
  const t = token();
  return {
    "Content-Type": "application/json",
    ...(t ? { Authorization: `Bearer ${t}` } : {}),
  };
}

async function parse(res: Response) {
  const txt = await res.text();
  if (!txt) return null;
  try { return JSON.parse(txt); } catch { return txt; }
}

function err(code: string, message: string, details?: unknown): ApiErr {
  return { ok: false, error: { code, message, details } };
}

export async function apiGet<T>(path: string): Promise<ApiResponse<T>> {
  try {
    const res = await fetch(join(BASE, path), { method: "GET", headers: headers(), credentials: "include" });
    const payload = await parse(res);
    if (!res.ok) return err(`HTTP_${res.status}`, (payload as any)?.detail || res.statusText, payload);
    if (payload && typeof payload === "object" && "ok" in payload) return payload as ApiResponse<T>;
    return { ok: true, data: payload as T };
  } catch (e) {
    return err("NETWORK_ERROR", "Failed to reach API", String(e));
  }
}

export async function apiPost<T, B = unknown>(path: string, body?: B): Promise<ApiResponse<T>> {
  try {
    const res = await fetch(join(BASE, path), {
      method: "POST",
      headers: headers(),
      credentials: "include",
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const payload = await parse(res);
    if (!res.ok) return err(`HTTP_${res.status}`, (payload as any)?.detail || res.statusText, payload);
    if (payload && typeof payload === "object" && "ok" in payload) return payload as ApiResponse<T>;
    return { ok: true, data: payload as T };
  } catch (e) {
    return err("NETWORK_ERROR", "Failed to reach API", String(e));
  }
}
