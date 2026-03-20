"use client";

import ThemeToggle from "./components/ThemeToggle";

const IconSpark = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
    <path d="M12 2l2.2 5.4L20 9l-5.8 1.6L12 16l-2.2-5.4L4 9l5.8-1.6L12 2z" />
  </svg>
);

const IconShield = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
    <path d="M12 3l7 3v6c0 5-3.8 8.6-7 9-3.2-.4-7-4-7-9V6l7-3z" />
  </svg>
);

const IconMail = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
    <path d="M4 6h16v12H4z" />
    <path d="M4 7l8 6 8-6" />
  </svg>
);

const IconArrow = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
    <path d="M5 12h14" />
    <path d="M13 6l6 6-6 6" />
  </svg>
);

export default function Home() {
  return (
    <main>
      <a className="skip-link" href="#contenido">
        Saltar al contenido
      </a>
      <div className="page">
        <div className="container" id="contenido">
          <nav className="nav glass card reveal">
            <div className="logo">
              <div className="logo-icon">Z</div>
              <span>Zia.AI</span>
              <span className="badge floating">Live · IA diaria</span>
            </div>
            <div className="nav-actions">
              <a className="button ghost" href="/app">
                Ir al dashboard
              </a>
              <ThemeToggle />
            </div>
          </nav>

          <section className="hero">
            <div className="glass card card-lift reveal" style={{ animationDelay: "80ms" }}>
              <span className="badge">Pulse de IA para equipos modernos</span>
              <h1 className="hero-title">
                Noticias de IA en un vistazo <span>verificado</span>.
              </h1>
              <p className="subtitle">
                Monitorea lanzamientos, investigación, regulación y seguridad con un flujo de
                lectura que prioriza claridad y confiabilidad.
              </p>
              <div className="hero-actions">
                <a className="button primary" href="/app">
                  Entrar al dashboard <span className="icon" aria-hidden="true"><IconArrow /></span>
                </a>
                <a className="button" href="#como-funciona">
                  Ver cómo funciona
                </a>
              </div>
            </div>

            <div className="glass card card-lift reveal" style={{ animationDelay: "140ms" }}>
              <h3 className="section-title">Qué obtienes</h3>
              <div className="meta">
                <span className="meta-pill"><span className="icon" aria-hidden="true"><IconShield /></span> Fuentes verificadas</span>
                <span className="meta-pill"><span className="icon" aria-hidden="true"><IconSpark /></span> Resumen instantáneo</span>
                <span className="meta-pill"><span className="icon" aria-hidden="true"><IconMail /></span> Envíos diarios</span>
              </div>
              <p className="subtitle">
                Curación de noticias con Firecrawl, respaldo con DuckDuckGo y enlaces originales
                para que valides cada dato.
              </p>
              <div className="stats">
                <div className="stat">
                  <div className="stat-value">20+</div>
                  <div className="stat-label">Fuentes confiables</div>
                </div>
                <div className="stat">
                  <div className="stat-value">3-4</div>
                  <div className="stat-label">Frases por resumen</div>
                </div>
                <div className="stat">
                  <div className="stat-value">100%</div>
                  <div className="stat-label">Links verificables</div>
                </div>
              </div>
            </div>
          </section>

          <section className="feature-grid" id="como-funciona">
            <div className="glass card card-lift reveal" style={{ animationDelay: "200ms" }}>
              <div className="meta">
                <span className="meta-pill">Paso 1</span>
              </div>
              <h3 className="card-title">Curamos las fuentes</h3>
              <p className="subtitle">
                Solo dominios verificados y enlaces originales para garantizar transparencia.
              </p>
            </div>
            <div className="glass card card-lift reveal" style={{ animationDelay: "240ms" }}>
              <div className="meta">
                <span className="meta-pill">Paso 2</span>
              </div>
              <h3 className="card-title">Sintetizamos señales</h3>
              <p className="subtitle">
                Resúmenes claros con contexto para equipos de producto y estrategia.
              </p>
            </div>
            <div className="glass card card-lift reveal" style={{ animationDelay: "280ms" }}>
              <div className="meta">
                <span className="meta-pill">Paso 3</span>
              </div>
              <h3 className="card-title">Entregamos por canal</h3>
              <p className="subtitle">
                Newsletter diaria y dashboard en tiempo real para tus decisiones.
              </p>
            </div>
          </section>

          <section className="glass card reveal" style={{ animationDelay: "320ms" }}>
            <h3 className="section-title">Diseñado para equipos modernos</h3>
            <p className="subtitle">
              CEOs, product managers y equipos de innovación usan Zia.AI para mantenerse
              al día sin ruido. Entra al dashboard y personaliza tu flujo en segundos.
            </p>
            <div className="hero-actions">
              <a className="button primary" href="/app">
                Abrir dashboard
              </a>
              <a className="button" href="mailto:hello@zia.ai">
                Hablar con ventas
              </a>
            </div>
          </section>

          <footer className="footer">
            Zia.AI · Noticias diarias de IA para equipos que construyen el futuro.
          </footer>
        </div>
      </div>
    </main>
  );
}
