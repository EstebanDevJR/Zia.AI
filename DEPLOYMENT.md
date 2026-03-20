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
Completa al menos `FIRECRAWL_API_KEY`, `OPENAI_API_KEY` y las credenciales SMTP.

## 4) Levantar contenedores
```bash
docker compose up -d --build
```

Frontend: `http://IP_PUBLICA:3000`
Backend: `http://IP_PUBLICA:8000/health`

## 5) Persistencia
La base de datos SQLite vive en el volumen `backend_data`.

Prueba rápida:
```bash
docker compose down
docker compose up -d
```
Las suscripciones deben mantenerse.

## 6) Operación
Ver logs:
```bash
docker compose logs -f backend
```
Reiniciar servicios:
```bash
docker compose restart
```
