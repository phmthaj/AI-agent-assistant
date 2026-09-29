from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import AgentOrchestrator
from app.config import get_settings
from app.database import get_db
from app.llm import LLMClient
from app.memory import RedisShortTermMemory
from app.schemas import ChatRequest, ChatResponse
from app.tools import build_default_registry


app = FastAPI(
    title="AI Agent Backend",
    version="0.1.0",
)
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

settings = get_settings()
llm_client = LLMClient(settings)
tool_registry = build_default_registry()
short_term_memory = RedisShortTermMemory(settings)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(static_dir / "index.html")


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    orchestrator = AgentOrchestrator(
        db=db,
        llm=llm_client,
        tools=tool_registry,
        settings=settings,
        memory=short_term_memory,
    )
    return await orchestrator.run(
        user_message=request.message,
        conversation_id=request.conversation_id,
    )
