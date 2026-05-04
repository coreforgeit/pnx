from fastapi import FastAPI

from settings import conf
from sheet_api.router import router as sheet_router


app = FastAPI(
    title=conf.api_title,
    version=conf.api_version,
    debug=conf.debug,
)

app.include_router(sheet_router, prefix=conf.sheet_api_prefix)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
