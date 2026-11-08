"use client";

/* 活动报名页：与首页共用 SignupFlow 单页流程。QR/链接两种入口都落到同一体验。 */

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import SignupFlow from "@/components/SignupFlow";
import { api, type Activity } from "@/lib/api";

export default function ActivitySignupPage() {
  const { id } = useParams<{ id: string }>();
  const [activity, setActivity] = useState<Activity | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getActivity(Number(id))
      .then(setActivity)
      .catch((e: Error) => setError(e.message));
  }, [id]);

  if (error) return <Center title="加载失败" body={error} />;
  if (!activity) return <Center title="加载中…" />;
  return <SignupFlow activity={activity} />;
}

function Center({ title, body }: { title?: string; body?: string }) {
  return (
    <main className="mx-auto max-w-xl px-4 py-24 text-center">
      {title && <h1 className="text-lg font-bold text-gray-900">{title}</h1>}
      <p className="mt-2 text-sm text-gray-500">{body}</p>
    </main>
  );
}
