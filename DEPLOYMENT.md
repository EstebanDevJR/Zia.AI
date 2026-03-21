# Despliegue en Droplet (Ubuntu)

## 1) Preparar servidor
```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git
sudo systemctl enable --now docker
```

## 2) Clonar repo
```bash
git clone https://github.com/EstebanDevJR/Zia.AI.git
cd Zia.AI
```

## 3) Variables de entorno
```bash
cp .env.example .env
nano .env
```
Completa al menos `FIRECRAWL_API_KEY`, `OPENAI_API_KEY` y las credenciales SMTP. Si quieres colas de trabajo, asegúrate de configurar `REDIS_URL`.
Define también:
- `DOMAIN` (tu dominio principal)
- `API_DOMAIN` (subdominio para API, por ejemplo `api.tu-dominio.com`)
- `NEXT_PUBLIC_API_URL` apuntando a `https://API_DOMAIN`
- `FRONTEND_ORIGIN` apuntando a `https://DOMAIN`
- `PUBLIC_BASE_URL` apuntando a `https://API_DOMAIN`

## 4) Levantar contenedores
```bash
docker compose up -d --build
```

Frontend: `http://IP_PUBLICA`
Backend: `http://IP_PUBLICA/health`
Métricas: `http://IP_PUBLICA/metrics`

## 5) HTTPS con Certbot (recomendado)
Prepara carpetas para el challenge:
```bash
mkdir -p nginx/certbot nginx/letsencrypt
```

Solicita certificados (ajusta los dominios a los tuyos):
```bash
sudo apt install -y certbot
sudo certbot certonly --webroot \
  -w $(pwd)/nginx/certbot \
  -d tu-dominio.com \
  -d www.tu-dominio.com \
  -d api.tu-dominio.com \
  --config-dir $(pwd)/nginx/letsencrypt \
  --work-dir $(pwd)/nginx/letsencrypt/work \
  --logs-dir $(pwd)/nginx/letsencrypt/logs
```

Luego reinicia Nginx para que detecte los certificados:
```bash
docker compose restart nginx
```

## 6) Persistencia
La base de datos SQLite vive en el volumen `backend_data`.

Prueba rápida:
```bash
docker compose down
docker compose up -d
```
Las suscripciones deben mantenerse.

## 7) Operación
Ver logs:
```bash
docker compose logs -f backend
```
Reiniciar servicios:
```bash
docker compose restart
```
