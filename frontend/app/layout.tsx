import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CivicFix",
  description: "AI-powered civic issue reporting and routing platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
