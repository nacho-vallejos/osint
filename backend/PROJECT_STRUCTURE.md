# 🗂️ Estructura del Proyecto - Celery Implementation

## Árbol de Archivos

```
backend/
├── 📁 app/
│   ├── 📁 core/
│   │   ├── __init__.py
│   │   └── celery_app.py              ← Configuración Celery
│   │
│   ├── 📁 tasks/
│   │   ├── __init__.py
│   │   └── scan_tasks.py              ← Tareas asíncronas
│   │
│   ├── �� routers/
│   │   ├── __init__.py
│   │   └── scan.py                    ← API endpoints async
│   │
│   ├── 📁 api/
│   │   ├── routes.py                  (existente)
│   │   ├── triangulation_routes.py    (existente)
│   │   ├── metadata_routes.py         (existente)
│   │   └── osint_framework_routes.py  (existente)
│   │
│   ├── 📁 collectors/
│   │   ├── base.py                    (existente)
│   │   ├── dns_collector.py           (existente)
│   │   ├── username_collector.py      (existente)
│   │   ├── metadata_collector.py      (existente)
│   │   ├── identity_collector.py      (existente)
│   │   ├── social_collector.py        (existente)
│   │   └── ...                        (otros 6 collectors)
│   │
│   ├── 📁 models/
│   │   └── schemas.py                 (existente)
│   │
│   └── main.py                        ← App FastAPI (actualizado)
│
├── 🐳 docker-compose.yml              ← Orquestación Docker
├── 🐳 Dockerfile                      ← Imagen Docker
├── 📦 requirements.txt                ← Dependencias Python
├── ⚙️  .env.example                   ← Variables de entorno
│
├── 📚 CELERY_README.md                ← Documentación completa
├── 📚 QUICKSTART.md                   ← Guía de inicio rápido
├── 📚 IMPLEMENTATION_SUMMARY.md       ← Resumen de implementación
├── 📚 PROJECT_STRUCTURE.md            ← Este archivo
│
└── 🧪 test_celery_setup.py            ← Script de verificación
```

## 📋 Componentes por Responsabilidad

### 🔧 Core (Configuración)
```
app/core/celery_app.py
├── Instancia de Celery
├── Configuración de Redis broker
├── Serialización JSON
├── Task routing y queues
├── Timeouts y retry policies
└── Worker settings
```

### 🔄 Tasks (Lógica Asíncrona)
```
app/tasks/scan_tasks.py
├── perform_osint_scan()
│   ├── Instanciación dinámica de collectors
│   ├── Ejecución async de collect()
│   ├── Actualización de estados
│   ├── Manejo de errores
│   └── Retry automático
│
├── COLLECTOR_MAP
│   └── Mapeo: type → Class
│
└── health_check()
```

### 🌐 API (Endpoints HTTP)
```
app/routers/scan.py
├── POST /api/v1/scan
│   └── Encolar tarea → task_id
│
├── GET /api/v1/scan/{task_id}
│   └── Consultar estado → result
│
├── GET /api/v1/scan/{task_id}/cancel
│   └── Cancelar tarea
│
├── GET /api/v1/collectors
│   └── Listar collectors
│
└── GET /api/v1/health
    └── Health check workers
```

### 🐳 Infraestructura (Docker)
```
docker-compose.yml
├── Service: redis
│   ├── Port: 6379
│   └── Volume: redis-data
│
├── Service: api
│   ├── Port: 8000
│   └── Depends: redis
│
├── Service: celery-worker
│   ├── Concurrency: 4
│   └── Depends: redis
│
├── Service: celery-beat
│   └── Scheduler
│
└── Service: flower
    ├── Port: 5555
    └── Monitoring UI
```

## 🔀 Flujo de Datos

