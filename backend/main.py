from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os
from agent import agent, PydanticAIDeps
from supabase import create_client
from openai import AsyncOpenAI
from dotenv import load_dotenv
from typing import Literal, List

from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart
)

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
deps = PydanticAIDeps(supabase, openai_client)

class ChatMessage(BaseModel):
    role: Literal["user", "agent"]
    content: str

class QueryRequest(BaseModel):
    message: str
    history: List[ChatMessage]

@app.post("/ask")
async def ask_agent(req: QueryRequest):
    try:
        message_history = []
        for msg in req.history:
            part = TextPart(content=msg.content)
            if msg.role == "user":
                message_history.append(ModelRequest(parts=[UserPromptPart(content=msg.content)]))
            else:
                message_history.append(ModelResponse(parts=[TextPart(content=msg.content)]))

        result = await agent.run(
            req.message,
            deps=deps,
            message_history=message_history
        )

        return {"response": result.output}

    except Exception as e:
        return {"error": str(e)}
