import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "证据时效词汇演练",
  description: "一个无指导、无上传、无自动判分的 Evidence Freshness 词汇演练页面。",
  robots: {
    index: false,
    follow: false,
  },
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
