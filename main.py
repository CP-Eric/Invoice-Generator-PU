import uvicorn
from fastapi import FastAPI
from app.routes import invoice_routes
from app.openapi_config import custom_openapi

app = FastAPI()
app.include_router(invoice_routes.router)
app.openapi = lambda: custom_openapi(app)
