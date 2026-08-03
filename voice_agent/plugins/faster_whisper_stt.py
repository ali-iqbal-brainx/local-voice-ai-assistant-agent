from __future__ import annotations

import asyncio
import io

from faster_whisper import WhisperModel
from livekit import rtc
from livekit.agents import NOT_GIVEN, APIConnectOptions, NotGivenOr, stt
from livekit.agents.utils import AudioBuffer


class FasterWhisperSTT(stt.STT):
    """Non-streaming STT wrapping faster-whisper. Wrap with `stt.StreamAdapter`
    (+ a VAD) before handing to `AgentSession` — this class only implements batch
    recognize, not the streaming interface."""

    def __init__(
        self,
        *,
        model_size: str = "small.en",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        super().__init__(capabilities=stt.STTCapabilities(streaming=False, interim_results=False))
        self._model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def _transcribe_sync(self, wav_bytes: bytes, language: str | None) -> str:
        segments, _info = self._model.transcribe(io.BytesIO(wav_bytes), language=language)
        return " ".join(segment.text.strip() for segment in segments).strip()

    async def _recognize_impl(
        self,
        buffer: AudioBuffer,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions,
    ) -> stt.SpeechEvent:
        wav_bytes = rtc.combine_audio_frames(buffer).to_wav_bytes()
        lang = None if language is NOT_GIVEN else language

        # WhisperModel.transcribe() returns a lazy generator — the actual decoding
        # happens while iterating it, so both the call AND the iteration must run
        # in the executor thread, or this blocks the event loop.
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(None, self._transcribe_sync, wav_bytes, lang)

        return stt.SpeechEvent(
            type=stt.SpeechEventType.FINAL_TRANSCRIPT,
            alternatives=[stt.SpeechData(language=lang or "en", text=text)],
        )
