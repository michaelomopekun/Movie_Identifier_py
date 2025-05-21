from api.routes import router
from fastapi import FastAPI
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


app.include_router(router)