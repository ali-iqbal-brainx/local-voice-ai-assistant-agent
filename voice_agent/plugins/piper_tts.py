from __future__ import annotations

import asyncio
from pathlib import Path

from livekit.agents import DEFAULT_API_CONNECT_OPTIONS, APIConnectOptions, tts
from piper import PiperVoice


class PiperChunkedStream(tts.ChunkedStream):
    def __init__(self, *, tts: "PiperTTS", input_text: str, conn_options: APIConnectOptions) -> None:
        super().__init__(tts=tts, input_text=input_text, conn_options=conn_options)
        self._piper_tts: PiperTTS = tts

    def _synthesize_sync(self) -> bytes:
        chunks = self._piper_tts.voice.synthesize(self.input_text)
        return b"".join(chunk.audio_int16_bytes for chunk in chunks)

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        # Piper's synthesize() is blocking CPU-bound ONNX inference — run it off
        # the event loop, same reasoning as FasterWhisperSTT.
        loop = asyncio.get_running_loop()
        pcm_bytes = await loop.run_in_executor(None, self._synthesize_sync)

        output_emitter.initialize(
            request_id=str(id(self)),
            sample_rate=self._piper_tts.sample_rate,
            num_channels=self._piper_tts.num_channels,
            # "audio/pcm" tells AudioEmitter these are already-decoded raw int16
            # samples — no ffmpeg/av decoding needed, unlike compressed formats.
            mime_type="audio/pcm",
        )
        output_emitter.push(pcm_bytes)
        output_emitter.flush()


class PiperTTS(tts.TTS):
    """Wraps Piper (no official livekit-agents plugin exists). Non-streaming:
    the full utterance is synthesized before any audio is pushed."""

    def __init__(self, *, model_path: str | Path, config_path: str | Path | None = None) -> None:
        self.voice = PiperVoice.load(model_path, config_path)
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=self.voice.config.sample_rate,
            num_channels=1,
        )

    def synthesize(
        self, text: str, *, conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS
    ) -> tts.ChunkedStream:
        return PiperChunkedStream(tts=self, input_text=text, conn_options=conn_options)
