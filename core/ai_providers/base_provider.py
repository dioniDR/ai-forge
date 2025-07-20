"""
AI Forge - Base AI Provider
Clase base abstracta para todos los proveedores de IA
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator
import asyncio
import json


class BaseAIProvider(ABC):
    """
    Clase base para todos los proveedores de IA
    
    Define la interfaz común que deben implementar todos los proveedores
    """
    
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__.replace('Provider', '').lower()
        self._config = {}
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Verifica si el proveedor está disponible y configurado correctamente
        
        Returns:
            True si el proveedor está disponible
        """
        pass
    
    @abstractmethod
    async def get_available_models(self) -> List[str]:
        """
        Obtiene la lista de modelos disponibles
        
        Returns:
            Lista de nombres de modelos
        """
        pass
    
    @abstractmethod
    async def chat(
        self, 
        message: str, 
        model: str = None, 
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = None,
        **kwargs
    ) -> str:
        """
        Envía un mensaje de chat y retorna la respuesta completa
        
        Args:
            message: Mensaje del usuario
            model: Modelo a usar (opcional)
            system_prompt: Prompt del sistema (opcional)
            temperature: Temperatura de generación
            max_tokens: Máximo número de tokens
            **kwargs: Parámetros adicionales específicos del proveedor
            
        Returns:
            Respuesta completa del modelo
        """
        pass
    
    @abstractmethod
    async def chat_stream(
        self, 
        message: str, 
        model: str = None, 
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Envía un mensaje de chat y retorna un stream de la respuesta
        
        Args:
            message: Mensaje del usuario
            model: Modelo a usar (opcional)
            system_prompt: Prompt del sistema (opcional)
            temperature: Temperatura de generación
            max_tokens: Máximo número de tokens
            **kwargs: Parámetros adicionales específicos del proveedor
            
        Yields:
            Fragmentos de la respuesta en formato server-sent events
        """
        pass
    
    def health_check(self) -> bool:
        """
        Realiza un health check básico del proveedor
        
        Returns:
            True si el proveedor está funcionando correctamente
        """
        try:
            return self.is_available()
        except Exception:
            return False
    
    def get_provider_name(self) -> str:
        """
        Obtiene el nombre del proveedor
        
        Returns:
            Nombre del proveedor
        """
        return self.name
    
    def get_provider_type(self) -> str:
        """
        Obtiene el tipo de proveedor (local, cloud, etc.)
        
        Returns:
            Tipo de proveedor
        """
        return "unknown"
    
    def get_config_info(self) -> Dict[str, Any]:
        """
        Obtiene información de configuración del proveedor
        
        Returns:
            Diccionario con información de configuración
        """
        return {
            "name": self.name,
            "type": self.get_provider_type(),
            "config_keys": list(self._config.keys()) if hasattr(self, '_config') else []
        }
    
    def set_config(self, config: Dict[str, Any]):
        """
        Establece la configuración del proveedor
        
        Args:
            config: Diccionario de configuración
        """
        self._config.update(config)
    
    def get_config(self, key: str = None, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración
        
        Args:
            key: Clave de configuración (si None, retorna toda la config)
            default: Valor por defecto si la clave no existe
            
        Returns:
            Valor de configuración
        """
        if key is None:
            return self._config.copy()
        return self._config.get(key, default)
    
    async def validate_model(self, model: str) -> bool:
        """
        Valida si un modelo está disponible
        
        Args:
            model: Nombre del modelo a validar
            
        Returns:
            True si el modelo está disponible
        """
        try:
            available_models = await self.get_available_models()
            return model in available_models
        except Exception:
            return False
    
    def _format_stream_response(self, content: str, done: bool = False) -> str:
        """
        Formatea una respuesta para streaming compatible con Server-Sent Events
        
        Args:
            content: Contenido de la respuesta
            done: Si la respuesta está completa
            
        Returns:
            String formateado para SSE
        """
        data = {
            "response": content,
            "done": done
        }
        return f"data: {json.dumps(data)}\n\n"
    
    def _handle_error(self, error: Exception, context: str = "") -> str:
        """
        Maneja errores de manera consistente
        
        Args:
            error: Excepción ocurrida
            context: Contexto donde ocurrió el error
            
        Returns:
            Mensaje de error formateado
        """
        error_msg = f"Error in {self.name}"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {str(error)}"
        
        return error_msg
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Prueba la conexión con el proveedor
        
        Returns:
            Diccionario con resultados de la prueba
        """
        result = {
            "provider": self.name,
            "available": False,
            "models_count": 0,
            "test_message": None,
            "error": None,
            "response_time": None
        }
        
        try:
            import time
            start_time = time.time()
            
            # Verificar disponibilidad
            result["available"] = self.is_available()
            
            if result["available"]:
                # Contar modelos
                models = await self.get_available_models()
                result["models_count"] = len(models)
                
                # Test de mensaje simple (si hay modelos disponibles)
                if models:
                    test_response = await self.chat(
                        message="Hello", 
                        model=models[0],
                        max_tokens=10
                    )
                    result["test_message"] = test_response[:50] + "..." if len(test_response) > 50 else test_response
            
            result["response_time"] = round((time.time() - start_time) * 1000, 2)  # ms
            
        except Exception as e:
            result["error"] = str(e)
        
        return result