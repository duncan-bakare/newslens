import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NewsLens — Understand what you read",
  description: "AI-powered news bias and credibility analyser",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}