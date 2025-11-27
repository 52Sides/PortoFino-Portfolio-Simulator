import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.sessions import SessionMiddleware

from api.routers import simulate, history, report, health, auth, oauth, token, ws_simulations, ws_reports
from core.config import settings
from core.report.xls_generator import REPORTS_DIR
from services.redis.client import redis_client
from services.kafka.producer import producer
from services.kafka.init_topics import create_topics
from services.kafka.consumer import consume_events

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown: Redis, Kafka topics, Kafka producer"""
    await redis_client.connect()
    await create_topics()
    await producer.start()
    consumer_tasks = [asyncio.create_task(consume_events())]
    logger.info("[Startup] Redis, Kafka topics, Kafka consumer connected")

    try:
        yield
    finally:
        for task in consumer_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info("[Shutdown] Kafka Consumer task cancelled")

        await redis_client.close()
        await producer.stop()
        logger.info("[Shutdown] Kafka and Redis closed")


app = FastAPI(
    title="PortoFino Portfolio Simulator API",
    description="API for portfolio simulation",
    version="3.0",
    lifespan=lifespan,
)

instrumentator = Instrumentator().instrument(app)
instrumentator.expose(app, endpoint="/metrics", include_in_schema=False)

origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://frontend:5173",
]
app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
)

app.mount(
    "/tmp/reports",
    StaticFiles(directory=str(REPORTS_DIR)),
    name="reports"
)

app.include_router(simulate.router)
app.include_router(history.router)
app.include_router(report.router)
app.include_router(health.router)
app.include_router(ws_simulations.router)
app.include_router(ws_reports.router)
app.include_router(auth.router)
app.include_router(oauth.router)
app.include_router(token.router)

logger.info("[Startup] FastAPI app initialized successfully")
