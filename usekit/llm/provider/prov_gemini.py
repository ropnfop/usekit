# Path: usekit.llm.provider.prov_gemini.py
# -----------------------------------------------------------------------
#  Google Gemini provider (genai SDK + REST fallback)
#  PATCH 2026-06-14: add multimodal image support.
#    - images ride in config["images"] = [{"path": str, "mime_type": str?}]
#    - bytes are read from disk (frontend already saves via /api/upload)
#    - SDK  path -> types.Part.from_bytes(...)
#    - REST path -> {"inlineData": {"mimeType": ..., "data": <base64>}}
#  Also: default model bumped 2.0-flash -> 2.5-flash
#        (gemini-2.0-flash was shut down on 2026-06-01).
# -----------------------------------------------------------------------

import time
import base64
import mimetypes
import io
import wave

from usekit.llm.provider import ProviderBase

# Safe default. gemini-2.0-flash reached end-of-life on 2026-06-01.
_DEFAULT_MODEL = "gemini-2.5-flash"
# TTS: known-good preview model + default voice. Gemini TTS returns headerless
# 24kHz/16-bit/mono PCM (NOT mp3) — it must be WAV-wrapped before playback.
_DEFAULT_TTS_MODEL = "gemini-2.5-flash-preview-tts"
_DEFAULT_VOICE = "Kore"


def _read_image(path: str):
    """Read an image file from disk -> (raw_bytes, guessed_mime).

    The frontend uploads via /api/upload which saves the resized JPEG to the
    Termux filesystem and returns its absolute path. We re-read those bytes
    here so they can be attached to the model request as real image data.
    """
    with open(path, "rb") as f:
        data = f.read()
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    return data, mime


