from pydantic import BaseModel , EmailStr
from typing import Optional
from datetime import datetime
from app.models import InvoiceStatus


# --Tenant ----
class TenantCreate(BaseModel):
    name : str
    email : EmailStr

class TenantOut(BaseModel):
    id : str
    name : str
    email : str
    created_at : datetime

    model_config = {"from_attributes" : True} # this tells pydantic that  an sqlalchemy model object is going to be handed to you , read its attributes directly

# ─── Auth ───────────────────────────────────────────────────

class TenantSignup(BaseModel):
    name: str
    email: EmailStr
    password: str


class TenantLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# --- Client ------
class ClientCreate(BaseModel):
    name : str
    email : EmailStr

class ClientOut(BaseModel):
    id : str
    tenant_id : str
    name : str
    email : str
    created_at : datetime

    model_config = {"from_attributes" : True}

# -- Invoice ----
class InvoiceCreate(BaseModel):
    client_id : str
    title : str
    amount : float
    due_date : Optional[datetime] = None

class InvoiceUpdate(BaseModel):
    status : InvoiceStatus

class InvoiceOut(BaseModel):
    id : str
    tenant_id : str
    client_id : str
    title : str
    amount : float
    status : InvoiceStatus
    due_date : Optional[datetime]
    created_at : datetime

    model_config = {"from_attributes" : True}

# -- Billing Summary ----

class BillingSummary(BaseModel):
    total_invoices : int
    total_amount : float
    paid_amount : float
    pending_amount : float     


