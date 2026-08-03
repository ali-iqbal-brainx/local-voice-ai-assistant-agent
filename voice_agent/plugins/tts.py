from pathlib import Path

from livekit.agents import tts

from .. import config
from .piper_tts import PiperTTS


def build_tts() -> tts.TTS:
    # Voice files aren't bundled — download once with:
    #   python -m piper.download_voices <voice> --download-dir <PIPER_MODEL_DIR>
    model_dir = Path(config.PIPER_MODEL_DIR)
    model_path = model_dir / f"{config.PIPER_VOICE}.onnx"
    config_path = model_dir / f"{config.PIPER_VOICE}.onnx.json"
    return PiperTTS(model_path=model_path, config_path=config_path)
