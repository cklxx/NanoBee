import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NanoBee Harness",
  description: "Control console for the long-running agent harness",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <div className="max-w-6xl mx-auto py-8 px-4 space-y-6">
          <header className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold">NanoBee Harness</h1>
              <p className="text-sm text-slate-600">Tasks, timelines, features, and workspace files.</p>
            </div>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
