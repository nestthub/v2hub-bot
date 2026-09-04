from .admin import router as admin_router
from .help import router as help_router
from .provider import router as provider_router
from .start import router as start_router
from .support import router as support_router
from .token import router as token_router

__all__ = [
    "admin_router",
    "help_router",
    "provider_router",
    "start_router",
    "support_router",
    "token_router",
]
