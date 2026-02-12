import io
from typing import cast

import qrcode
import qrcode.image.svg
from django.conf import settings
from django.core.cache import cache

from apps.polls.models import Poll


class DistributionService:
    @staticmethod
    def get_public_url(poll: Poll) -> str:
        """
        Returns the absolute public URL for a poll.
        """
        base_url = getattr(settings, "BASE_URL", "http://localhost:8000").rstrip("/")
        return f"{base_url}/polls/{poll.slug}/"

    @classmethod
    def generate_qr_code(cls, poll: Poll, img_format: str = "png") -> str | bytes:
        """
        Generates a QR code for the poll's public URL.
        Caches the result in Redis to avoid redundant generation.
        """
        cache_key = f"poll_qr_{poll.slug}_{img_format}"
        cached_qr = cache.get(cache_key)
        if cached_qr:
            return cast(str | bytes, cached_qr)

        url = cls.get_public_url(poll)

        if img_format == "svg":
            factory = qrcode.image.svg.SvgImage
            img = qrcode.make(url, image_factory=factory)
            stream = io.BytesIO()
            img.save(stream)
            qr_content_str = stream.getvalue().decode()
            cache.set(cache_key, qr_content_str, 86400)
            return qr_content_str
        else:
            png_img = qrcode.make(url)
            stream = io.BytesIO()
            png_img.save(stream)
            qr_content_bytes = stream.getvalue()
            cache.set(cache_key, qr_content_bytes, 86400)
            return qr_content_bytes

    @classmethod
    def get_embed_code(cls, poll: Poll) -> str:
        """
        Returns the iframe embed snippet for a poll.
        """
        public_url = cls.get_public_url(poll)
        return (
            f'<iframe src="{public_url}" width="100%" height="600" '
            'frameborder="0" allowfullscreen></iframe>'
        )
