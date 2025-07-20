"""
AI Forge - Base Application Framework
Núcleo reutilizable para crear aplicaciones especializadas de IA
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, Callable
import asyncio
import json
import os
from datetime import datetime

from .config_manager import ConfigManager
from .prompts_manager import PromptsManager
from .ai_providers.provider_factory import ProviderFactory


class SavePromptRequest(BaseModel):
    name: str
    prompt: str
    description: Optional[str] = None


class UsePromptRequest(BaseModel):
    prompt_id: str


class ChatRequest(BaseModel):
    message: str
    provider: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    stream: bool = True


class BaseAIApp:
    """
    Clase base para crear aplicaciones especializadas de IA
    
    Proporciona funcionalidades comunes como:
    - Sistema de prompts
    - Gestión de configuración 
    - Múltiples proveedores de IA
    - Endpoints base
    """
    
    def __init__(
        self, 
        app_name: str, 
        default_config: Dict[str, Any] = None,
        custom_routes: Optional[Callable] = None
    ):
        self.app_name = app_name
        self.app = FastAPI(title=f"AI Forge - {app_name}")
        
        # Inicializar gestores
        self.config = ConfigManager(f"data/{app_name}_config.json", default_config or {})
        self.prompts = PromptsManager(f"data/{app_name}_prompts.json")
        self.providers = ProviderFactory()
        
        # Configurar rutas base
        self._setup_base_routes()
        
        # Configurar archivos estáticos
        if os.path.exists("shared/static"):
            self.app.mount("/static", StaticFiles(directory="shared/static"), name="static")
        
        # Agregar rutas personalizadas si se proporcionan
        if custom_routes:
            custom_routes(self)
    
    def _setup_base_routes(self):
        """Configura las rutas base que todas las apps necesitan"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "app": self.app_name,
                "timestamp": datetime.now().isoformat()
            }
        
        # === SISTEMA DE PROMPTS ===
        @self.app.get("/prompts")
        async def get_prompts():
            """Obtener todos los prompts guardados"""
            return {"prompts": self.prompts.get_all()}
        
        @self.app.post("/prompts")
        async def save_prompt(request: SavePromptRequest):
            """Guardar un nuevo prompt"""
            try:
                result = self.prompts.save(
                    name=request.name,
                    prompt=request.prompt,
                    description=request.description
                )
                return {"message": "Prompt saved successfully", "prompt": result}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/prompts/use")
        async def use_prompt(request: UsePromptRequest):
            """Aplicar un prompt específico a la configuración"""
            try:
                prompt_data = self.prompts.get(request.prompt_id)
                if not prompt_data:
                    raise HTTPException(status_code=404, detail="Prompt not found")
                
                # Actualizar configuración con el prompt
                current_config = self.config.get()
                current_config["system_prompt"] = prompt_data["prompt"]
                self.config.update(current_config)
                
                # Marcar como usado
                self.prompts.mark_used(request.prompt_id)
                
                return {
                    "message": f"Prompt '{prompt_data['name']}' applied successfully",
                    "prompt": prompt_data
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/prompts/{prompt_id}")
        async def get_prompt(prompt_id: str):
            """Obtener un prompt específico"""
            prompt_data = self.prompts.get(prompt_id)
            if not prompt_data:
                raise HTTPException(status_code=404, detail="Prompt not found")
            return {"prompt": prompt_data}
        
        @self.app.delete("/prompts/{prompt_id}")
        async def delete_prompt(prompt_id: str):
            """Eliminar un prompt"""
            try:
                deleted = self.prompts.delete(prompt_id)
                return {"message": f"Prompt '{deleted['name']}' deleted successfully"}
            except Exception as e:
                raise HTTPException(status_code=404, detail=str(e))
        
        # === CONFIGURACIÓN ===
        @self.app.get("/config")
        async def get_config():
            """Obtener configuración actual"""
            return self.config.get()
        
        @self.app.post("/config")
        async def update_config(config_data: Dict[str, Any]):
            """Actualizar configuración"""
            try:
                updated_config = self.config.update(config_data)
                return {
                    "message": "Configuration updated successfully",
                    "config": updated_config
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # === PROVEEDORES DE IA ===
        @self.app.get("/providers")
        async def get_available_providers():
            """Listar proveedores de IA disponibles"""
            return {"providers": self.providers.get_available_providers()}
        
        @self.app.get("/providers/{provider_name}/models")
        async def get_provider_models(provider_name: str):
            """Obtener modelos disponibles para un proveedor específico"""
            try:
                provider = self.providers.get_provider(provider_name)
                models = await provider.get_available_models()
                return {"provider": provider_name, "models": models}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # === CHAT UNIVERSAL ===
        @self.app.post("/chat")
        async def universal_chat(request: ChatRequest):
            """Endpoint de chat que puede usar cualquier proveedor de IA"""
            try:
                # Obtener configuración actual
                config = self.config.get()
                
                # Determinar proveedor y modelo
                provider_name = request.provider or config.get("default_provider", "ollama")
                model_name = request.model or config.get("default_model")
                
                # Obtener proveedor
                provider = self.providers.get_provider(provider_name)
                
                # Preparar parámetros
                chat_params = {
                    "message": request.message,
                    "model": model_name,
                    "system_prompt": request.system_prompt or config.get("system_prompt"),
                    "temperature": request.temperature or config.get("temperature", 0.7),
                    "stream": request.stream
                }
                
                # Enviar request
                if request.stream:
                    return StreamingResponse(
                        provider.chat_stream(**chat_params),
                        media_type="text/plain"
                    )
                else:
                    response = await provider.chat(**chat_params)
                    return {"response": response}
                    
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    def add_route(self, path: str, method: str = "GET", **kwargs):
        """Helper para agregar rutas personalizadas"""
        return self.app.api_route(path, methods=[method], **kwargs)
    
    def add_page_route(self, path: str, template_path: str):
        """Helper para agregar páginas HTML"""
        @self.app.get(path, response_class=HTMLResponse)
        async def serve_page():
            try:
                with open(template_path, "r", encoding="utf-8") as file:
                    return HTMLResponse(content=file.read())
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail="Page not found")
    
    def get_app(self) -> FastAPI:
        """Retorna la instancia de FastAPI"""
        return self.app
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, **kwargs):
        """Ejecuta la aplicación"""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port, **kwargs)