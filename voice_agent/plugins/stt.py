from livekit.agents import stt, vad as agents_vad

from .. import config
from .faster_whisper_stt import FasterWhisperSTT


def build_stt(vad: agents_vad.VAD) -> stt.STT:
    # faster-whisper is a batch (non-streaming) engine — StreamAdapter combines it
    # with the shared VAD instance to produce the streaming interface AgentSession
    # expects. `vad` should be the same instance passed to AgentSession(vad=...),
    # not a second one, to avoid loading the Silero model twice.
    whisper_stt = FasterWhisperSTT(
        model_size=config.WHISPER_MODEL,
        device=config.WHISPER_DEVICE,
        compute_type=config.WHISPER_COMPUTE_TYPE,
    )
    return stt.StreamAdapter(stt=whisper_stt, vad=vad)
