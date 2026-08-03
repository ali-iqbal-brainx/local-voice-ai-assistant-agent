from livekit.agents import Agent, AgentSession, JobContext, TurnHandlingOptions
from livekit.plugins import silero

from .plugins import build_llm, build_stt, build_tts
from .prompts import VOICE_ASSISTANT_INSTRUCTIONS


# NOTE: this targets the AgentSession-based API (livekit-agents 1.x). Check
# docs.livekit.io/agents against the installed version if this has moved on.
async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    vad = silero.VAD.load()
    session = AgentSession(
        stt=build_stt(vad),
        llm=build_llm(),
        tts=build_tts(),
        vad=vad,
        # Default turn detection tries a cloud endpoint, then falls back to
        # downloading a local model — both network calls we don't need. VAD-based
        # (silence/end-of-speech) turn detection needs nothing extra and is enough
        # for this demo.
        turn_handling=TurnHandlingOptions(turn_detection="vad"),
    )

    await session.start(agent=Agent(instructions=VOICE_ASSISTANT_INSTRUCTIONS), room=ctx.room)
