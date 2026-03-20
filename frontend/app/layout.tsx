import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import Link from 'next/link';
import { Github } from 'lucide-react';
import './globals.css';
import ThemeToggle from './components/ThemeToggle';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
});

export const metadata: Metadata = {
  title: 'Zia | News',
  description: 'Ultra-minimalist news dashboard.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable}`}>
      <body suppressHydrationWarning className="font-sans antialiased selection:bg-black selection:text-white dark:selection:bg-white dark:selection:text-black">
        <a href="#main-content" className="skip-link">
          Skip to content
        </a>
        <header className="fixed top-0 left-0 w-full z-50 px-6 py-4 flex justify-between items-center border-b border-[var(--border)] bg-[var(--bg)]">
          <div className="flex items-center gap-4">
            <Link href="/" className="text-lg font-bold tracking-tighter uppercase hover:opacity-100 opacity-100 transition-opacity">
              Zia
            </Link>
          </div>
          <ThemeToggle />
        </header>
        <main id="main-content" className="pt-24 min-h-screen px-6">
          {children}
        </main>
        <footer className="px-6 py-12 border-t border-[var(--border)] text-[10px] uppercase tracking-[0.2em] opacity-40 flex justify-between items-center">
          <p>© 2026 Zia. Minimalist News Engine.</p>
          <a 
            href="https://github.com" 
            target="_blank" 
            rel="noopener noreferrer"
            className="hover:opacity-100 transition-opacity flex items-center gap-2"
          >
            <Github size={14} />
            <span>Github</span>
          </a>
        </footer>
      </body>
    </html>
  );
}