"""Model Forge API"""
from .routes import router
from .routes_v2 import router as router_v2

__all__ = ["router", "router_v2"]
