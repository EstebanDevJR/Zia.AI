# Zia.AI

Plataforma ultra minimalista para noticias diarias de IA, con filtros, resúmenes automáticos, envío por correo y suscripciones diarias. Frontend en Next.js y backend en FastAPI con orquestación de agentes (LangGraph) y SQLite.

## Estructura
- frontend/  (Next.js)
- backend/   (FastAPI + LangGraph)
- docker-compose.yml

## Requisitos
- Docker y Docker Compose
- (Opcional) claves de API para Firecrawl y resumen

## Fuentes confiables
La API consulta Firecrawl Search con una lista de dominios permitidos (`FIRECRAWL_ALLOWED_DOMAINS`). La UI siempre enlaza a la fuente original.

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
