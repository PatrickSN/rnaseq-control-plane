import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "rnaseq-control-plane",
  description: "Run and monitor RNA-Seq Nextflow pipelines"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <header className="topbar">
            <Link className="brand" href="/pipelines">
              rnaseq-control-plane
            </Link>
            <Link href="/pipelines">Pipelines</Link>
            <Link href="/runs/new">New run</Link>
            <Link href="/login">Login</Link>
          </header>
          <main className="content">{children}</main>
        </div>
      </body>
    </html>
  );
}

