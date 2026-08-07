import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "勤怠管理",
  description: "AWS 学習用勤怠管理アプリ",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
