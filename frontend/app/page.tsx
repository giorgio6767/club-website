/* M0 占位首页：M2 按需求文档拆分页面结构
   （首页 / 社团介绍 / 新闻 / 活动 / 报名 / 问答浮窗）。 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

export default function Home() {
  return (
    <main className="mx-auto max-w-3xl px-4 py-16 text-center">
      <h1 className="text-3xl font-bold text-red-700 md:text-4xl">校红十字会学生分会</h1>
      <p className="mt-4 text-gray-600">
        网站搭建中。后端接口：<code className="rounded bg-red-100 px-1">{API_BASE}</code>
      </p>
      <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
        <a
          href={`${API_BASE}/docs`}
          className="rounded-lg bg-red-700 px-6 py-3 text-white hover:bg-red-800"
        >
          查看后端接口文档
        </a>
      </div>
    </main>
  );
}
