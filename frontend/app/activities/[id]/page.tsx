"use client";

/* 活动详情 + 场次报名页（手机 QQ 场景优先）。
   交互与临时静态页一致：多选场次（满员置灰）、重叠/重复/满员错误原样展示后端文案。 */

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, fmtShiftTime, shiftState, type Activity, type SignupPayload } from "@/lib/api";

export default function ActivitySignupPage() {
  const { id } = useParams<{ id: string }>();
  const [activity, setActivity] = useState<Activity | null>(null);
  const [error, setError] = useState<string | null>(null); // 加载错误
  const [selected, setSelected] = useState<number[]>([]);
  const [form, setForm] = useState({ name: "", student_id: "", college: "", phone: "" });
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    api
      .getActivity(Number(id))
      .then(setActivity)
      .catch((e: Error) => setError(e.message));
  }, [id]);

  function toggle(shiftId: number, full: boolean) {
    if (full) return;
    setSubmitError(null);
    setSelected((prev) =>
      prev.includes(shiftId) ? prev.filter((x) => x !== shiftId) : [...prev, shiftId],
    );
  }

  async function submit() {
    if (selected.length === 0) return setSubmitError("请至少选择一个场次");
    if (form.name.trim().length < 2) return setSubmitError("请填写姓名（与学籍一致）");
    if (!form.student_id.trim()) return setSubmitError("请填写学号");
    if (form.college.trim().length < 2) return setSubmitError("请填写学院");
    if (!/^1\d{10}$/.test(form.phone.trim())) return setSubmitError("请填写 11 位手机号");

    setSubmitting(true);
    setSubmitError(null);
    const payload: SignupPayload = {
      name: form.name.trim(),
      student_id: form.student_id.trim(),
      college: form.college.trim(),
      phone: form.phone.trim(),
      shift_ids: selected,
    };
    try {
      await api.signup(Number(id), payload);
      setDone(true);
      window.scrollTo(0, 0);
    } catch (e) {
      setSubmitError((e as Error).message);
      // 重新拉取，刷新名额状态（例如刚被人报满）
      api.getActivity(Number(id)).then(setActivity).catch(() => {});
    } finally {
      setSubmitting(false);
    }
  }

  if (error)
    return <Notice title="加载失败" body={error} />;
  if (!activity)
    return <Notice title="" body="加载中…" />;

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
      <header className="pt-8">
        <h1 className="text-xl font-bold text-gray-900">{activity.title}</h1>
        {activity.description && (
          <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-gray-500">
            {activity.description}
          </p>
        )}
      </header>

      <section className="mt-6">
        <h2 className="text-base font-semibold text-gray-900">选择场次（可多选）</h2>
        <div className="mt-3 space-y-2.5">
          {activity.shifts.map((s) => {
            const { full, remaining } = shiftState(s);
            const checked = selected.includes(s.id);
            return (
              <label
                key={s.id}
                className={`flex cursor-pointer items-start gap-3 rounded-2xl border p-4 transition ${
                  checked ? "border-red-600 bg-red-50" : "border-gray-200 bg-white"
                }`}
                onClick={() => toggle(s.id, full)}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  disabled={full}
                  onChange={() => {}}
                  className="mt-1 h-4.5 w-4.5 flex-none accent-red-700"
                />
                <span>
                  <span
                    className={`block text-[15px] font-semibold ${
                      full ? "text-gray-400" : "text-gray-900"
                    }`}
                  >
                    {s.post_name}
                    <span className="ml-2 text-xs font-normal">
                      {full ? "（已满）" : `（剩 ${remaining} 名额）`}
                    </span>
                  </span>
                  <span className="mt-0.5 block text-[13px] text-gray-500">
                    {fmtShiftTime(s.start_time, s.end_time)}
                    {s.location && ` · ${s.location}`}
                  </span>
                </span>
              </label>
            );
          })}
        </div>
      </section>

      <section className="mt-8 rounded-2xl bg-white p-5 shadow-sm">
        <h2 className="text-base font-semibold text-gray-900">填写报名信息</h2>
        <Field label="姓名" value={form.name} placeholder="与学籍一致"
               onChange={(v) => setForm({ ...form, name: v })} />
        <Field label="学号" value={form.student_id} placeholder="完整学号" inputMode="numeric"
               onChange={(v) => setForm({ ...form, student_id: v })} />
        <Field label="学院" value={form.college} placeholder="如：材料学院"
               onChange={(v) => setForm({ ...form, college: v })} />
        <Field label="手机号" value={form.phone} placeholder="11 位手机号" inputMode="numeric" maxLength={11}
               onChange={(v) => setForm({ ...form, phone: v })} />
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

function Notice({ title, body }: { title: string; body: string }) {
  return (
    <main className="mx-auto max-w-xl px-4 py-20 text-center">
      {title && <h1 className="text-lg font-bold text-gray-900">{title}</h1>}
      <p className="mt-2 text-sm text-gray-500">{body}</p>
    </main>
  );
}
