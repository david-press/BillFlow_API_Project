from models import Tenant
from sqlalchemy import select
from dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException
from schemas import TenantSignup, TenantLogin, Token, RefreshRequest
from auth import hash_password, verify_password, create_access_token, create_refresh_token, decode_token

router = APIRouter(prefix="/auth", tags=["Auth"])


# ─── Signup ─────────────────────────────────────────────────

@router.post("/signup", response_model=Token)
async def signup(payload: TenantSignup, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tenant).where(Tenant.email == payload.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    tenant = Tenant(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password)
    )
    db.add(tenant)
    await db.flush()
    await db.refresh(tenant)

    access_token = create_access_token({"sub": tenant.id})
    refresh_token = create_refresh_token({"sub": tenant.id})

    return Token(access_token=access_token, refresh_token=refresh_token)


# ─── Login ──────────────────────────────────────────────────

@router.post("/login", response_model=Token)
async def login(payload: TenantLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tenant).where(Tenant.email == payload.email))
    tenant = result.scalar_one_or_none()

    if not tenant or not verify_password(payload.password, tenant.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token({"sub": tenant.id})
    refresh_token = create_refresh_token({"sub": tenant.id})

    return Token(access_token=access_token, refresh_token=refresh_token)


# ─── Refresh ────────────────────────────────────────────────

@router.post("/refresh", response_model=Token)
async def refresh(payload: RefreshRequest):
    try:
        decoded = decode_token(payload.refresh_token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token is not a refresh token")

    tenant_id = decoded.get("sub")
    new_access_token = create_access_token({"sub": tenant_id})
    new_refresh_token = create_refresh_token({"sub": tenant_id})

    return Token(access_token=new_access_token, refresh_token=new_refresh_token)