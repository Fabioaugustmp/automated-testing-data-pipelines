from fastapi import FastAPI
from app.db.base import Base
from app.db.session import engine
from app.api.endpoints import transaction

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API de Transações com ETL",
    description="Uma API simples para registrar e consultar transações financeiras usando um fluxo ETL.",
    version="1.0.0"
)

# Include API routers
app.include_router(transaction.router)