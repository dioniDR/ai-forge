"""
AI Forge - AI Providers Package
Módulo para conectar con diferentes proveedores de IA
"""

from .base_provider import BaseAIProvider
from .ollama_provider import OllamaProvider
from .provider_factory import ProviderFactory

__all__ = [
    "BaseAIProvider",
    "OllamaProvider", 
    "ProviderFactory"
]

# Versión del módulo de proveedores
__version__ = "1.0.0"