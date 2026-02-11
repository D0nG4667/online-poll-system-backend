# Import authentication extensions to ensure drf-spectacular discovery
try:
    from . import authentication_extensions  # noqa
except ImportError:
    pass
