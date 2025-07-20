"""
AI Forge - Provider Factory
Factory para crear y gestionar diferentes proveedores de IA
"""

import os
from typing import Dict, List, Optional, Any
from .base_provider import BaseAIProvider
from .ollama_provider import OllamaProvider


class ProviderFactory:
    """
    Factory para crear y gestionar proveedores de IA
    
    Soporta:
    - Ollama (local)
    - OpenAI (cloud) 
    - Anthropic (cloud)
    - Google AI (cloud)
    - Fallback automático
    """
    
    def __init__(self):
        self._providers = {}
        self._available_providers = {
            'ollama': OllamaProvider,
            # TODO: Agregar otros proveedores
            # 'openai': OpenAIProvider,
            # 'anthropic': AnthropicProvider,
            # 'google': GoogleAIProvider,
        }
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Inicializa los proveedores disponibles"""
        for name, provider_class in self._available_providers.items():
            try:
                provider = provider_class()
                if provider.is_available():
                    self._providers[name] = provider
                    print(f"✅ Provider '{name}' initialized successfully")
                else:
                    print(f"⚠️ Provider '{name}' not available (check configuration)")
            except Exception as e:
                print(f"❌ Failed to initialize provider '{name}': {e}")
    
    def get_provider(self, name: str) -> BaseAIProvider:
        """
        Obtiene un proveedor específico
        
        Args:
            name: Nombre del proveedor
            
        Returns:
            Instancia del proveedor
            
        Raises:
            ValueError: Si el proveedor no está disponible
        """
        if name not in self._providers:
            available = list(self._providers.keys())
            raise ValueError(f"Provider '{name}' not available. Available providers: {available}")
        
        return self._providers[name]
    
    def get_available_providers(self) -> List[str]:
        """
        Obtiene lista de proveedores disponibles
        
        Returns:
            Lista de nombres de proveedores
        """
        return list(self._providers.keys())
    
    def get_best_provider_for_task(self, task_type: str = "general") -> Optional[BaseAIProvider]:
        """
        Obtiene el mejor proveedor para un tipo de tarea específica
        
        Args:
            task_type: Tipo de tarea (math, coding, creative, etc.)
            
        Returns:
            Mejor proveedor disponible para la tarea
        """
        # Mapeo de tareas a proveedores preferidos
        task_preferences = {
            "math": ["ollama", "openai", "google"],
            "coding": ["anthropic", "ollama", "openai"], 
            "creative": ["anthropic", "openai", "ollama"],
            "translation": ["google", "openai", "ollama"],
            "analysis": ["anthropic", "openai", "ollama"],
            "general": ["ollama", "openai", "anthropic"]
        }
        
        preferred_providers = task_preferences.get(task_type, task_preferences["general"])
        
        for provider_name in preferred_providers:
            if provider_name in self._providers:
                return self._providers[provider_name]
        
        # Fallback al primer proveedor disponible
        if self._providers:
            return next(iter(self._providers.values()))
        
        return None
    
    def test_providers(self) -> Dict[str, Dict[str, Any]]:
        """
        Prueba todos los proveedores disponibles
        
        Returns:
            Diccionario con resultados de las pruebas
        """
        results = {}
        
        for name, provider in self._providers.items():
            try:
                # Test básico
                start_time = __import__('time').time()
                is_healthy = provider.health_check()
                response_time = __import__('time').time() - start_time
                
                results[name] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "response_time": round(response_time * 1000, 2),  # ms
                    "models_available": len(provider.get_available_models()) if is_healthy else 0,
                    "error": None
                }
                
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "response_time": None,
                    "models_available": 0,
                    "error": str(e)
                }
        
        return results
    
    def get_provider_info(self, provider_name: str = None) -> Dict[str, Any]:
        """
        Obtiene información detallada de uno o todos los proveedores
        
        Args:
            provider_name: Nombre específico del proveedor (opcional)
            
        Returns:
            Información de proveedores
        """
        if provider_name:
            if provider_name not in self._providers:
                raise ValueError(f"Provider '{provider_name}' not available")
            
            provider = self._providers[provider_name]
            return {
                "name": provider_name,
                "type": provider.get_provider_type(),
                "available": provider.is_available(),
                "models": provider.get_available_models(),
                "config": provider.get_config_info()
            }
        else:
            # Información de todos los proveedores
            info = {}
            for name, provider in self._providers.items():
                info[name] = {
                    "type": provider.get_provider_type(),
                    "available": provider.is_available(),
                    "models_count": len(provider.get_available_models()),
                    "config": provider.get_config_info()
                }
            return info
    
    def auto_configure(self) -> Dict[str, str]:
        """
        Configuración automática basada en proveedores disponibles
        
        Returns:
            Configuración recomendada
        """
        config = {}
        
        # Proveedor por defecto
        if "ollama" in self._providers:
            config["default_provider"] = "ollama"
        elif self._providers:
            config["default_provider"] = next(iter(self._providers.keys()))
        else:
            config["default_provider"] = None
        
        # Estrategias por tipo de tarea
        for task_type in ["math", "coding", "creative", "translation", "analysis"]:
            best_provider = self.get_best_provider_for_task(task_type)
            if best_provider:
                config[f"provider_for_{task_type}"] = best_provider.get_provider_name()
        
        # Configuración de fallback
        available_providers = self.get_available_providers()
        if len(available_providers) > 1:
            config["enable_fallback"] = True
            config["fallback_order"] = available_providers
        else:
            config["enable_fallback"] = False
        
        return config
    
    def reload_providers(self):
        """Recarga todos los proveedores"""
        self._providers.clear()
        self._initialize_providers()
    
    def add_custom_provider(self, name: str, provider_class):
        """
        Agrega un proveedor personalizado
        
        Args:
            name: Nombre del proveedor
            provider_class: Clase del proveedor (debe heredar de BaseAIProvider)
        """
        if not issubclass(provider_class, BaseAIProvider):
            raise ValueError("Provider class must inherit from BaseAIProvider")
        
        try:
            provider = provider_class()
            if provider.is_available():
                self._providers[name] = provider
                print(f"✅ Custom provider '{name}' added successfully")
            else:
                print(f"⚠️ Custom provider '{name}' not available")
        except Exception as e:
            print(f"❌ Failed to add custom provider '{name}': {e}")
            raise