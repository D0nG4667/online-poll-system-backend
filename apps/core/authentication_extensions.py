from drf_spectacular.extensions import OpenApiAuthenticationExtension

from apps.core.authentication import MultiAuthenticationBackend


class MultiAuthenticationBackendScheme(OpenApiAuthenticationExtension):
    target_class = MultiAuthenticationBackend
    name = "MultiAuthentication"

    def get_security_definition(self, auto_schema):
        # This backend actually supports multiple methods.
        # We can represent it as a combination or choose the most common one.
        # For documentation purposes, we'll list primary ones in the backend.
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Bearer [JWT] or X-Session-Token [Session Token]",
        }
