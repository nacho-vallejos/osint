# Sistema de Créditos y Rate Limiting

## 📋 Resumen

Sistema de facturación por créditos con rate limiting para la API de OSINT, implementando:
- ✅ Modelo de datos con SQLAlchemy
- ✅ Rate limiting con Redis
- ✅ Deducción atómica de créditos con row-level locking
- ✅ Protección contra race conditions
- ✅ Integración completa en endpoints

---

## 🏗️ Arquitectura

### 1. Database Layer (`app/database.py`)
```python
# Motor SQLAlchemy con soporte PostgreSQL/SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./osint_platform.db")
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
```

**Características:**
- Connection pooling automático
- Fallback a SQLite para desarrollo
- Dependency `get_db()` para inyección en endpoints

### 2. User Model (`app/models/user.py`)
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    credits_balance = Column(Integer, default=10, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
```

**Características:**
- Balance de créditos con default de 10
- Timestamps automáticos
- Estado de cuenta (activo/inactivo)

### 3. Rate Limiter (`app/main.py`)
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_connection = redis.from_url("redis://localhost:6379")
    await FastAPILimiter.init(redis_connection)
    init_db()
    yield
    await redis_connection.close()
```

**Configuración:**
- Redis como backend de rate limiting
- Inicialización automática al startup
- Limpieza en shutdown

### 4. Dependencies (`app/api/deps.py`)

#### a) Authentication
```python
async def get_current_user_id(
    x_user_id: Optional[str] = Header(None)
) -> int:
    """Extrae user_id del header X-User-Id"""
```

#### b) Credit Deduction (⚠️ CRÍTICO)
```python
def check_and_deduct_credits(cost: int):
    async def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        # 🔒 ROW LOCKING para prevenir race conditions
        user = db.query(User).filter(
            User.id == current_user.id
        ).with_for_update().first()
        
        if user.credits_balance < cost:
            raise HTTPException(402, "Insufficient credits")
        
        user.credits_balance -= cost
        db.commit()
        return user
```

**Garantías de Seguridad:**
- `with_for_update()`: Bloquea la fila hasta el commit
- Previene doble-gasto en requests paralelas
- Rollback automático en excepciones
- Transacciones ACID completas

---

## 🔐 Endpoints Protegidos

### POST /api/v1/scan

**Rate Limit:** 10 requests/minuto  
**Costo:** 5 créditos por escaneo

```python
@router.post("/scan", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def initiate_scan(
    request: ScanRequest,
    user: User = Depends(check_and_deduct_credits(cost=5))
) -> ScanResponse:
    # Los créditos ya fueron deducidos aquí
    task = perform_osint_scan.delay(request.target, request.type)
    return ScanResponse(
        task_id=task.id,
        credits_remaining=user.credits_balance,
        cost=5
    )
```

**Flujo de Ejecución:**
1. ✅ Rate limiter verifica límite de requests
2. ✅ Dependency obtiene usuario actual
3. ✅ Dependency bloquea fila con `with_for_update()`
4. ✅ Verifica balance suficiente
5. ✅ Deduce créditos atómicamente
6. ✅ Commit y release del lock
7. ✅ Endpoint encola tarea en Celery

**Códigos de Error:**
- `401 Unauthorized`: Header X-User-Id faltante/inválido
- `402 Payment Required`: Créditos insuficientes
- `403 Forbidden`: Cuenta inactiva
- `429 Too Many Requests`: Rate limit excedido
- `500 Internal Server Error`: Error de transacción

---

## 🚀 Uso

### 1. Inicializar Base de Datos
```bash
cd /home/ruler/osint-work/backend
python3 init_db.py
```

**Usuarios de Prueba Creados:**
| ID | Email                  | Créditos | Estado   |
|----|------------------------|----------|----------|
| 1  | test@example.com       | 100      | ✓ Activo |
| 2  | admin@example.com      | 1000     | ✓ Activo |
| 3  | premium@example.com    | 500      | ✓ Activo |
| 4  | basic@example.com      | 10       | ✓ Activo |
| 5  | broke@example.com      | 0        | ✓ Activo |
| 6  | inactive@example.com   | 50       | ✗ Inactivo |

### 2. Consultar Balance de Créditos
```bash
curl http://localhost:8000/api/v1/credits \
  -H 'X-User-Id: 1'
```

**Respuesta:**
```json
{
  "user_id": 1,
  "email": "test@example.com",
  "credits_balance": 100,
  "is_active": true
}
```

### 3. Iniciar Escaneo (Deduce 5 Créditos)
```bash
curl -X POST http://localhost:8000/api/v1/scan \
  -H 'Content-Type: application/json' \
  -H 'X-User-Id: 1' \
  -d '{
    "target": "example.com",
    "type": "dns"
  }'
```

**Respuesta (200 OK):**
```json
{
  "task_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "status": "PENDING",
  "message": "Scan initiated successfully",
  "target": "example.com",
  "collector_type": "dns",
  "credits_remaining": 95,
  "cost": 5
}
```

### 4. Caso: Créditos Insuficientes
```bash
curl -X POST http://localhost:8000/api/v1/scan \
  -H 'X-User-Id: 5'  # Usuario broke@example.com (0 créditos)
  -d '{"target": "test.com", "type": "dns"}'
```

**Respuesta (402 Payment Required):**
```json
{
  "detail": "Insufficient credits. Required: 5, Available: 0"
}
```

**Headers:**
```
X-Credits-Required: 5
X-Credits-Available: 0
X-Credits-Needed: 5
```

### 5. Caso: Rate Limit Excedido
```bash
# 11ª request en el mismo minuto
curl -X POST http://localhost:8000/api/v1/scan ...
```

**Respuesta (429 Too Many Requests):**
```json
{
  "detail": "Rate limit exceeded"
}
```

---

## 🔍 Testing de Race Conditions

### Script de Prueba Paralela
```python
import asyncio
import aiohttp

async def parallel_scans(user_id: int, count: int):
    """Envía múltiples scans simultáneos"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(count):
            task = session.post(
                'http://localhost:8000/api/v1/scan',
                json={'target': 'test.com', 'type': 'dns'},
                headers={'X-User-Id': str(user_id)}
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        return responses

# Usuario con 10 créditos intenta 3 scans paralelos (15 créditos)
asyncio.run(parallel_scans(user_id=4, count=3))
```

**Resultado Esperado:**
- ✅ 2 scans aceptados (10 créditos deducidos)
- ❌ 1 scan rechazado con `402 Insufficient credits`
- ✅ Balance final: 0 créditos (consistente)

**Sin Row Locking:**
- ❌ 3 scans aceptados (race condition)
- ❌ Balance final: -5 créditos (inconsistente)

---

## 🛠️ Variables de Entorno

### Configuración de Database
```bash
# PostgreSQL (Producción)
DATABASE_URL=postgresql://user:password@localhost:5432/osint_db

# SQLite (Desarrollo - Default)
DATABASE_URL=sqlite:///./osint_platform.db
```

### Redis (Rate Limiting)
```bash
# Ya configurado en main.py
REDIS_URL=redis://localhost:6379
```

---

## 📊 Métricas y Monitoreo

### Query para Auditoría de Créditos
```sql
-- Usuarios con balance bajo
SELECT id, email, credits_balance 
FROM users 
WHERE credits_balance < 10 
  AND is_active = true;

-- Distribución de créditos
SELECT 
    CASE 
        WHEN credits_balance = 0 THEN 'Sin créditos'
        WHEN credits_balance <= 50 THEN 'Bajo (1-50)'
        WHEN credits_balance <= 200 THEN 'Medio (51-200)'
        ELSE 'Alto (200+)'
    END as tier,
    COUNT(*) as users
FROM users
WHERE is_active = true
GROUP BY tier;
```

### Logs del Sistema
```python
# En production, agregar logging
import logging

logger = logging.getLogger(__name__)

# En check_and_deduct_credits()
logger.info(f"User {user_id} deducted {cost} credits. Balance: {user.credits_balance}")
```

---

## 🚨 Troubleshooting

### Error: "pg_config executable not found"
**Solución:**
```bash
pip3 install psycopg2-binary --no-build-isolation
```

### Error: SQLAlchemy import error (Python 3.13)
**Solución:**
```bash
pip3 install sqlalchemy==2.0.36  # Versión compatible
```

### Error: Rate limiter not initialized
**Verificar:**
1. Redis corriendo: `redis-cli ping` → `PONG`
2. Lifespan registrado en FastAPI
3. Logs de startup: "✓ Rate limiter initialized with Redis"

### Base de datos no se crea
**Debug:**
```bash
python3 -c "from app.database import init_db; init_db(); print('OK')"
```

---

## 📝 Notas de Implementación

### Decisiones de Diseño

1. **¿Por qué X-User-Id en lugar de JWT?**
   - Simplifica el testing y desarrollo
   - En producción, reemplazar con validación JWT real

2. **¿Por qué no refund en scan cancelado?**
   - Los créditos se cobran al ENCOLAR, no al completar
   - Ya se consumieron recursos del worker queue

3. **¿Por qué SQLite por defecto?**
   - Cero configuración para desarrollo local
   - Transiciones suaves a PostgreSQL con misma API

4. **¿Por qué `with_for_update()` y no optimistic locking?**
   - Garantía absoluta de consistencia
   - Evita retry logic complejo
   - PostgreSQL maneja locks eficientemente

### Próximas Mejoras

- [ ] Sistema de recarga de créditos (Stripe/PayPal)
- [ ] Historial de transacciones (tabla `credit_transactions`)
- [ ] Tiers de usuarios con diferentes costos
- [ ] Rate limits dinámicos por tier
- [ ] Dashboard de métricas de uso
- [ ] Alertas de balance bajo por email
- [ ] API para administradores (agregar créditos)

---

## 📚 Referencias

- [SQLAlchemy Row Locking](https://docs.sqlalchemy.org/en/20/orm/queryguide/dml.html#selecting-for-update)
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
- [fastapi-limiter Docs](https://github.com/long2ice/fastapi-limiter)
- [PostgreSQL Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html)

---

**Versión:** 2.3.0  
**Fecha:** Diciembre 2025  
**Autor:** Backend Architecture Team