```
1. Cliente
   ↓ POST /scan {target, type}
   
2. FastAPI (app/routers/scan.py)
   ↓ Validar → Encolar tarea
   ↓ perform_osint_scan.delay(target, type)
   
3. Redis Broker
   ↓ Queue: osint_scans
   
4. Celery Worker (app/tasks/scan_tasks.py)
   ↓ Pull tarea → Procesar
   ↓ COLLECTOR_MAP[type] → collector_class
   ↓ collector = collector_class()
   ↓ result = await collector.collect(target)
   
5. Redis Backend
   ↓ Guardar resultado
   
6. Cliente
   ↓ GET /scan/{task_id}
   ↓ Polling cada 2s
   
7. FastAPI
   ↓ AsyncResult(task_id)
   ↓ Retornar estado/resultado
   
8. Cliente
   └─ Recibir resultado final
```

## 🎯 Endpoints Disponibles

### Async Scans (NUEVOS)
```
POST   /api/v1/scan                    ← Iniciar scan
GET    /api/v1/scan/{task_id}         ← Consultar estado
GET    /api/v1/scan/{task_id}/cancel  ← Cancelar
GET    /api/v1/collectors              ← Listar collectors
GET    /api/v1/health                  ← Health check
```

### Existing Routes (PREVIOS)
```
POST   /api/v1/dns/analyze
POST   /api/v1/username/analyze
POST   /api/v1/triangulation/correlate
GET    /api/v1/metadata/extract
GET    /api/v1/osint-framework/categories/tree
```

## 📊 Estadísticas de Implementación

| Categoría | Archivos | Líneas |
|-----------|----------|--------|
| **Código Nuevo** | 4 | 616 |
| - Core | 1 | 72 |
| - Tasks | 1 | 190 |
| - Routers | 1 | 321 |
| - Main | 1 | 33 |
| **Testing** | 1 | 149 |
| **Documentación** | 4 | 828 |
| **Config** | 4 | 212 |
| **TOTAL** | 13 | 1,805 |

## 🔌 Dependencias Nuevas

```python
# requirements.txt
celery[redis]==5.3.4  # Framework de tareas
redis==5.0.1          # Cliente Redis
kombu==5.3.4          # Messaging library
flower==2.0.1         # Monitoring UI
```

## 🚀 Comandos de Uso

### Desarrollo Local
```bash
# Terminal 1: API
uvicorn app.main:app --reload --port 8000

# Terminal 2: Worker
celery -A app.core.celery_app worker --loglevel=info

# Terminal 3: Monitoring
celery -A app.core.celery_app flower --port=5555
```

### Docker Compose
```bash
# Iniciar todo
docker-compose up -d

# Ver logs
docker-compose logs -f celery-worker

# Escalar workers
docker-compose up -d --scale celery-worker=4

# Detener
docker-compose down
```

### Testing
```bash
# Verificar setup
python test_celery_setup.py

# Probar API
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "google.com", "type": "dns"}'
```

## 🔍 Debugging

### Ver tareas activas
```bash
celery -A app.core.celery_app inspect active
```

### Ver workers registrados
```bash
celery -A app.core.celery_app inspect registered
```

### Purgar cola
```bash
celery -A app.core.celery_app purge
```

### Redis CLI
```bash
redis-cli
> KEYS celery*
> GET celery-task-meta-<task_id>
```

## 📈 Monitoring URLs

| Service | URL | Descripción |
|---------|-----|-------------|
| API | http://localhost:8000 | FastAPI Server |
| Swagger | http://localhost:8000/docs | API Docs |
| Flower | http://localhost:5555 | Celery Monitor |
| Redis | localhost:6379 | Redis Broker |

## ✅ Checklist de Verificación

- [ ] Redis instalado y corriendo
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Test setup exitoso (`python test_celery_setup.py`)
- [ ] API iniciada (puerto 8000)
- [ ] Worker iniciado
- [ ] Flower accesible (puerto 5555)
- [ ] Scan de prueba exitoso
- [ ] Monitoring en Flower funcional

## 🎓 Recursos de Aprendizaje

1. **Celery Basics**: https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html
2. **Redis Commands**: https://redis.io/commands/
3. **FastAPI Async**: https://fastapi.tiangolo.com/async/
4. **Flower Docs**: https://flower.readthedocs.io/

---

**Última actualización**: Diciembre 2024
**Versión**: 2.1.0
