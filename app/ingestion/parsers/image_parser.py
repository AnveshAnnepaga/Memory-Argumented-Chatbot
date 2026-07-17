import hashlib
import logging
import base64
from typing import Optional

logger = logging.getLogger("app.ingestion.parsers.image")

try:
    from PIL import Image
    import io as _io
    _PILLOW_AVAILABLE = True
except ImportError:
    _PILLOW_AVAILABLE = False
    logger.info("Pillow not installed. Image processing will be unavailable.")

try:
    from groq import AsyncGroq
    _GROQ_AVAILABLE = True
except ImportError:
    _GROQ_AVAILABLE = False

try:
    import httpx
    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False

_OLLAMA_AVAILABLE = False


class ImageParser:
    """
    Describes image content using a vision-capable LLM.
    Priority: Groq LLaVA (free API) -> Ollama LLaVA (local) -> fallback text.
    """

    def __init__(self):
        self._description_cache: dict = {}
        self._groq_client = None
        self._groq_available = True

    def _get_groq_client(self):
        if self._groq_client is None and _GROQ_AVAILABLE:
            try:
                from app.core.config import settings
                api_key = getattr(settings, "GROQ_API_KEY", "")
                if api_key and api_key != "your_groq_api_key_here":
                    self._groq_client = AsyncGroq(api_key=api_key, timeout=15)
                else:
                    self._groq_available = False
            except Exception:
                self._groq_available = False
        return self._groq_client

    def _compute_image_hash(self, image_bytes: bytes) -> str:
        return hashlib.sha256(image_bytes).hexdigest()[:16]

    async def _describe_via_groq(self, image_bytes: bytes, filename: str) -> Optional[str]:
        if not self._groq_available:
            return None
        client = self._get_groq_client()
        if not client:
            return None
        try:
            encoded = base64.b64encode(image_bytes).decode("utf-8")
            import mimetypes
            mime, _ = mimetypes.guess_type(filename)
            if not mime:
                mime = "image/png"
            data_url = f"data:{mime};base64,{encoded}"

            import asyncio
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model="llava-v1.5-7b-4096-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Describe this image in detail. Include objects, people, text, colors, layout, and any notable elements."},
                                {"type": "image_url", "image_url": {"url": data_url}},
                            ],
                        }
                    ],
                    max_tokens=512,
                    temperature=0.2,
                ),
                timeout=25,
            )
            desc = response.choices[0].message.content if response.choices else None
            if desc and desc.strip():
                logger.info(f"Groq LLaVA described image '{filename}' ({len(desc.split())} words)")
                return desc.strip()
        except Exception as e:
            logger.warning(f"Groq LLaVA image description failed for '{filename}': {e}. Falling back.")
            self._groq_available = False
        return None

    async def _describe_via_ollama(self, image_bytes: bytes, filename: str) -> Optional[str]:
        if not _HTTPX_AVAILABLE:
            return None
        try:
            import base64
            encoded = base64.b64encode(image_bytes).decode("utf-8")
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llava:7b",
                        "prompt": "Describe this image in detail. Include objects, people, text, colors, layout, and any notable elements.",
                        "images": [encoded],
                        "stream": False,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    desc = data.get("response", "").strip()
                    if desc:
                        logger.info(f"Ollama LLaVA described image '{filename}' ({len(desc.split())} words)")
                        return desc
        except Exception as e:
            logger.debug(f"Ollama image description failed: {e}")
        return None

    async def parse(self, file_bytes: bytes, filename: str = "") -> Optional["FileParseResult"]:
        from app.ingestion.parsers import FileParseResult

        img_hash = self._compute_image_hash(file_bytes)
        if img_hash in self._description_cache:
            cached_desc = self._description_cache[img_hash]
            logger.info(f"Using cached description for image '{filename}'")
            return FileParseResult(
                text=cached_desc,
                title=filename or "Uploaded Image",
                file_type="image_description",
                metadata={"image_hash": img_hash, "cached": True},
                raw_bytes=file_bytes,
            )

        # Basic image info via Pillow
        width = height = 0
        format_name = "unknown"
        if _PILLOW_AVAILABLE:
            try:
                import io
                img = Image.open(io.BytesIO(file_bytes))
                width, height = img.size
                format_name = img.format or "unknown"
                img.close()
            except Exception:
                pass

        # Describe via Groq LLaVA first, then Ollama fallback
        description = await self._describe_via_groq(file_bytes, filename)
        if not description:
            description = await self._describe_via_ollama(file_bytes, filename)
        if not description:
            fallback_text = (
                f"[Image: {filename} | Dimensions: {width}x{height} | Format: {format_name} | "
                f"Size: {len(file_bytes)} bytes | Visual description could not be generated]"
            )
            logger.warning(f"Image description failed for '{filename}', using fallback text")
            description = fallback_text

        self._description_cache[img_hash] = description
        title = filename.replace("_", " ").replace("-", " ")

        return FileParseResult(
            text=description,
            title=title,
            file_type="image_description",
            metadata={
                "image_hash": img_hash,
                "width": width,
                "height": height,
                "format": format_name,
                "size_bytes": len(file_bytes),
            },
            raw_bytes=file_bytes,
        )


image_parser = ImageParser()
