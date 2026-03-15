from fastapi import FastAPI
from .db import Base, engine
from .routers.inventory import router as inventory_router
from .routers.reports import router as reports_router
from .routers.catalog import router as catalog_router
from .routers.leads import router as leads_router

app = FastAPI(title="Phones Core API")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


app.include_router(inventory_router)
app.include_router(reports_router)
app.include_router(catalog_router)
app.include_router(leads_router)