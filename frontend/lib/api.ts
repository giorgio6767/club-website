/** 后端接口类型与请求封装。线上同源走 /api（nginx 反代），开发期设
 *  NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000。 */
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";

export type Shift = {
  id: number;
  post_name: string;
  location: string;
  start_time: string;
  end_time: string;
  capacity: number;
  booked_count: number;
};

export type Activity = {
  id: number;
  title: string;
  description: string;
  status: string;
  signup_deadline: string | null;
  shifts: Shift[];
};

export type ActivitySummary = Omit<Activity, "shifts">;

export type SignupPayload = {
  name: string;
  student_id: string;
  college: string;
  phone: string;
  shift_ids: number[];
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    ...init,
  });
  const body = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const detail = (body as { detail?: string }).detail ?? `请求失败（${resp.status}）`;
    throw new Error(detail);
  }
  return body as T;
}

export const api = {
  listOpenActivities: () => request<ActivitySummary[]>("/api/activities"),
  getActivity: (id: number) => request<Activity>(`/api/activities/${id}`),
  signup: (activityId: number, payload: SignupPayload) =>
    request<{ member_id: number; booked_shift_ids: number[] }>(
      `/api/activities/${activityId}/signups`,
      { method: "POST", body: JSON.stringify(payload) },
    ),
};

/** 场次剩余名额与状态的小工具 */
export function shiftState(s: Shift): { full: boolean; remaining: number } {
  const remaining = Math.max(0, s.capacity - s.booked_count);
  return { full: remaining === 0, remaining };
}

export function fmtShiftTime(startIso: string, endIso: string): string {
  const s = new Date(startIso);
  const e = new Date(endIso);
  const p = (n: number) => String(n).padStart(2, "0");
  const sameDay = s.toDateString() === e.toDateString();
  const day = `${s.getMonth() + 1}月${s.getDate()}日`;
  const start = `${p(s.getHours())}:${p(s.getMinutes())}`;
  const end = sameDay
    ? `${p(e.getHours())}:${p(e.getMinutes())}`
    : `${e.getMonth() + 1}月${e.getDate()}日 ${p(e.getHours())}:${p(e.getMinutes())}`;
  return `${day} ${start} ~ ${end}`;
}
