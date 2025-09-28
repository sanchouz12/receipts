from fastapi import FastAPI

from src.routes.auth import router as auth_router

app = FastAPI(root_path="/api", redirect_slashes=False)
app.include_router(auth_router)
