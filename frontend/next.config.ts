import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 后端接口地址：开发时后端跑 8000，部署后换成服务器域名
  env: {
    NEXT_PUBLIC_API_BASE: process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000",
  },
};

export default nextConfig;
