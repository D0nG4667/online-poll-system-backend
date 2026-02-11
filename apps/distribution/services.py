import io

import qrcode
import qrcode.image.svg
from django.conf import settings
from django.core.cache import cache


class DistributionService:
    @staticmethod
    def get_public_url(poll):
        """
        Returns the absolute public URL for a poll.
        """
        base_url = getattr(settings, "BASE_URL", "http://localhost:8000").rstrip("/")
        return f"{base_url}/polls/{poll.slug}/"

    @classmethod
    def generate_qr_code(cls, poll, img_format="png"):
        """
        Generates a QR code for the poll's public URL.
        Caches the result in Redis to avoid redundant generation.
        """
        cache_key = f"poll_qr_{poll.slug}_{img_format}"
        cached_qr = cache.get(cache_key)
        if cached_qr:
            return cached_qr

        url = cls.get_public_url(poll)

        if img_format == "svg":
            factory = qrcode.image.svg.SvgImage
            img = qrcode.make(url, image_factory=factory)
            stream = io.BytesIO()
            img.save(stream)
            qr_content = stream.getvalue().decode()
        else:
            img = qrcode.make(url)
            stream = io.BytesIO()
            img.save(stream)
            qr_content = stream.getvalue()

        # Cache for 1 day
        cache.set(cache_key, qr_content, 86400)
        return qr_content

    @classmethod
    def get_embed_code(cls, poll):
        """
        Returns the iframe embed snippet for a poll.
        """
        public_url = cls.get_public_url(poll)
        return (
            f'<iframe src="{public_url}" width="100%" height="600" '
            'frameborder="0" allowfullscreen></iframe>'
        )