class ProvGemini(ProviderBase):
    """Google Gemini SDK adapter (text + image)."""

    name = "gemini"

    def __init__(self):
        self._client = None

    def connect(self, config: dict) -> dict:
        """Connect via google-genai SDK."""
        api_key = config.get("api_key", "")
        model = config.get("model", _DEFAULT_MODEL)
        mode = config.get("mode", "sdk")

        if mode == "sdk":
            try:
                from google import genai
                from google.genai import types as genai_types
            except ImportError:
                raise ImportError(
                    "[prov_gemini] google-genai not installed. "
                    "pip install google-genai"
                )

            if not api_key:
                raise ValueError("[prov_gemini] api_key required")

            self._client = genai.Client(
                api_key=api_key,
                http_options=genai_types.HttpOptions(api_version="v1"),
            )

            return {
                "provider": self.name,
                "mode": mode,
                "model": model,
                "api_key": api_key,
            }

        elif mode == "rest":
            if not api_key:
                raise ValueError("[prov_gemini.rest] api_key required")
            return {
                "provider": self.name,
                "mode": "rest",
                "model": model,
                "api_key": api_key,
                "endpoint": "https://generativelanguage.googleapis.com/v1",
            }

        raise ValueError(f"[prov_gemini] unknown mode: {mode}")

    # ------------------------------------------------------------------
    #  Image part builders
    # ------------------------------------------------------------------
    @staticmethod
    def _image_parts_sdk(images, genai_types):
        """Build SDK image Parts from config['images'] entries."""
        parts = []
        for img in images or []:
            path = img.get("path")
            if not path:
                continue
            data, guessed = _read_image(path)
            mime = img.get("mime_type") or guessed
            parts.append(genai_types.Part.from_bytes(data=data, mime_type=mime))
        return parts

    @staticmethod
    def _image_parts_rest(images):
        """Build REST inlineData parts from config['images'] entries."""
        parts = []
        for img in images or []:
            path = img.get("path")
            if not path:
                continue
            data, guessed = _read_image(path)
            mime = img.get("mime_type") or guessed
            b64 = base64.b64encode(data).decode("ascii")
            parts.append({"inlineData": {"mimeType": mime, "data": b64}})
        return parts

    # ------------------------------------------------------------------
    #  Send
    # ------------------------------------------------------------------
    def send(self, prompt: str, config: dict) -> dict:
        """Send prompt (+ optional images) to Gemini."""
        mode = config.get("mode", "sdk")
        model = config.get("model", _DEFAULT_MODEL)

        temperature = config.get("temperature", 0.3)
        max_tokens = config.get("max_tokens", 1200)
        images = config.get("images") or []  # [{"path": str, "mime_type": str?}]
        search = bool(config.get("search"))   # google_search grounding on/off

        started = time.time()

        try:
            if mode == "sdk" and self._client:
                from google.genai import types as genai_types
                gen_kwargs = {
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
                if search:
                    # Grounding: model decides when to search and cites sources
                    # (groundingMetadata) in the response.
                    gen_kwargs["tools"] = [
                        genai_types.Tool(google_search=genai_types.GoogleSearch())
                    ]
                gen_config = genai_types.GenerateContentConfig(**gen_kwargs)
                # Multimodal contents: text first, then any image parts.
                # A bare string still works for the text-only case.
                img_parts = self._image_parts_sdk(images, genai_types)
                contents = [prompt, *img_parts] if img_parts else prompt

                resp = self._client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=gen_config,
                )
                elapsed = round(time.time() - started, 3)
                return {
                    "_sdk_response": resp,
                    "_elapsed": elapsed,
                    "_status_code": 200,
                    "_mode": "sdk",
                    "_n_images": len(img_parts),
                }

            elif mode == "rest":
                import requests as req
                api_key = config.get("api_key", "")
                url = (
                    f"https://generativelanguage.googleapis.com/v1/"
                    f"models/{model}:generateContent?key={api_key}"
                )
                # text part first, then inlineData image parts.
                parts = [{"text": prompt}]
                parts.extend(self._image_parts_rest(images))
                body = {"contents": [{"parts": parts}]}
                if search:
                    body["tools"] = [{"google_search": {}}]

                resp = req.post(url, json=body, timeout=30)
                elapsed = round(time.time() - started, 3)
                data = resp.json()
                data["_elapsed"] = elapsed
                data["_status_code"] = resp.status_code
                data["_mode"] = "rest"
                return data

        except Exception as e:
            elapsed = round(time.time() - started, 3)
            return {"_elapsed": elapsed, "_status_code": None, "_error": str(e)}

        return {"_elapsed": 0, "_error": "no valid mode"}

    def ping(self, config: dict) -> dict:
        """Minimal generate for health check."""
        # Strip images for ping so a stray attachment never blocks a probe.
        ping_cfg = {**config, "max_tokens": 5, "temperature": 0, "images": []}
        result = self.send("Hi", ping_cfg)
        ok = "_error" not in result
        return {"ok": ok, "elapsed": result.get("_elapsed", 0)}

    # ------------------------------------------------------------------
    #  TTS (text -> speech)
    # ------------------------------------------------------------------
    @staticmethod
    def _pcm_to_wav(pcm: bytes, rate: int = 24000, channels: int = 1, width: int = 2) -> bytes:
        """Wrap headerless 16-bit PCM (what Gemini TTS returns) into a WAV
        container so browsers/players can actually play it. Saving the raw
        bytes as .mp3 produces an unplayable file — this is the key gotcha."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(width)
            wf.setframerate(rate)
            wf.writeframes(pcm)
        return buf.getvalue()

    def synthesize(self, text: str, config: dict) -> dict:
        """Text -> speech. Returns {wav: bytes, mime, _elapsed} or {_error}.

        REST mode is used by default (no client connection needed, and avoids
        the SDK v1/v1beta mismatch for preview TTS models).
        """
        mode = config.get("mode", "rest")
        model = config.get("tts_model", _DEFAULT_TTS_MODEL)
        voice = config.get("voice", _DEFAULT_VOICE)
        started = time.time()

        try:
            if mode == "sdk" and self._client:
                from google.genai import types as t
                cfg = t.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=t.SpeechConfig(
                        voice_config=t.VoiceConfig(
                            prebuilt_voice_config=t.PrebuiltVoiceConfig(voice_name=voice)
                        )
                    ),
                )
                resp = self._client.models.generate_content(
                    model=model, contents=text, config=cfg,
                )
                pcm = resp.candidates[0].content.parts[0].inline_data.data  # raw bytes
                return {
                    "wav": self._pcm_to_wav(pcm),
                    "mime": "audio/wav",
                    "_elapsed": round(time.time() - started, 3),
                }

            # REST (default)
            import requests as req
            api_key = config.get("api_key", "")
            if not api_key:
                return {"_error": "[tts] api_key required"}
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/"
                f"models/{model}:generateContent?key={api_key}"
            )
            body = {
                "contents": [{"parts": [{"text": text}]}],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {
                        "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}
                    },
                },
            }
            r = req.post(url, json=body, timeout=60)
            if r.status_code != 200:
                return {"_error": f"tts http {r.status_code}: {r.text[:200]}"}
            data = r.json()
            pcm_b64 = data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
            return {
                "wav": self._pcm_to_wav(base64.b64decode(pcm_b64)),
                "mime": "audio/wav",
                "_elapsed": round(time.time() - started, 3),
            }

        except Exception as e:
            return {"_error": str(e), "_elapsed": round(time.time() - started, 3)}

    def close(self) -> None:
        self._client = None
