"use client";

/* 官网单页（MVP）：社团名 + 一句话介绍 + 正在报名的活动入口。
   等报名期结束后再扩成完整官网（介绍页/新闻，见需求文档 M3 后）。 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type ActivitySummary } from "@/lib/api";

export default function Home() {
  const [activities, setActivities] = useState<ActivitySummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listOpenActivities()
      .then(setActivities)
      .catch((e: Error) => setError(e.message));
  }, []);

  return (
    <main className="mx-auto min-h-screen max-w-xl px-4 pb-16">
      {/* 头部 */}
      <header className="pt-10 text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-700 text-2xl text-white">
          +{/* 红十字标识占位：正式 logo 由社团提供后替换 */}
        </div>
        <h1 className="mt-3 text-2xl font-bold text-red-700">校红十字会学生分会</h1>
        <p className="mt-2 text-sm text-gray-500">人道 · 博爱 · 奉献</p>
      </header>

      {/* 正在报名 */}
      <section className="mt-10">
        <h2 className="text-lg font-semibold text-gray-900">正在报名</h2>

        {error && (
          <p className="mt-4 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>
        )}

        {activities?.length === 0 && (
          <p className="mt-4 rounded-xl bg-white p-5 text-center text-sm text-gray-500 shadow-sm">
            当前没有开放报名的活动，请在 QQ 群留意通知
          </p>
        )}

        <div className="mt-4 space-y-3">
          {activities?.map((a) => (
            <Link
              key={a.id}
              href={`/activities/${a.id}`}
              className="block rounded-2xl bg-white p-5 shadow-sm transition active:scale-[0.99]"
            >
              <h3 className="font-semibold text-gray-900">{a.title}</h3>
              {a.description && (
                <p className="mt-1 line-clamp-2 text-sm text-gray-500">{a.description}</p>
              )}
              <span className="mt-3 inline-block rounded-full bg-red-600 px-4 py-1.5 text-sm font-medium text-white">
                立即报名 →
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* 社团介绍占位（正式文案待社团提供） */}
      <section className="mt-12 rounded-2xl bg-white p-5 shadow-sm">
        <h2 className="text-base font-semibold text-gray-900">关于我们</h2>
        <p className="mt-2 text-sm leading-relaxed text-gray-500">
          校红十字会学生分会以“人道、博爱、奉献”为宗旨，组织无偿献血志愿服务、
          急救知识普及与校园公益活动。欢迎同学们关注 QQ 群通知，加入我们。
        </p>
      </section>

      <footer className="mt-12 text-center text-xs text-gray-400">
        © {new Date().getFullYear()} 校红十字会学生分会
      </footer>
    </main>
  );
}
