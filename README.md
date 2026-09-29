# AI Agent Assistant

Project Python/FastAPI cơ bản cho một AI agent có backend API, frontend chat UI, PostgreSQL persistent history, Redis short-term memory, OpenAI-compatible LLM client và tool calling.

`User -> FastAPI -> Agent Orchestrator -> LLM -> Tool(s) -> LLM -> Final answer`

## Thành phần chính

- `app/main.py`: FastAPI routes.
- `app/agent/orchestrator.py`: quản lý agent loop, state trong request và persistence logs.
- `app/llm/client.py`: client OpenAI-compatible, dùng được với vLLM nếu endpoint hỗ trợ Chat Completions/tool calling.
- `app/tools/`: tool system có registry và các tool demo.
- `app/memory/`: Redis short-term memory cho recent context của conversation.
- `app/static/`: frontend chat UI được FastAPI serve tại `/`.
- `app/models.py`: SQLAlchemy models cho `Conversation`, `Message`, `AgentRun`, `ToolCall`.
- `alembic/`: migration schema ban đầu.

## Cấu trúc thư mục

```text
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── agent/
│   ├── llm/
│   ├── memory/
│   ├── tools/
│   └── static/
├── alembic/
├── docker-compose.yml
├── requirements.txt
├── create_tables.py
├── test_db.py
└── README.md
```

## Lưu trữ dữ liệu

PostgreSQL là nguồn dữ liệu lâu dài:

- `conversations`: mỗi cuộc hội thoại.
- `messages`: lịch sử user/assistant messages.
- `agent_runs`: mỗi lần agent xử lý một request.
- `tool_calls`: tool name, arguments và result.

Redis là short-term memory:

- Giữ các message gần nhất của conversation.
- Có TTL để tự hết hạn.
- Nếu Redis chưa chạy hoặc bị lỗi, agent fallback sang các message gần nhất trong PostgreSQL.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker compose up -d postgres
docker compose up -d redis
alembic upgrade head
```

Nếu chưa muốn dùng Alembic, có thể tạo bảng nhanh bằng:

```bash
python create_tables.py
```

Nếu database đã có sẵn bảng từ lần chạy `create_tables.py` trước đó, có thể đánh dấu Alembic đang ở version hiện tại:

```bash
alembic stamp head
```

## Cấu hình

Các biến môi trường chính:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_agent
REDIS_URL=redis://localhost:6379/0
SHORT_TERM_MEMORY_TTL_SECONDS=3600
SHORT_TERM_MEMORY_MAX_MESSAGES=12
OPENAI_API_BASE=http://127.0.0.1:8000/v1
OPENAI_API_KEY=dummy
OPENAI_MODEL=Qwen/Qwen3-4B
LLM_MAX_TOKENS=2048
AGENT_MAX_STEPS=6
```

Với vLLM, chạy server OpenAI-compatible và trỏ `OPENAI_API_BASE` tới endpoint `/v1`.

PostgreSQL là nguồn dữ liệu lâu dài. Redis chỉ giữ short-term memory gần đây để agent gửi ít context hơn cho LLM; nếu Redis chưa chạy, agent fallback sang các message gần nhất trong PostgreSQL.

## Chạy API

```bash
uvicorn app.main:app --reload --port 8001
```

Nếu port `8001` đang bận, đổi sang port khác, ví dụ `--port 8765`.

Frontend:

```text
http://127.0.0.1:8001/
```

Chat mới:

```bash
curl -X POST http://127.0.0.1:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Tính giúp tôi (120 + 35) * 4 rồi giải thích ngắn gọn."}'
```

Tiếp tục conversation cũ:

```bash
curl -X POST http://127.0.0.1:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":1,"message":"Câu trước kết quả là gì?"}'
```

Response mẫu:

```json
{
  "conversation_id": 1,
  "agent_run_id": 1,
  "answer": "Kết quả là 620.",
  "tool_calls": [
    {
      "tool_name": "calculator",
      "arguments": {"expression": "(120 + 35) * 4"},
      "result": {"ok": true, "expression": "(120 + 35) * 4", "value": 620}
    }
  ]
}
```

## Thêm tool mới

1. Tạo class kế thừa `BaseTool` trong `app/tools/`.
2. Định nghĩa `name`, `description`, `parameters` theo JSON Schema.
3. Implement `execute()`.
4. Register tool trong `build_default_registry()` ở `app/tools/__init__.py`.

Skeleton:

```python
from typing import Any

from app.tools.base import BaseTool


class MyTool(BaseTool):
    name = "my_tool"
    description = "Describe what this tool does."
    parameters = {
        "type": "object",
        "properties": {
            "input": {"type": "string"}
        },
        "required": ["input"],
        "additionalProperties": False,
    }

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True, "value": arguments["input"]}
```

## Tool demo hiện có

- `calculator`: tính toán biểu thức số học.
- `current_time`: lấy thời gian UTC hiện tại.
- `web_search`: tìm thông tin nhanh qua DuckDuckGo Instant Answer.
- `unit_converter`: đổi đơn vị độ dài, khối lượng, nhiệt độ.
- `text_analyzer`: thống kê text, top terms, số câu/từ/ký tự.
- `http_fetch`: fetch URL public với giới hạn kích thước và chặn private/local network.

## Hướng mở rộng

- Redis cache/session queue.
- RAG với pgvector.
- Long-term memory table tách riêng khỏi message history.
- Planner/verifier node trong orchestrator.
- Background jobs cho runs dài.
- Multi-agent hoặc graph-based orchestration.
- Auth/user management.
- Streaming response qua Server-Sent Events hoặc WebSocket.
