import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NanoBee Harness",
  description: "Control console for the long-running agent harness",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen overflow-hidden">
        {children}
      </body>
    </html>
  );
}
