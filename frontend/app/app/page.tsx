"use client";

import { useEffect, useMemo, useState } from "react";
import ThemeToggle from "../components/ThemeToggle";

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

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const LANG_OPTIONS = [
  { label: "Español (ES)", value: "es-ES" },
  { label: "Inglés (US)", value: "en-US" }
];

const IconFilter = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
    <path d="M4 5h16l-6 7v5l-4 2v-7L4 5z" />
  </svg>
);

const IconMail = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
    <path d="M4 6h16v12H4z" />
    <path d="M4 7l8 6 8-6" />
  </svg>
);

const IconSpark = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
    <path d="M12 2l2.2 5.4L20 9l-5.8 1.6L12 16l-2.2-5.4L4 9l5.8-1.6L12 2z" />
  </svg>
);

export default function Dashboard() {
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [news, setNews] = useState<Article[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [summaryMap, setSummaryMap] = useState<Record<string, string>>({});
  const [sendEmail, setSendEmail] = useState<string>("");
  const [subEmail, setSubEmail] = useState<string>("");
  const [subCategory, setSubCategory] = useState<string>("research");
  const [lang, setLang] = useState<string>(LANG_OPTIONS[0].value);
  const [message, setMessage] = useState<string>("");

  const visibleNews = useMemo(() => news, [news]);

  useEffect(() => {
    const init = async () => {
      try {
        const catRes = await fetch(`${API_BASE}/categories`);
        if (catRes.ok) {
          const data = await catRes.json();
          setCategories(data);
          if (data.length > 0) {
            setSubCategory(data[0]);
          }
        }
      } catch (err) {
        console.error(err);
      }
    };

    init();
  }, []);

  useEffect(() => {
    const loadNews = async () => {
      setLoading(true);
      const params = new URLSearchParams();
      if (selectedCategory !== "all") {
        params.set("category", selectedCategory);
      }
      if (lang) {
        params.set("lang", lang);
      }
      const url = `${API_BASE}/news${params.toString() ? `?${params}` : ""}`;
      try {
        const res = await fetch(url);
        if (!res.ok) {
          throw new Error("No se pudo cargar noticias");
        }
        const data = await res.json();
        setNews(data.items || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadNews();
  }, [selectedCategory, lang]);

  const handleSummary = async (article: Article) => {
    if (summaryMap[article.url]) return;
    try {
      const res = await fetch(`${API_BASE}/summary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ article })
      });
      const data = await res.json();
      setSummaryMap((prev) => ({ ...prev, [article.url]: data.summary }));
    } catch (err) {
      console.error(err);
    }
  };

  const handleSend = async (article: Article) => {
    if (!sendEmail) {
      setMessage("Ingresa tu correo para enviar la noticia.");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: sendEmail, article })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "No se pudo enviar");
      }
      setMessage("Noticia en cola para envío.");
    } catch (err: any) {
      setMessage(err.message || "Error al enviar.");
    }
  };

  const handleSubscribe = async () => {
    if (!subEmail) {
      setMessage("Ingresa tu correo para suscribirte.");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/subscribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: subEmail, category: subCategory })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "No se pudo suscribir");
      }
      const data = await res.json();
      if (data.confirmed) {
        setMessage("Suscripción activa. Recibirás noticias diarias.");
      } else {
        setMessage("Revisa tu correo para confirmar la suscripción.");
      }
    } catch (err: any) {
      setMessage(err.message || "Error al suscribirte.");
    }
  };

  return (
    <main>
      <a className="skip-link" href="#dashboard">
        Saltar al contenido
      </a>
      <div className="page">
        <div className="container" id="dashboard">
          <nav className="nav glass card reveal">
            <div className="logo">
              <div className="logo-icon">Z</div>
              <span>Zia.AI Dashboard</span>
              <span className="badge floating">Actualizado hoy</span>
            </div>
            <div className="nav-actions">
              <a className="button ghost" href="/">
                Volver al inicio
              </a>
              <ThemeToggle />
            </div>
          </nav>

          <section className="section-grid">
            <div className="glass card reveal" style={{ animationDelay: "80ms" }}>
              <h3 className="card-title">Filtros inteligentes</h3>
              <p className="subtitle">Explora por categoría y lenguaje.</p>
              <div className="filters" aria-label="Filtros de categoría">
                <button
                  className={`chip ${selectedCategory === "all" ? "active" : ""}`}
                  onClick={() => setSelectedCategory("all")}
                  type="button"
                >
                  Todas
                </button>
                {categories.map((cat) => (
                  <button
                    key={cat}
                    className={`chip ${selectedCategory === cat ? "active" : ""}`}
                    onClick={() => setSelectedCategory(cat)}
                    type="button"
                  >
                    {cat}
                  </button>
                ))}
              </div>
              <div style={{ marginTop: "12px" }}>
                <label className="subtitle" htmlFor="lang">
                  Idioma
                </label>
                <select
                  className="input"
                  id="lang"
                  value={lang}
                  onChange={(event) => setLang(event.target.value)}
                >
                  {LANG_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="glass card reveal" style={{ animationDelay: "120ms" }}>
              <h3 className="card-title">Suscripción diaria</h3>
              <p className="subtitle">Recibe solo el tipo de noticias que te interesa.</p>
              <input
                className="input"
                placeholder="Tu correo"
                type="email"
                value={subEmail}
                onChange={(event) => setSubEmail(event.target.value)}
              />
              <select
                className="input"
                value={subCategory}
                onChange={(event) => setSubCategory(event.target.value)}
              >
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
              <button className="button primary" onClick={handleSubscribe} type="button">
                Suscribirme
              </button>
            </div>
          </section>

          <section className="glass card reveal" style={{ animationDelay: "160ms" }}>
            <div className="meta">
              <span className="meta-pill"><span className="icon" aria-hidden="true"><IconMail /></span> Envío directo</span>
              <span className="meta-pill"><span className="icon" aria-hidden="true"><IconSpark /></span> Resumen inmediato</span>
            </div>
            <h3 className="card-title">Envía una noticia a tu correo</h3>
            <p className="subtitle">Ideal para compartir con tu equipo o archivar insights.</p>
            <input
              className="input"
              placeholder="correo@dominio.com"
              type="email"
              value={sendEmail}
              onChange={(event) => setSendEmail(event.target.value)}
            />
            {message ? (
              <p className="notification" role="status" aria-live="polite">
                {message}
              </p>
            ) : null}
          </section>

          <section className="glass card reveal" style={{ animationDelay: "200ms" }}>
            <div className="meta">
              <span className="meta-pill"><span className="icon" aria-hidden="true"><IconFilter /></span> Curado</span>
            </div>
            <h3 className="card-title">Noticias de hoy</h3>
            <p className="subtitle">Siempre incluye el enlace original para verificar la fuente.</p>
            {loading ? <p className="notification">Cargando...</p> : null}
          </section>

          <section className="news-grid" aria-busy={loading}>
            {visibleNews.map((article, index) => (
              <article
                className="glass card card-lift reveal"
                style={{ animationDelay: `${240 + index * 40}ms` }}
                key={article.url}
              >
                <div className="meta">
                  <span>{article.source_domain || article.source}</span>
                  {article.published_at ? (
                    <span>{new Date(article.published_at).toLocaleString()}</span>
                  ) : null}
                  {article.trust_score !== null && article.trust_score !== undefined ? (
                    <span className="meta-pill">
                      Confianza {Math.round(article.trust_score * 100)}%
                    </span>
                  ) : null}
                </div>
                <h2 className="card-title">{article.title}</h2>
                <p className="subtitle">{article.description}</p>
                <div className="actions">
                  <a className="button" href={article.url} target="_blank" rel="noreferrer">
                    Ver fuente original
                  </a>
                  <button
                    className="button"
                    onClick={() => handleSummary(article)}
                    type="button"
                  >
                    Generar resumen
                  </button>
                  <button
                    className="button primary"
                    onClick={() => handleSend(article)}
                    type="button"
                  >
                    Enviar por correo
                  </button>
                </div>
                {summaryMap[article.url] ? (
                  <div className="glass card">
                    <strong>Resumen</strong>
                    <p className="subtitle">{summaryMap[article.url]}</p>
                  </div>
                ) : null}
              </article>
            ))}
          </section>
        </div>
      </div>
    </main>
  );
}
