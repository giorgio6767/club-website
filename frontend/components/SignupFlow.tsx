"use client";

/* 单页报名流程（2026-11 口径）：
   信息收集（姓名/学号/联系方式）在最上 → 地点→日期→时段→岗位 四级复选树 → 底部提交。
   由首页（单一开放活动时自动直入）与 /activities/[id] 共用。 */

import { useEffect, useMemo, useRef, useState } from "react";
import {
  api,
  fmtShiftTime,
  shiftState,
  type Activity,
  type Shift,
  type SignupPayload,
} from "@/lib/api";

/* ---------- 场次树数据结构 ---------- */

type SlotGroup = { key: string; label: string; shifts: Shift[] };
type DayGroup = { key: string; label: string; slots: SlotGroup[] };

function buildTree(shifts: Shift[]): DayGroup[] {
  const days = new Map<string, Map<string, Shift[]>>();
  for (const s of [...shifts].sort((a, b) => a.start_time.localeCompare(b.start_time))) {
    const d = new Date(s.start_time);
    const dayKey = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
    const slotKey = `${s.start_time}|${s.end_time}`;
    if (!days.has(dayKey)) days.set(dayKey, new Map());
    const slots = days.get(dayKey)!;
    if (!slots.has(slotKey)) slots.set(slotKey, []);
    slots.get(slotKey)!.push(s);
  }
  return [...days.entries()].map(([dayKey, slotMap]) => ({
    key: dayKey,
    label: (() => {
      const d = new Date(dayMapKeyToDate(dayKey));
      return `${d.getMonth() + 1}月${d.getDate()}日`;
    })(),
    slots: [...slotMap.entries()].map(([slotKey, list]) => ({
      key: slotKey,
      label: fmtShiftTime(list[0].start_time, list[0].end_time).split(" ").slice(1).join(" "),
      shifts: list,
    })),
  }));
}

function dayMapKeyToDate(key: string): Date {
  const [y, m, d] = key.split("-").map(Number);
  return new Date(y, m, d);
}

function p(n: number) {
  return String(n).padStart(2, "0");
}

/* ---------- 三态复选框 ---------- */

function Check({
  state,
  onChange,
  disabled,
  size = "base",
}: {
  state: "all" | "some" | "none";
  onChange: () => void;
  disabled?: boolean;
  size?: "base" | "sm";
}) {
  const ref = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (ref.current) ref.current.indeterminate = state === "some";
  }, [state]);
  return (
    <input
      ref={ref}
      type="checkbox"
      checked={state === "all"}
      onChange={onChange}
      disabled={disabled}
      className={`flex-none accent-red-700 ${size === "sm" ? "h-4 w-4" : "h-[18px] w-[18px]"}`}
    />
  );
}

/* ---------- 主组件 ---------- */

