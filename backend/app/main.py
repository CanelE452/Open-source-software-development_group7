from fastapi import FastAPI

from backend.app.api.dependencies import init_app_state
from backend.app.api.errors import register_exception_handlers
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.repositories import router as repositories_router
from backend.app.api.routes.search import router as search_router


def create_app() -> FastAPI:
    """앱을 만들고 라우터·상태·오류 핸들러를 연결한다."""

    app = FastAPI(title="Issue Finder", version="0.1.0")
    app.include_router(health_router, prefix="/api")
    app.include_router(repositories_router, prefix="/api")
    app.include_router(search_router, prefix="/api")
    register_exception_handlers(app)
    init_app_state(app)
    return app


app = create_app()
