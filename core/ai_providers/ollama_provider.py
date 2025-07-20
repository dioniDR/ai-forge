"""
AI Forge - Ollama Provider
Proveedor para conectar con Ollama (IA local)
"""

import os
import json
import time
import httpx
from typing import List, Dict, Any, AsyncGenerator
from .base_provider import BaseAIProvider


class OllamaProvider(BaseAIProvider):
    """
    Proveedor para Ollama - IA local
    
    Características:
    - Conexión a servidor Ollama local
    - Soporte para streaming
    - Gestión automática de modelos
    - Configuración flexible
    """
    
    def __init__(self):
        super().__init__("ollama")
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._models_cache = None
        self._cache_timeout = 300  # 5 minutos
        self._last_cache_time = 0
        
        # Configuración por defecto
        self._config = {
            "base_url": self.base_url,
            "timeout": 60.0,
            "default_model": "llama3.2",
            "stream": True
        }
    
    def is_available(self) -> bool:
        """Verifica si Ollama está disponible"""
        try:
            import httpx
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
    
    def get_provider_type(self) -> str:
        """Retorna el tipo de proveedor"""
        return "local"
    
    async def get_available_models(self) -> List[str]:
        """Obtiene modelos disponibles en Ollama"""
        import time
        
        # Usar cache si es válido
        current_time = time.time()
        if (self._models_cache is not None and 
            current_time - self._last_cache_time < self._cache_timeout):
            return self._models_cache
        
        try:
            async with httpx.AsyncClient(timeout=self._config["timeout"]) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                
                if response.status_code == 200:
                    data = response.json()
                    models = [model["name"] for model in data.get("models", [])]
                    
                    # Actualizar cache
                    self._models_cache = models
                    self._last_cache_time = current_time
                    
                    return models
                else:
                    return []
        except Exception as e:
            print(f"Error getting Ollama models: {e}")
            return []
    
    async def chat(
        self, 
        message: str, 
        model: str = None, 
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = None,
        **kwargs
    ) -> str:
        """Chat sin streaming - retorna respuesta completa"""
        model = model or self._config["default_model"]
        
        payload = {
            "model": model,
            "prompt": message,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        # Agregar system prompt si se proporciona
        if system_prompt:
            payload["system"] = system_prompt
        
        # Agregar parámetros adicionales
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        # Agregar opciones de kwargs
        payload["options"].update({
            k: v for k, v in kwargs.items() 
            if k in ["top_p", "top_k", "repeat_penalty", "num_ctx"]
        })
        
        try:
            async with httpx.AsyncClient(timeout=self._config["timeout"]) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "")
                else:
                    raise Exception(f"Ollama API error: {response.status_code}")
                    
        except Exception as e:
            raise Exception(self._handle_error(e, "chat"))
    
    async def chat_stream(
        self, 
        message: str, 
        model: str = None, 
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Chat con streaming - yields fragmentos de respuesta"""
        model = model or self._config["default_model"]
        
        payload = {
            "model": model,
            "prompt": message,
            "stream": True,
            "options": {
                "temperature": temperature,
            }
        }
        
        # Agregar system prompt si se proporciona
        if system_prompt:
            payload["system"] = system_prompt
        
        # Agregar parámetros adicionales
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        # Agregar opciones de kwargs
        payload["options"].update({
            k: v for k, v in kwargs.items() 
            if k in ["top_p", "top_k", "repeat_penalty", "num_ctx"]
        })
        
        try:
            async with httpx.AsyncClient(timeout=self._config["timeout"]) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    
                    if response.status_code != 200:
                        yield self._format_stream_response(
                            f"Error: Ollama API returned {response.status_code}",
                            done=True
                        )
                        return
                    
                    async for chunk in response.aiter_lines():
                        if chunk:
                            try:
                                data = json.loads(chunk)
                                
                                if "response" in data:
                                    # Enviar fragmento de respuesta
                                    yield self._format_stream_response(
                                        data["response"], 
                                        done=False
                                    )
                                
                                if data.get("done", False):
                                    # Señalar fin de respuesta
                                    yield self._format_stream_response("", done=True)
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            error_msg = self._handle_error(e, "chat_stream")
            yield self._format_stream_response(error_msg, done=True)
    
    def get_config_info(self) -> Dict[str, Any]:
        """Información de configuración específica de Ollama"""
        base_info = super().get_config_info()
        base_info.update({
            "base_url": self.base_url,
            "models_cached": self._models_cache is not None,
            "cache_age": time.time() - self._last_cache_time if self._last_cache_time > 0 else None
        })
        return base_info
    
    async def pull_model(self, model_name: str) -> AsyncGenerator[str, None]:
        """
        Descarga un modelo en Ollama
        
        Args:
            model_name: Nombre del modelo a descargar
            
        Yields:
            Estado del progreso de descarga
        """
        payload = {"name": model_name}
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:  # Timeout más largo para downloads
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/pull",
                    json=payload
                ) as response:
                    
                    async for chunk in response.aiter_lines():
                        if chunk:
                            try:
                                data = json.loads(chunk)
                                
                                # Formatear progreso de descarga
                                if "status" in data:
                                    progress_info = {
                                        "status": data["status"],
                                        "progress": data.get("progress", 0),
                                        "total": data.get("total", 0),
                                        "completed": data.get("completed", 0)
                                    }
                                    
                                    yield self._format_stream_response(
                                        json.dumps(progress_info),
                                        done=data.get("status") == "success"
                                    )
                                    
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            error_msg = self._handle_error(e, "pull_model")
            yield self._format_stream_response(error_msg, done=True)
    
    async def delete_model(self, model_name: str) -> bool:
        """
        Elimina un modelo de Ollama
        
        Args:
            model_name: Nombre del modelo a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            async with httpx.AsyncClient(timeout=self._config["timeout"]) as client:
                response = await client.delete(
                    f"{self.base_url}/api/delete",
                    json={"name": model_name}
                )
                
                if response.status_code == 200:
                    # Limpiar cache de modelos
                    self._models_cache = None
                    return True
                else:
                    return False
                    
        except Exception:
            return False
    
    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Obtiene información detallada de un modelo
        
        Args:
            model_name: Nombre del modelo
            
        Returns:
            Información del modelo
        """
        try:
            async with httpx.AsyncClient(timeout=self._config["timeout"]) as client:
                response = await client.post(
                    f"{self.base_url}/api/show",
                    json={"name": model_name}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {}
                    
        except Exception:
            return {}
    
    def clear_models_cache(self):
        """Limpia el cache de modelos"""
        self._models_cache = None
        self._last_cache_time = 0
    
    