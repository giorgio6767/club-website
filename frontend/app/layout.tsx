import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "校红十字会学生分会",
  description: "活动发布、志愿服务报名与急救知识问答",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="bg-red-50 text-gray-900 antialiased">{children}</body>
    </html>
  );
}
