from fastapi import FastAPI

from src.routes.auth import router as auth_router
from src.routes.receipts import router as receipts_router

app = FastAPI(root_path="/api", redirect_slashes=False)
app.include_router(auth_router)
app.include_router(receipts_router)
