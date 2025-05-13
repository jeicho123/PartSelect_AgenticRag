from __future__ import annotations as _annotations

from dataclasses import dataclass
from dotenv import load_dotenv
import logfire
import asyncio
import httpx
import os

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncOpenAI
from supabase import Client, create_client
from typing import List

load_dotenv()

llm = os.getenv('LLM_MODEL', 'gpt-4o-mini')
model = OpenAIModel(llm)

logfire.configure(send_to_logfire='if-token-present')

@dataclass
class PydanticAIDeps:
    supabase: Client
    openai_client: AsyncOpenAI

system_prompt = system_prompt = """
You are an expert in appliance parts, powered by product information from PartSelect.

You have access to detailed documentation chunks about appliance parts including descriptions, usage, and related accessories. These are stored in a vector database, along with product URLs and full content pages.

Your only job is to assist with questions related to these PartSelect products. You do not answer unrelated questions.

Don't ask the user before taking an action — just do it. Always use the available tools to retrieve relevant content before responding, especially when the user's query asks about a specific part, product type, or usage.

When responding, always start by retrieving relevant content using the RAG tool.
Then check the list of known product URLs if needed, or fetch the full content for a specific page if it helps.

Always let the user know when no relevant product information is found — be honest and clear.
"""

agent = Agent(
    model,
    system_prompt=system_prompt,
    deps_type=PydanticAIDeps,
    retries=2
)

# -----------------------------------
# Tool 1: Embed Query for Vector Search
# -----------------------------------
async def get_embedding(text: str, openai_client: AsyncOpenAI) -> List[float]:
    try:
        response = await openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding error: {e}")
        return [0.0] * 1536

# -----------------------------------
# Tool 2: RAG - Retrieve Relevant Chunks
# -----------------------------------
@agent.tool
async def search_parts_content(ctx: RunContext[PydanticAIDeps], query: str) -> str:
    """
    Perform semantic search on product content to retrieve the most relevant chunks.
    """
    try:
        embedding = await get_embedding(query, ctx.deps.openai_client)
        result = ctx.deps.supabase.rpc(
            'match_partselect_chunks',
            {
                'query_embedding': embedding,
                'match_count': 5
            }
        ).execute()

        if not result.data:
            return "No relevant product content found."

        return "\n\n---\n\n".join([r['content'] for r in result.data])

    except Exception as e:
        return f"Error during vector search: {str(e)}"

# -----------------------------------
# Tool 3: List Stored Product URLs
# -----------------------------------
@agent.tool
async def list_product_urls(ctx: RunContext[PydanticAIDeps]) -> List[str]:
    """
    Get all unique product page URLs stored in Supabase.
    """
    try:
        result = ctx.deps.supabase.from_('partselect_chunks') \
            .select('url') \
            .execute()

        return sorted(set(row['url'] for row in result.data)) if result.data else []
    except Exception as e:
        print(f"Error listing URLs: {e}")
        return []

# -----------------------------------
# Tool 4: Fetch Full Page Content by URL
# -----------------------------------
@agent.tool
async def get_page_content(ctx: RunContext[PydanticAIDeps], url: str) -> str:
    """
    Retrieve all chunks for a product page given its URL.
    """
    try:
        result = ctx.deps.supabase.from_('partselect_chunks') \
            .select('content') \
            .eq('url', url) \
            .execute()

        if not result.data:
            return f"No content found for {url}"

        return "\n\n".join([r['content'] for r in result.data])
    except Exception as e:
        return f"Error retrieving page content: {str(e)}"