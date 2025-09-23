from fastapi import FastAPI

app = FastAPI(root_path="/api", redirect_slashes=False)
