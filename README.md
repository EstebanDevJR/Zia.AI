# Zia.AI

Plataforma ultra minimalista para noticias diarias de IA, con filtros, resúmenes automáticos, envío por correo y suscripciones diarias. Frontend en Next.js y backend en FastAPI con orquestación de agentes (LangGraph) y SQLite.

## Estructura
- frontend/  (Next.js)
- backend/   (FastAPI + LangGraph)
- docker-compose.yml

## Requisitos
- Docker y Docker Compose
- (Opcional) claves de API para Firecrawl y resumen
- Redis (incluido en docker-compose para cola de trabajos)

## Fuentes confiables
La API consulta Firecrawl Search con una lista de dominios permitidos (`FIRECRAWL_ALLOWED_DOMAINS`). La UI siempre enlaza a la fuente original.

Si Firecrawl no está disponible, se usa DuckDuckGo HTML como fallback para obtener resultados de los dominios permitidos.

## Observabilidad
- `/metrics` expone métricas Prometheus (latencia, conteo y llamadas externas).
- Logs JSON básicos para eventos clave.

## Suscripciones
Se usa doble opt-in por correo cuando SMTP está configurado. También se incluye enlace de cancelación en cada digest diario.

## Variables de entorno
Copia `.env.example` a `.env` y completa los valores. El frontend usa `NEXT_PUBLIC_API_URL` y el backend lee las credenciales de Firecrawl/OpenAI/SMTP desde ese mismo archivo.

## Desarrollo rápido (sin Docker)
Backend:
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Docker
```bash
docker compose up --build
```

## Deploy
Ver `DEPLOYMENT.md`.
