__all__ = (
    'admin_router',
    'users_router'
)

from .admin import router as admin_router
from .users import router as users_router
