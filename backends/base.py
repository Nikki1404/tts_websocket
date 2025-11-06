import asyncio
from typing import Dict, AsyncGenerator, Tuple, Type

_BACKENDS = {}

def register(cls):
    """Register a backend class by its .name attribute."""
    if not hasattr(cls, "name"):
        raise ValueError(f"Backend {cls} missing .name")
    _BACKENDS[cls.name] = cls
    return cls

def get_backend(name: str) -> Type["Backend"]:
    return _BACKENDS.get(name)

class Backend:
    name = "base"
    async def stream(self, payload: Dict) -> AsyncGenerator[Tuple[str, Dict], None]:
        raise NotImplementedError