export default function SignupFlow({ activity: initial }: { activity: Activity }) {
  const [activity, setActivity] = useState<Activity>(initial);
  const [selected, setSelected] = useState<number[]>([]);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [form, setForm] = useState({ name: "", student_id: "", phone: "" });
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const tree = useMemo(() => buildTree(activity.shifts), [activity]);
  const location = activity.shifts[0]?.location ?? "";

  // 默认展开第一天和它的第一个时段，避免白屏感
  useEffect(() => {
    if (tree.length > 0) {
      const first = new Set<string>([`d:${tree[0].key}`]);
      if (tree[0].slots.length > 0) first.add(`s:${tree[0].slots[0].key}`);
      setExpanded(first);
    }
  }, [tree]);

  const toggleExpand = (key: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });

  const leafState = (shifts: Shift[]): "all" | "some" | "none" => {
    const selectable = shifts.filter((s) => !shiftState(s).full);
    const picked = selectable.filter((s) => selected.includes(s.id)).length;
    if (selectable.length > 0 && picked === selectable.length) return "all";
    if (picked > 0) return "some";
    return "none";
  };

  /* 选择语义：同一时段的岗位互斥（时间相同，报名系统也按冲突拒绝），
     所以时段内是单选；勾时段/日期 = 每个时段自动选第一个有空位的岗位。 */
  const firstAvailable = (shifts: Shift[]) => shifts.find((s) => !shiftState(s).full);

  const setSlot = (slotShifts: Shift[], pick: boolean) => {
    setSubmitError(null);
    setSelected((prev) => {
      const set = new Set(prev);
      for (const s of slotShifts) set.delete(s.id);
      if (pick) {
        const f = firstAvailable(slotShifts);
        if (f) set.add(f.id);
      }
      return [...set];
    });
  };

  const setDay = (day: DayGroup, pick: boolean) => {
    setSubmitError(null);
    setSelected((prev) => {
      const set = new Set(prev);
      for (const slot of day.slots) {
        for (const s of slot.shifts) set.delete(s.id);
        if (pick) {
          const f = firstAvailable(slot.shifts);
          if (f) set.add(f.id);
        }
      }
      return [...set];
    });
  };

  const pickLeaf = (slotShifts: Shift[], target: Shift) => {
    setSubmitError(null);
    setSelected((prev) => {
      const set = new Set(prev);
      const had = set.has(target.id);
      for (const s of slotShifts) set.delete(s.id);
      if (!had) set.add(target.id);
      return [...set];
    });
  };

  function submit() {
    const name = form.name.trim();
    const studentId = form.student_id.trim();
    const phone = form.phone.trim();
    if (name.length < 2) return setSubmitError("请填写姓名（与学籍一致）");
    if (!studentId) return setSubmitError("请填写学号");
    if (!/^1\d{10}$/.test(phone)) return setSubmitError("请填写 11 位手机号");
    if (selected.length === 0) return setSubmitError("请在下方选择至少一个场次");

    setSubmitting(true);
    setSubmitError(null);
    const payload: SignupPayload = { name, student_id: studentId, phone, shift_ids: selected };
    api
      .signup(activity.id, payload)
      .then(() => {
        setDone(true);
        window.scrollTo(0, 0);
      })
      .catch((e: Error) => {
        setSubmitError(e.message);
        api.getActivity(activity.id).then(setActivity).catch(() => {});
      })
      .finally(() => setSubmitting(false));
  }

  if (done)
    return (
      <main className="mx-auto max-w-xl px-4 py-14 text-center">
        <div className="rounded-3xl bg-white p-8 shadow-sm">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100 text-3xl">
            ✓
          </div>
          <h1 className="mt-4 text-xl font-bold text-gray-900">报名成功</h1>
          <p className="mt-2 text-sm text-gray-500">
            {form.name}，你已成功报名 {selected.length} 个场次。
            <br />
            活动前请在 QQ 群留意集合通知。
          </p>
        </div>
      </main>
    );

  return (
    <main className="mx-auto max-w-xl px-4 pb-28">
      <header className="pt-7">
        <h1 className="text-xl font-bold leading-snug text-gray-900">{activity.title}</h1>
        <p className="mt-1 text-[13px] text-gray-500">
          📍 {location}
          {activity.signup_deadline &&
            (() => {
              const d = new Date(activity.signup_deadline);
              return ` · ${d.getMonth() + 1}月${d.getDate()}日 ${p(d.getHours())}:${p(d.getMinutes())} 截止`;
            })()}
        </p>
      </header>

      {/* 信息收集（在最上面） */}
      <section className="mt-5 rounded-2xl bg-white p-5 shadow-sm">
        <h2 className="text-base font-semibold text-gray-900">填写志愿者信息</h2>
        <Field label="姓名" value={form.name} placeholder="与学籍一致"
               onChange={(v) => setForm({ ...form, name: v })} />
        <Field label="学号" value={form.student_id} placeholder="完整学号" inputMode="numeric"
               onChange={(v) => setForm({ ...form, student_id: v })} />
        <Field label="联系方式" value={form.phone} placeholder="11 位手机号" inputMode="numeric" maxLength={11}
               onChange={(v) => setForm({ ...form, phone: v })} />
      </section>

      {/* 四级复选树：地点 → 日期 → 时段 → 岗位 */}
      <section className="mt-6">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">选择场次（可多选）</h2>
          <span className="text-[13px] text-gray-500">
            已选 <b className="text-red-700">{selected.length}</b>
          </span>
        </div>

        <div className="mt-3 rounded-2xl bg-white shadow-sm">
          {/* 地点层：单一地点作为树根展示 */}
          <div className="flex items-center gap-2 border-b border-gray-100 px-4 py-3">
            <span className="text-[15px] font-semibold text-gray-900">📍 {location}</span>
          </div>

          {tree.map((day) => {
            const dayShifts = day.slots.flatMap((s) => s.shifts);
            const dState = leafState(dayShifts);
            const dOpen = expanded.has(`d:${day.key}`);
            return (
              <div key={day.key} className="border-b border-gray-100 last:border-0">
                {/* 日期行 */}
                <div className="flex items-center gap-3 px-4 py-3">
                  <Check state={dState} onChange={() => setDay(day, dState !== "all")} />
                  <button
                    type="button"
                    onClick={() => toggleExpand(`d:${day.key}`)}
                    className="flex flex-1 items-center justify-between text-left"
                  >
                    <span className="text-[15px] font-semibold text-gray-900">{day.label}</span>
                    <span className="text-[13px] text-gray-400">
                      {dOpen ? "收起 ▲" : `展开 ${day.slots.length} 个时段 ▼`}
                    </span>
                  </button>
                </div>

                {dOpen &&
                  day.slots.map((slot) => {
                    const sState = leafState(slot.shifts);
                    const sOpen = expanded.has(`s:${slot.key}`);
                    return (
                      <div key={slot.key} className="border-t border-gray-50 bg-gray-50/60">
                        {/* 时段行 */}
                        <div className="flex items-center gap-3 px-4 py-2.5 pl-8">
                          <Check size="sm" state={sState}
                                 onChange={() => setSlot(slot.shifts, sState === "none")} />
                          <button
                            type="button"
                            onClick={() => toggleExpand(`s:${slot.key}`)}
                            className="flex flex-1 items-center justify-between text-left"
                          >
                            <span className="text-[14px] font-medium text-gray-800">{slot.label}</span>
                            <span className="text-xs text-gray-400">{sOpen ? "收起 ▲" : "岗位 ▼"}</span>
                          </button>
                        </div>

                        {sOpen && (
                          <div className="pb-2 pl-12 pr-4">
                            {slot.shifts.map((s) => {
                              const { full, remaining } = shiftState(s);
                              const checked = selected.includes(s.id);
                              return (
                                <label
                                  key={s.id}
                                  className={`flex cursor-pointer items-center gap-2.5 rounded-lg px-2.5 py-2 ${
                                    checked ? "bg-red-50" : ""
                                  } ${full ? "opacity-45" : ""}`}
                                >
                                  <input
                                    type="checkbox"
                                    checked={checked}
                                    disabled={full}
                                    onChange={() => pickLeaf(slot.shifts, s)}
                                    className="h-4 w-4 flex-none accent-red-700"
                                  />
                                  <span className="flex-1 text-[14px] text-gray-800">{s.post_name}</span>
                                  <span className="text-xs text-gray-400">
                                    {full ? "已满" : `剩 ${remaining}`}
                                  </span>
                                </label>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
              </div>
            );
          })}
        </div>

        <p className="mt-2 px-1 text-xs text-gray-400">
          每个时段选一个岗位；勾选日期/时段会自动选第一个有空位的岗位，想换岗直接点别的岗位。
          同一天可报多个时段。
        </p>
      </section>

      {submitError && (
        <p className="mt-4 rounded-xl bg-red-100 p-3.5 text-sm font-medium text-red-800">
          {submitError}
        </p>
      )}

      {/* 底部固定提交条 */}
      <div className="fixed inset-x-0 bottom-0 border-t border-gray-100 bg-white/95 p-4 backdrop-blur">
        <div className="mx-auto flex max-w-xl items-center gap-3">
          <span className="flex-1 text-sm text-gray-500">
            已选 <b className="text-red-700">{selected.length}</b> 个场次
          </span>
          <button
            onClick={submit}
            disabled={submitting}
            className="rounded-xl bg-red-700 px-8 py-3 text-[15px] font-semibold text-white disabled:bg-gray-300"
          >
            {submitting ? "提交中…" : "提交报名"}
          </button>
        </div>
      </div>
    </main>
  );
}

function Field({
  label, value, placeholder, inputMode, maxLength, onChange,
}: {
  label: string; value: string; placeholder: string;
  inputMode?: "numeric" | "text"; maxLength?: number; onChange: (v: string) => void;
}) {
  return (
    <div className="mt-3">
      <label className="mb-1 block text-[13px] text-gray-600">{label}</label>
      <input
        value={value}
        placeholder={placeholder}
        inputMode={inputMode}
        maxLength={maxLength}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-xl border border-gray-300 bg-white px-3.5 py-2.5 text-base outline-none focus:border-red-600"
      />
    </div>
  );
}
