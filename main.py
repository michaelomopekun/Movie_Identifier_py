from api.routes import router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Service.TrailerSearchService import TrailerSearchService


app = FastAPI(
    title="Movie Identifier API",
    description="An API for identifying movies using movie scenes.",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "Movie Identifier",
            "description": "Endpoints for identifying movie using scene.",
        },
    ],
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

app.include_router(router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
