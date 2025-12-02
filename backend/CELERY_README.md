# OSINT Platform - Async Task Queue with Celery

## Arquitectura

Esta implementación utiliza **Celery** con **Redis** como broker de mensajes y backend de resultados para procesar tareas de OSINT de forma asíncrona.

### Componentes

1. **FastAPI API** (`app/main.py`) - Servidor web principal
2. **Celery Worker** (`app/core/celery_app.py`) - Procesador de tareas asíncronas
3. **Redis** - Broker de mensajes y almacenamiento de resultados
4. **Flower** (opcional) - UI de monitoreo de Celery

## 🚀 Inicio Rápido

### Con Docker Compose (Recomendado)

```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down
```

Servicios disponibles:
- API: http://localhost:8000
- Flower (Monitoring): http://localhost:5555
- Redis: localhost:6379

### Sin Docker (Desarrollo Local)

1. **Instalar Redis**:
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis

# Fedora
sudo dnf install redis
sudo systemctl start redis
```

2. **Instalar dependencias Python**:
```bash
pip install -r requirements.txt
```

3. **Iniciar servicios** (3 terminales separadas):

**Terminal 1 - API**:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Celery Worker**:
```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info --concurrency=4
```

**Terminal 3 - Flower (opcional)**:
```bash
cd backend
celery -A app.core.celery_app flower --port=5555
```

## 📡 API Endpoints

### 1. Iniciar Scan Asíncrono

**POST** `/api/v1/scan`

Encola una tarea de OSINT y retorna inmediatamente un `task_id`.

**Request Body**:
```json
{
  "target": "example.com",
  "type": "dns"
}
```

**Response**:
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "PENDING",
  "message": "Scan initiated successfully",
  "target": "example.com",
  "collector_type": "dns"
}
```

**Collector Types disponibles**:
- `dns` - DNS/Domain analysis
- `username` - Username OSINT
- `metadata` - Image/File metadata extraction
- `identity` - Identity triangulation
- `social` - Social media profiles
- `crtsh` - Certificate transparency logs
- `whois` - WHOIS information
- `shodan` - Shodan IoT search
- `virustotal` - VirusTotal analysis
- `haveibeenpwned` - Data breach check
- `securitytrails` - Security trails history

### 2. Consultar Estado de Scan

**GET** `/api/v1/scan/{task_id}`

Consulta el estado actual de una tarea.

**Estados posibles**:
- `PENDING` - En cola, esperando procesamiento
- `STARTED` - Tarea iniciada
- `PROCESSING` - En ejecución (custom state con progress)
- `SUCCESS` - Completada exitosamente
- `FAILURE` - Falló
- `RETRY` - Reintentando

**Response (en proceso)**:
```json
{
  "task_id": "a1b2c3d4-...",
  "status": "PROCESSING",
  "progress": "Running DNSCollector...",
  "meta": {
    "collector_type": "dns",
    "target": "example.com",
    "status": "Running DNSCollector..."
  }
}
```

**Response (completada)**:
```json
{
  "task_id": "a1b2c3d4-...",
  "status": "SUCCESS",
  "progress": "Scan completed successfully",
  "result": {
    "id": "result-uuid",
    "collector_name": "DNSCollector",
    "target": "example.com",
    "success": true,
    "data": {
      "dns_records": [...],
      "nameservers": [...]
    },
    "timestamp": "2024-12-01T10:30:00",
    "metadata": {}
  }
}
```

### 3. Cancelar Scan

**GET** `/api/v1/scan/{task_id}/cancel`

Cancela una tarea en ejecución.

### 4. Listar Collectors

**GET** `/api/v1/collectors`

Lista todos los collectors disponibles.

### 5. Health Check de Celery

**GET** `/api/v1/health`

Verifica el estado de los workers de Celery.

## 🔧 Configuración

### Variables de Entorno

Copia `.env.example` a `.env` y configura:

```bash
cp .env.example .env
```

Variables principales:
- `REDIS_URL` - URL de conexión a Redis
- `CELERY_WORKER_CONCURRENCY` - Número de workers concurrentes
- `CELERY_WORKER_MAX_TASKS_PER_CHILD` - Reiniciar worker después de N tareas

### Celery Configuration

Edita `app/core/celery_app.py` para ajustar:
- Timeouts de tareas
- Políticas de retry
- Serialización
- Routing de colas

## 📊 Monitoreo

### Flower UI

Accede a http://localhost:5555 para ver:
- Workers activos
- Tareas en cola
- Historial de tareas
- Estadísticas en tiempo real

### Celery CLI

```bash
# Ver workers activos
celery -A app.core.celery_app inspect active

# Ver tareas registradas
celery -A app.core.celery_app inspect registered

# Ver estadísticas
celery -A app.core.celery_app inspect stats

# Purgar todas las tareas
celery -A app.core.celery_app purge
```

## 🧪 Testing

### Curl Examples

**Iniciar scan**:
```bash
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com", "type": "dns"}'
```

**Consultar estado** (reemplaza TASK_ID):
```bash
curl http://localhost:8000/api/v1/scan/TASK_ID
```

### Python Example

```python
import httpx
import time

# Iniciar scan
response = httpx.post(
    "http://localhost:8000/api/v1/scan",
    json={"target": "example.com", "type": "dns"}
)
task_id = response.json()["task_id"]
print(f"Task ID: {task_id}")

# Polling del estado
while True:
    status_response = httpx.get(f"http://localhost:8000/api/v1/scan/{task_id}")
    status_data = status_response.json()
    
    print(f"Status: {status_data['status']}")
    
    if status_data["status"] == "SUCCESS":
        print("Result:", status_data["result"])
        break
    elif status_data["status"] == "FAILURE":
        print("Error:", status_data["error"])
        break
    
    time.sleep(2)  # Wait 2 seconds before next check
```

## 🐛 Troubleshooting

### Redis no conecta
```bash
# Verificar que Redis esté corriendo
redis-cli ping
# Debería responder: PONG

# Ver logs de Redis
sudo journalctl -u redis -f
```

### Celery worker no inicia
```bash
# Verificar que Redis esté accesible
redis-cli -u redis://localhost:6379/0 ping

# Verificar imports
python -c "from app.core.celery_app import celery_app; print('OK')"
```

### Tareas se quedan en PENDING
- Verifica que el worker esté corriendo
- Verifica la conexión a Redis
- Revisa los logs del worker

## 📚 Documentación

### Swagger UI
Accede a http://localhost:8000/docs para la documentación interactiva de la API.

### Architecture
```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /scan
       ▼
┌─────────────┐     ┌─────────────┐
│  FastAPI    │────▶│   Redis     │
│     API     │     │   Broker    │
└─────────────┘     └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Celery    │
                    │   Worker    │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Collectors  │
                    │ (DNS, etc)  │
                    └─────────────┘
```

## �� Notas

- Las tareas expiran después de 1 hora (configurable en `celery_app.py`)
- Los workers se reinician automáticamente después de 100 tareas
- Timeout por tarea: 5 minutos (hard), 4 minutos (soft)
- Retry automático: 3 intentos con backoff exponencial
