import mimetypes
from pathlib import Path
from typing import Any, Dict, Optional
from sarvamai import SarvamAI


class AudioTranscriber:
    """Transcribes and translates voice confirmations using Sarvam Saaras v4 STT."""

    def __init__(self, client: SarvamAI):
        self.client = client

    def transcribe_voice_confirmation(
        self,
        audio_path: str,
        translate_to_english: bool = True,
    ) -> Dict[str, Any]:
        """Transcribes voice confirmation audio and optionally translates to English.

        Args:
            audio_path: Path to the recorded audio file (WAV, MP3, M4A, OGG, etc.).
            translate_to_english: Whether to generate an English translation for auditing.

        Returns:
            Dict containing transcript, language_code, and optional translated_transcript.
        """
        path = Path(audio_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Audio file not found: {path}")

        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type:
            ext = path.suffix.lower()
            if ext == ".wav":
                mime_type = "audio/wav"
            elif ext == ".mp3":
                mime_type = "audio/mpeg"
            elif ext in [".m4a", ".mp4"]:
                mime_type = "audio/mp4"
            else:
                mime_type = "audio/wav"

        # 1. Primary transcription (native language verbatim / code-mixed)
        with open(path, "rb") as f:
            audio_bytes = f.read()

        file_payload = (path.name, audio_bytes, mime_type)

        primary_res = self.client.speech_to_text.transcribe(
            file=file_payload,
            model="saaras:v4",
            mode="transcribe",
            with_timestamps=True,
        )

        detected_lang = getattr(primary_res, "language_code", None)
        native_transcript = getattr(primary_res, "transcript", "") or ""
        lang_prob = getattr(primary_res, "language_probability", None)

        translated_transcript: Optional[str] = None

        # 2. If the spoken language is non-English and translation is requested
        if translate_to_english and detected_lang and detected_lang != "en-IN":
            try:
                trans_file_payload = (path.name, audio_bytes, mime_type)
                trans_res = self.client.speech_to_text.transcribe(
                    file=trans_file_payload,
                    model="saaras:v4",
                    mode="translate",
                )
                translated_transcript = getattr(trans_res, "transcript", None)
            except Exception:
                # Fall back gracefully if translate mode is not available for specific codec
                translated_transcript = None

        raw_ts = getattr(primary_res, "timestamps", None)
        ts_serializable = None
        if raw_ts is not None:
            if hasattr(raw_ts, "model_dump"):
                ts_serializable = raw_ts.model_dump()
            elif hasattr(raw_ts, "dict"):
                ts_serializable = raw_ts.dict()
            else:
                ts_serializable = str(raw_ts)

        return {
            "transcript": native_transcript,
            "language_code": detected_lang or "unknown",
            "language_probability": lang_prob,
            "translated_transcript": translated_transcript or native_transcript,
            "timestamps": ts_serializable,
        }
