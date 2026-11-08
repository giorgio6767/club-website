"use client";

/* 单页入口：只有一个开放活动时自动直入报名流程（用户要求"所有东西压缩进一个页面"）。
   多个活动时退化为列表；无活动显示空态。 */

import { useEffect, useState } from "react";
import Link from "next/link";
import SignupFlow from "@/components/SignupFlow";
import { api, type Activity, type ActivitySummary } from "@/lib/api";

export default function Home() {
  const [activity, setActivity] = useState<Activity | null>(null);
  const [others, setOthers] = useState<ActivitySummary[]>([]);
  const [state, setState] = useState<"loading" | "error" | "empty" | "ready">("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .listOpenActivities()
      .then(async (list) => {
        if (list.length === 0) return setState("empty");
        const first = await api.getActivity(list[0].id);
        setActivity(first);
        setOthers(list.slice(1));
        setState("ready");
      })
      .catch((e: Error) => {
        setError(e.message);
        setState("error");
      });
  }, []);

  if (state === "loading")
    return <Center>加载中…</Center>;
  if (state === "error")
    return <Center title="加载失败" body={error} />;
  if (state === "empty" || activity === null)
    return (
      <Center title="当前没有开放报名的活动">
        请在 QQ 群留意通知
        <br />
        <span className="text-xs text-gray-400">红十字会学生分会</span>
      </Center>
    );

  return (
    <div>
      <SignupFlow activity={activity} />
      {others.length > 0 && (
        <section className="mx-auto -mt-16 max-w-xl px-4 pb-24">
          <h2 className="text-sm font-semibold text-gray-600">其他开放报名的活动</h2>
          <div className="mt-2 space-y-2">
            {others.map((a) => (
              <Link key={a.id} href={`/activities/${a.id}`}
                    className="block rounded-xl bg-white p-3.5 text-sm font-medium text-gray-800 shadow-sm">
                {a.title} →
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function Center({ title, body, children }: { title?: string; body?: string; children?: React.ReactNode }) {
  return (
    <main className="mx-auto max-w-xl px-4 py-24 text-center">
      {title && <h1 className="text-lg font-bold text-gray-900">{title}</h1>}
      {body && <p className="mt-2 text-sm text-gray-500">{body}</p>}
      {children}
    </main>
  );
}
