from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from BillFlow_API.app.database import AsyncSessionLocal
from BillFlow_API.app.models import Tenant, ApiKey
from BillFlow_API.app.auth import decode_token


# ─── Dependency 1: Database Session ───────────────────────

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ─── Bearer scheme (JWT extraction) ───────────────────────

bearer_scheme = HTTPBearer()


# ─── Dependency 2: Current Tenant via JWT ──────────────────

async def get_current_tenant(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db)
) -> Tenant:
    token = credentials.credentials

    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Token is not an access token")

    tenant_id = payload.get("sub")
    if tenant_id is None:
        raise HTTPException(status_code=401, detail="Token missing subject")

    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return tenant


# ─── API key scheme (for service/flexible auth) ───────────

api_key_scheme = APIKeyHeader(name="x-api-key", auto_error=False)


# ─── Dependency 3: Current Tenant via JWT OR API key ───────

async def get_current_tenant_flexible(
    api_key: str = Security(api_key_scheme),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Tenant:
    if api_key:
        result = await db.execute(select(ApiKey).where(ApiKey.key == api_key))
        key_row = result.scalar_one_or_none()
        if not key_row:
            raise HTTPException(status_code=401, detail="Invalid API key")
        result = await db.execute(select(Tenant).where(Tenant.id == key_row.tenant_id))
        return result.scalar_one_or_none()

    if credentials:
        return await get_current_tenant(credentials, db)

    raise HTTPException(status_code=401, detail="No valid credentials provided")