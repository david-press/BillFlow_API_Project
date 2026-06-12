from fastapi import FastAPI
from app.database import lifespan
from app.routers import clients , invoices , tenants

app = FastAPI(
    title= "BillFlow API",
    description="Multi-tenant invoice and billing backend",
    version = "1.0.0",
    lifespan= lifespan
)

app.include_router(tenants.router)
app.include_router(clients.router)
app.include_router(invoices.router)


app.get("/")
async def root():
    return {"status" : "BillFlow running"}