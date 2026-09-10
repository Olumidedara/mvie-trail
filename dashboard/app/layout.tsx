import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Movie StoryBot",
  description: "Automated storytelling videos from royalty-free film sources",
};

const NAV = [
  { href: "/", label: "Home" },
  { href: "/library", label: "Library" },
  { href: "/settings", label: "Settings" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <header className="border-b border-line bg-panel/60 backdrop-blur sticky top-0 z-10">
          <div className="mx-auto max-w-5xl px-4 py-3 flex items-center justify-between">
            <Link href="/" className="font-bold tracking-tight text-lg">
              🎬 Movie <span className="text-accent">StoryBot</span>
            </Link>
            <nav className="flex items-center gap-1">
              {NAV.map((n) => (
                <Link
                  key={n.href}
                  href={n.href}
                  className="px-3 py-1.5 rounded-lg text-sm text-zinc-300 hover:text-white hover:bg-line/50 transition"
                >
                  {n.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
        <footer className="border-t border-line mt-12">
          <div className="mx-auto max-w-5xl px-4 py-6 text-xs text-zinc-500">
            Posting is manual by design. Generated videos are royalty-free derived works.
          </div>
        </footer>
      </body>
    </html>
  );
}