# agent3.py – LiveKit voice agent using the custom RAG tool
from __future__ import annotations
import inspect, os, asyncio
from livekit.agents import (
    AutoSubscribe, JobContext, WorkerOptions, cli,
    Agent, AgentSession, llm,
)
from livekit.plugins import openai
from dotenv import load_dotenv
from api import AssistantFnc
from prompts import INSTRUCTIONS, WELCOME_MESSAGE

load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

def make_realtime_model():
    sig = inspect.signature(openai.realtime.RealtimeModel)
    cfg = {
        "temperature": 0.8,
        "model": "gpt-4o-realtime-preview",
        "voice": "echo",
        "api_key": OPENAI_KEY,
    }
    return openai.realtime.RealtimeModel(
        **{k: v for k, v in cfg.items() if k in sig.parameters}
    )

async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    await ctx.wait_for_participant()

    model         = make_realtime_model()
    assistant_fnc = AssistantFnc()
    assistant     = AgentSession(llm=model)

    await assistant.start(
        Agent(
            instructions=INSTRUCTIONS,
            tools=assistant_fnc._tools  # includes sunset17_search & save_lead
        ),
        room=ctx.room,
    )

    await assistant.generate_reply(user_input=WELCOME_MESSAGE)

    @assistant.on("user_speech_committed")
    def _on_commit(msg: llm.ChatMessage):
        # relay user text straight to LLM – the agent will auto‑invoke sunset17_search
        asyncio.create_task(
            assistant.generate_reply(user_input=msg.content)
        )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
