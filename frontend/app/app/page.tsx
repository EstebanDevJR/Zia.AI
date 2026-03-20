'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Loader2,
  ArrowRight,
  ExternalLink,
  Mail,
  Shield
} from 'lucide-react';

type Article = {
  title: string;
  description?: string | null;
  url: string;
  source: string;
  published_at?: string | null;
  image_url?: string | null;
  category?: string | null;
  source_domain?: string | null;
  trust_score?: number | null;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Dashboard() {
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [lang, setLang] = useState<string>('es-ES');
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(false);
  const [summaries, setSummaries] = useState<Record<string, string>>({});
  const [summarizing, setSummarizing] = useState<Record<string, boolean>>({});
  const [status, setStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [email, setEmail] = useState('');
  const [subEmail, setSubEmail] = useState('');
  const [subCategory, setSubCategory] = useState('');

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const res = await fetch(`${API_URL}/categories`);
        if (!res.ok) throw new Error('Error');
        const data = await res.json();
        setCategories(data);
        if (data.length > 0) {
          setSelectedCategory(data[0]);
          setSubCategory(data[0]);
        }
      } catch (err) {
        console.error(err);
      }
    };
    fetchCategories();
  }, []);

  const fetchNews = useCallback(async () => {
    if (!selectedCategory) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/news?category=${selectedCategory}&lang=${lang}`);
      if (!res.ok) throw new Error('Error');
      const data = await res.json();
      setArticles(data.items);
    } catch (err) {
      console.error(err);
      showStatus('error', 'Error loading news.');
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, lang]);

  useEffect(() => {
    fetchNews();
  }, [fetchNews]);

  const showStatus = (type: 'success' | 'error', message: string) => {
    setStatus({ type, message });
    setTimeout(() => setStatus(null), 3000);
  };

  const generateSummary = async (article: Article) => {
    if (summaries[article.url]) return;
    setSummarizing(prev => ({ ...prev, [article.url]: true }));
    try {
      const res = await fetch(`${API_URL}/summary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ article }),
      });
      if (!res.ok) throw new Error('Error');
      const data = await res.json();
      setSummaries(prev => ({ ...prev, [article.url]: data.summary }));
    } catch (err) {
      showStatus('error', 'Summary failed.');
    } finally {
      setSummarizing(prev => ({ ...prev, [article.url]: false }));
    }
  };

  const sendByEmail = async (article: Article) => {
    if (!email) {
      showStatus('error', 'Enter email first.');
      return;
    }
    try {
      const res = await fetch(`${API_URL}/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, article }),
      });
      if (!res.ok) throw new Error('Error');
      showStatus('success', 'Sent.');
    } catch (err) {
      showStatus('error', 'Send failed.');
    }
  };

  const subscribe = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subEmail || !subCategory) return;
    try {
      const res = await fetch(`${API_URL}/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: subEmail, category: subCategory }),
      });
      if (!res.ok) throw new Error('Error');
      const data = await res.json();
      showStatus('success', data.confirmed ? 'Subscribed.' : 'Check email.');
      setSubEmail('');
    } catch (err) {
      showStatus('error', 'Subscription failed.');
    }
  };

  return (
    <div className="max-w-5xl mx-auto py-12 animate-fade">
      {/* Status */}
      <div aria-live="polite" className="fixed bottom-12 right-12 z-50">
        <AnimatePresence>
          {status && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              className="px-6 py-3 border border-black dark:border-white bg-white dark:bg-black font-bold uppercase text-xs tracking-widest"
            >
              {status.message}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <header className="mb-24">
        <h1 className="text-4xl font-bold tracking-tighter uppercase mb-2">Feed</h1>
        <div className="h-px bg-black dark:bg-white w-12" />
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-24">
        <div className="space-y-24">
          {/* Controls */}
          <div className="flex flex-wrap gap-12 text-[10px] font-bold uppercase tracking-[0.2em] opacity-40">
            <div className="flex items-center gap-4">
              <span>Category</span>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="bg-transparent border-none focus:ring-0 p-0 cursor-pointer uppercase"
              >
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-4">
              <span>Language</span>
              <select
                value={lang}
                onChange={(e) => setLang(e.target.value)}
                className="bg-transparent border-none focus:ring-0 p-0 cursor-pointer uppercase"
              >
                <option value="es-ES">ES</option>
                <option value="en-US">EN</option>
              </select>
            </div>
          </div>

          {/* Articles */}
          <div className="space-y-32">
            {loading ? (
              <div className="flex items-center gap-4 opacity-40">
                <Loader2 className="animate-spin" size={16} />
                <span className="text-xs uppercase tracking-widest">Loading...</span>
              </div>
            ) : (
              articles.map((article) => (
                <article key={article.url} className="group">
                  <div className="flex flex-col gap-8">
                    <div className="flex items-center justify-between text-[10px] uppercase tracking-[0.2em] opacity-40">
                      <div className="flex items-center gap-4">
                        <span>{article.source_domain || article.source}</span>
                        <span>/</span>
                        <span>{article.published_at ? new Date(article.published_at).toLocaleDateString() : 'Now'}</span>
                      </div>
                      {article.trust_score && (
                        <div className="flex items-center gap-2">
                          <Shield size={10} />
                          <span>{Math.round(article.trust_score * 100)}%</span>
                        </div>
                      )}
                    </div>
                    
                    <h2 className="text-3xl font-bold tracking-tight leading-tight group-hover:underline underline-offset-8 decoration-1">
                      {article.title}
                    </h2>
                    
                    <p className="opacity-60 text-sm leading-relaxed max-w-2xl">
                      {article.description}
                    </p>

                    <AnimatePresence>
                      {summaries[article.url] && (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          className="p-8 border border-black dark:border-white text-sm leading-relaxed"
                        >
                          <span className="font-bold uppercase text-[10px] tracking-widest block mb-4">Summary</span>
                          {summaries[article.url]}
                        </motion.div>
                      )}
                    </AnimatePresence>

                    <div className="flex flex-wrap gap-8 pt-4">
                      <a
                        href={article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[10px] font-bold uppercase tracking-widest flex items-center gap-2 hover:opacity-100 opacity-40 transition-opacity"
                      >
                        Source <ExternalLink size={10} />
                      </a>
                      <button
                        onClick={() => generateSummary(article)}
                        disabled={summarizing[article.url] || !!summaries[article.url]}
                        className="text-[10px] font-bold uppercase tracking-widest flex items-center gap-2 hover:opacity-100 opacity-40 transition-opacity disabled:opacity-20"
                      >
                        {summarizing[article.url] ? '...' : summaries[article.url] ? 'Done' : 'Summarize'}
                      </button>
                      <button
                        onClick={() => sendByEmail(article)}
                        className="text-[10px] font-bold uppercase tracking-widest flex items-center gap-2 hover:opacity-100 opacity-40 transition-opacity"
                      >
                        Send <Mail size={10} />
                      </button>
                    </div>
                  </div>
                </article>
              ))
            )}
          </div>
        </div>

        {/* Sidebar */}
        <aside className="space-y-24">
          <section>
            <h3 className="text-[10px] font-bold uppercase tracking-[0.3em] mb-8 opacity-40">Subscribe</h3>
            <form onSubmit={subscribe} className="space-y-8">
              <input
                type="email"
                placeholder="EMAIL"
                required
                value={subEmail}
                onChange={(e) => setSubEmail(e.target.value)}
                className="w-full bg-transparent border-b border-black dark:border-white py-2 text-xs outline-none uppercase tracking-widest"
              />
              <select
                value={subCategory}
                onChange={(e) => setSubCategory(e.target.value)}
                className="w-full bg-transparent border-b border-black dark:border-white py-2 text-xs outline-none uppercase tracking-widest"
              >
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
              <button
                type="submit"
                className="btn-minimal-inverse w-full text-[10px] font-bold uppercase tracking-widest"
              >
                Join
              </button>
            </form>
          </section>

          <section>
            <h3 className="text-[10px] font-bold uppercase tracking-[0.3em] mb-8 opacity-40">Destination</h3>
            <input
              type="email"
              placeholder="TARGET EMAIL"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-transparent border-b border-black dark:border-white py-2 text-xs outline-none uppercase tracking-widest"
            />
          </section>

          <section className="pt-12 border-t border-black dark:border-white">
            <p className="text-[10px] opacity-40 leading-relaxed uppercase tracking-widest">
              Strict verification. <br />
              Zero noise. <br />
              Pure information.
            </p>
          </section>
        </aside>
      </div>
    </div>
  );
}
