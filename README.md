# agent

The actual voice AI: a Python [`livekit-agents`](https://docs.livekit.io/agents/)
worker that joins a LiveKit room and runs speech-to-text (faster-whisper) →
LLM (Ollama) → text-to-speech (Piper) — all local, no paid APIs.

This is one piece of a three-part demo: a `frontend` (React) a user talks to,
a `backend` (NestJS) that mints the LiveKit tokens the frontend uses to join a
room, and this `agent`. The agent is an independent LiveKit client of the same
project — it doesn't talk to the backend directly. Once registered, LiveKit
Cloud automatically dispatches it into any room that gets created.

## Setup

**Use Python 3.13, not the system's 3.14** — `piper-tts` doesn't ship 3.14
wheels yet. If you don't have 3.13:

```bash
brew install python@3.13
```

Then:

```bash
/opt/homebrew/bin/python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` — same LiveKit Cloud project as the `backend`:

| Var | Required | Notes |
|---|---|---|
| `LIVEKIT_URL` / `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` | **yes** | same LiveKit Cloud project as `backend` |
| `OLLAMA_BASE_URL` | no | defaults to `http://localhost:11434/v1` |
| `OLLAMA_MODEL` | no | defaults to `llama3.2:3b` — **must already be pulled** (`ollama pull llama3.2:3b`) |
| `WHISPER_MODEL` | no | defaults to `tiny.en` — see note below before bumping this up |
| `WHISPER_DEVICE` / `WHISPER_COMPUTE_TYPE` | no | default to `cpu` / `int8` |
| `PIPER_VOICE` | no | defaults to `en_US-lessac-medium` — **must be downloaded first**, see below |
| `PIPER_MODEL_DIR` | no | defaults to `models/piper` |

### Download the Piper voice

Not bundled with the package — one-time download:

```bash
python -m piper.download_voices en_US-lessac-medium --download-dir models/piper
```

(swap the voice name if you change `PIPER_VOICE`; `models/` is gitignored)

### About `WHISPER_MODEL`

Defaults to `tiny.en` deliberately, not for accuracy but for reliability: the
larger `small.en` model hung repeatedly downloading from Hugging Face Hub in
testing (unrelated to this code — a `huggingface_hub` connection issue on a
slow/flaky network) and left an incomplete, confusing cache. If you want
better accuracy and have a good connection, pre-download it *before* your
first real conversation, not mid-session:

```bash
python -c "from faster_whisper import WhisperModel; WhisperModel('small.en')"
```

Then set `WHISPER_MODEL=small.en` in `.env`.

### Confirm Ollama is ready

```bash
ollama list   # confirm OLLAMA_MODEL is in this list; if not: ollama pull <model>
```

## Run

```bash
source .venv/bin/activate
python -m voice_agent.main dev
```

Wait for `registered worker {"id": "AW_...", ...}` — that means it's connected
to LiveKit Cloud and will automatically join any room the frontend creates.
Leave it running; no need to restart it between conversations (only if you
change the Python source — this CLI doesn't hot-reload).

## Structure

```
voice_agent/
├── config.py            # env vars
├── prompts.py           # the agent's system prompt — single source of truth,
│                         # imported by pipeline.py rather than duplicated
├── pipeline.py           # builds the AgentSession (VAD + STT + LLM + TTS) + worker entrypoint
├── main.py               # CLI entrypoint (`python -m voice_agent.main`)
└── plugins/
    ├── llm.py             # Ollama via the official `openai` plugin (with_ollama)
    ├── faster_whisper_stt.py  # custom — no official livekit-agents plugin exists
    └── piper_tts.py           # custom — no official livekit-agents plugin exists
```

`pipeline.py` explicitly sets VAD-based turn detection
(`turn_handling=TurnHandlingOptions(turn_detection="vad")`) rather than the
default, which tries a cloud endpoint and then a separate model download
before falling back — both unnecessary network calls for what local
voice-activity detection already handles.
