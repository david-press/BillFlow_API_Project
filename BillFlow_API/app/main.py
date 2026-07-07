from fastapi import FastAPI
from app.database import lifespan
from fastapi.middleware.cors import CORSMiddleware
from app.routers import clients , invoices , tenants , auth

app = FastAPI(
    title= "BillFlow API",
    description="Multi-tenant invoice and billing backend",
    version = "1.1.0",
    lifespan= lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # fine for local dev, never in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tenants.router)
app.include_router(clients.router)
app.include_router(invoices.router)


app.get("/")
async def root():
    return {"status" : "BillFlow running"}