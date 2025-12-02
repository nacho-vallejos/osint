# 🚀 Quick Start - Celery Async Tasks

## Opción 1: Desarrollo Local (Sin Docker)

### 1. Instalar Redis

```bash
# Fedora
sudo dnf install redis
sudo systemctl start redis
sudo systemctl enable redis

# Verificar
redis-cli ping  # Debe responder: PONG
```

### 2. Instalar Dependencias Python

```bash
cd backend
pip install -r requirements.txt
```

### 3. Verificar Setup

```bash
cd backend
python test_celery_setup.py
```

### 4. Iniciar Servicios (3 terminales)

**Terminal 1 - FastAPI**:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Celery Worker**:
```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info --concurrency=4
```

**Terminal 3 - Flower (Monitoring UI)**:
```bash
cd backend
celery -A app.core.celery_app flower --port=5555
```

### 5. Probar la API

```bash
# Iniciar un scan
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "google.com", "type": "dns"}'

# La respuesta incluirá un task_id:
# {"task_id": "abc123...", "status": "PENDING", ...}

# Consultar el estado (reemplaza TASK_ID)
curl http://localhost:8000/api/v1/scan/TASK_ID
```

## Opción 2: Docker Compose (Producción)

### 1. Iniciar Todos los Servicios

```bash
cd backend
docker-compose up -d
```

Esto inicia:
- Redis (puerto 6379)
- FastAPI API (puerto 8000)
- Celery Worker
- Celery Beat (scheduler)
- Flower UI (puerto 5555)

### 2. Ver Logs

```bash
# Todos los servicios
docker-compose logs -f

# Solo el worker
docker-compose logs -f celery-worker

# Solo la API
docker-compose logs -f api
```

### 3. Detener Servicios

```bash
docker-compose down
```

## URLs Importantes

- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Flower Monitoring**: http://localhost:5555
- **Health Check**: http://localhost:8000/health

## Collectors Disponibles

| Type | Descripción |
|------|-------------|
| `dns` | Análisis DNS/Dominio |
| `username` | OSINT de username |
| `metadata` | Extracción de metadatos |
| `identity` | Triangulación de identidad |
| `social` | Perfiles de redes sociales |
| `crtsh` | Certificados SSL/TLS |
| `whois` | Información WHOIS |
| `shodan` | Búsqueda IoT |
| `virustotal` | Análisis VirusTotal |
| `haveibeenpwned` | Verificación de brechas |
| `securitytrails` | Historial de seguridad |

## Ejemplo de Uso Completo

```python
import httpx
import time

# 1. Iniciar scan
response = httpx.post(
    "http://localhost:8000/api/v1/scan",
    json={"target": "example.com", "type": "dns"}
)
data = response.json()
task_id = data["task_id"]
print(f"✓ Scan iniciado: {task_id}")

# 2. Polling del estado
while True:
    response = httpx.get(f"http://localhost:8000/api/v1/scan/{task_id}")
    data = response.json()
    
    print(f"Status: {data['status']} - {data.get('progress', '')}")
    
    if data["status"] == "SUCCESS":
        print("✓ Resultado:", data["result"])
        break
    elif data["status"] == "FAILURE":
        print("✗ Error:", data.get("error"))
        break
    
    time.sleep(2)
```

## Troubleshooting

### Redis no conecta
```bash
# Verificar que Redis esté corriendo
sudo systemctl status redis
redis-cli ping

# Ver logs
sudo journalctl -u redis -f
```

### Worker no procesa tareas
```bash
# Verificar que el worker esté corriendo
ps aux | grep celery

# Ver logs del worker
# (en la terminal donde iniciaste el worker)
```

### Tareas se quedan en PENDING
1. Verifica que Redis esté corriendo: `redis-cli ping`
2. Verifica que el worker esté activo: Flower UI (http://localhost:5555)
3. Revisa los logs del worker para errores

## Comandos Útiles

```bash
# Ver workers activos
celery -A app.core.celery_app inspect active

# Ver tareas registradas
celery -A app.core.celery_app inspect registered

# Purgar todas las tareas en cola
celery -A app.core.celery_app purge

# Ver estadísticas
celery -A app.core.celery_app inspect stats
```

## Próximos Pasos

1. Lee `CELERY_README.md` para documentación completa
2. Explora la API en http://localhost:8000/docs
3. Monitorea las tareas en Flower: http://localhost:5555
4. Personaliza la configuración en `app/core/celery_app.py`
