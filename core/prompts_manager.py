"""
AI Forge - Prompts Manager
Sistema universal de gestión de prompts para aplicaciones especializadas
"""

import json
import os
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime


class PromptsManager:
    """
    Gestor de prompts para aplicaciones AI Forge
    
    Permite:
    - CRUD completo de prompts
    - Categorización y etiquetado
    - Historial de uso
    - Búsqueda y filtrado
    - Importación/exportación
    """
    
    def __init__(self, prompts_file: str):
        self.prompts_file = prompts_file
        self._prompts = {}
        self._ensure_data_dir()
        self._load_prompts()
    
    def _ensure_data_dir(self):
        """Asegura que el directorio de datos existe"""
        os.makedirs(os.path.dirname(self.prompts_file), exist_ok=True)
    
    def _load_prompts(self):
        """Carga prompts desde archivo"""
        try:
            if os.path.exists(self.prompts_file):
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    self._prompts = json.load(f)
            else:
                self._prompts = {}
                self._save_prompts()
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"Warning: Could not load prompts from {self.prompts_file}, starting fresh")
            self._prompts = {}
            self._save_prompts()
    
    def _save_prompts(self):
        """Guarda prompts al archivo"""
        try:
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump(self._prompts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving prompts to {self.prompts_file}: {e}")
    
    def save(self, name: str, prompt: str, description: str = "", 
             category: str = "general", tags: List[str] = None) -> Dict[str, Any]:
        """
        Guarda un nuevo prompt
        
        Args:
            name: Nombre del prompt
            prompt: Contenido del prompt
            description: Descripción opcional
            category: Categoría del prompt
            tags: Etiquetas opcionales
            
        Returns:
            Diccionario con los datos del prompt guardado
        """
        prompt_id = str(uuid.uuid4())
        
        prompt_data = {
            "id": prompt_id,
            "name": name,
            "prompt": prompt,
            "description": description,
            "category": category,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "use_count": 0,
            "version": "1.0"
        }
        
        self._prompts[prompt_id] = prompt_data
        self._save_prompts()
        
        return prompt_data
    
    def get(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un prompt específico
        
        Args:
            prompt_id: ID del prompt
            
        Returns:
            Datos del prompt o None si no existe
        """
        return self._prompts.get(prompt_id)
    
    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene todos los prompts
        
        Returns:
            Diccionario con todos los prompts
        """
        return self._prompts.copy()
    
    def update(self, prompt_id: str, **updates) -> Dict[str, Any]:
        """
        Actualiza un prompt existente
        
        Args:
            prompt_id: ID del prompt
            **updates: Campos a actualizar
            
        Returns:
            Prompt actualizado
            
        Raises:
            KeyError: Si el prompt no existe
        """
        if prompt_id not in self._prompts:
            raise KeyError(f"Prompt {prompt_id} not found")
        
        # Filtrar campos que no se pueden actualizar
        forbidden_fields = {'id', 'created_at', 'use_count'}
        allowed_updates = {k: v for k, v in updates.items() if k not in forbidden_fields}
        
        # Actualizar timestamp de modificación
        allowed_updates['modified_at'] = datetime.now().isoformat()
        
        self._prompts[prompt_id].update(allowed_updates)
        self._save_prompts()
        
        return self._prompts[prompt_id]
    
    def delete(self, prompt_id: str) -> Dict[str, Any]:
        """
        Elimina un prompt
        
        Args:
            prompt_id: ID del prompt
            
        Returns:
            Prompt eliminado
            
        Raises:
            KeyError: Si el prompt no existe
        """
        if prompt_id not in self._prompts:
            raise KeyError(f"Prompt {prompt_id} not found")
        
        deleted_prompt = self._prompts.pop(prompt_id)
        self._save_prompts()
        
        return deleted_prompt
    
    def mark_used(self, prompt_id: str):
        """
        Marca un prompt como usado (actualiza estadísticas)
        
        Args:
            prompt_id: ID del prompt
        """
        if prompt_id in self._prompts:
            self._prompts[prompt_id]['last_used'] = datetime.now().isoformat()
            self._prompts[prompt_id]['use_count'] = self._prompts[prompt_id].get('use_count', 0) + 1
            self._save_prompts()
    
    def search(self, query: str, category: str = None, tags: List[str] = None) -> List[Dict[str, Any]]:
        """
        Busca prompts por texto, categoría o etiquetas
        
        Args:
            query: Texto a buscar en nombre, descripción o contenido
            category: Filtrar por categoría específica
            tags: Filtrar por etiquetas específicas
            
        Returns:
            Lista de prompts que coinciden con la búsqueda
        """
        results = []
        query_lower = query.lower() if query else ""
        
        for prompt_data in self._prompts.values():
            # Filtro por categoría
            if category and prompt_data.get('category') != category:
                continue
            
            # Filtro por etiquetas
            if tags:
                prompt_tags = prompt_data.get('tags', [])
                if not any(tag in prompt_tags for tag in tags):
                    continue
            
            # Búsqueda de texto
            if query:
                searchable_text = (
                    prompt_data.get('name', '') + ' ' +
                    prompt_data.get('description', '') + ' ' +
                    prompt_data.get('prompt', '')
                ).lower()
                
                if query_lower not in searchable_text:
                    continue
            
            results.append(prompt_data)
        
        # Ordenar por uso reciente y frecuencia
        results.sort(key=lambda x: (x.get('use_count', 0), x.get('last_used', '')), reverse=True)
        
        return results
    
    def get_categories(self) -> List[str]:
        """
        Obtiene todas las categorías disponibles
        
        Returns:
            Lista de categorías únicas
        """
        categories = set()
        for prompt_data in self._prompts.values():
            categories.add(prompt_data.get('category', 'general'))
        return sorted(list(categories))
    
    def get_tags(self) -> List[str]:
        """
        Obtiene todas las etiquetas disponibles
        
        Returns:
            Lista de etiquetas únicas
        """
        tags = set()
        for prompt_data in self._prompts.values():
            tags.update(prompt_data.get('tags', []))
        return sorted(list(tags))
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de uso de prompts
        
        Returns:
            Diccionario con estadísticas
        """
        if not self._prompts:
            return {
                "total_prompts": 0,
                "categories": 0,
                "tags": 0,
                "most_used": None,
                "recent_used": None
            }
        
        # Calcular estadísticas
        total_uses = sum(p.get('use_count', 0) for p in self._prompts.values())
        
        # Prompt más usado
        most_used = max(self._prompts.values(), key=lambda x: x.get('use_count', 0))
        
        # Prompt usado más recientemente
        used_prompts = [p for p in self._prompts.values() if p.get('last_used')]
        recent_used = max(used_prompts, key=lambda x: x.get('last_used', '')) if used_prompts else None
        
        return {
            "total_prompts": len(self._prompts),
            "total_uses": total_uses,
            "categories": len(self.get_categories()),
            "tags": len(self.get_tags()),
            "most_used": {
                "name": most_used.get('name'),
                "use_count": most_used.get('use_count', 0)
            } if most_used.get('use_count', 0) > 0 else None,
            "recent_used": {
                "name": recent_used.get('name'),
                "last_used": recent_used.get('last_used')
            } if recent_used else None
        }
    
    def export_prompts(self, export_path: str, category: str = None):
        """
        Exporta prompts a un archivo
        
        Args:
            export_path: Ruta donde guardar el archivo
            category: Exportar solo una categoría específica (opcional)
        """
        if category:
            prompts_to_export = {
                k: v for k, v in self._prompts.items() 
                if v.get('category') == category
            }
        else:
            prompts_to_export = self._prompts.copy()
        
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "source": "ai-forge",
            "version": "1.0",
            "category_filter": category,
            "prompts": prompts_to_export
        }
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def import_prompts(self, import_path: str, overwrite: bool = False) -> Dict[str, Any]:
        """
        Importa prompts desde un archivo
        
        Args:
            import_path: Ruta del archivo a importar
            overwrite: Si sobrescribir prompts existentes con el mismo nombre
            
        Returns:
            Estadísticas de la importación
        """
        with open(import_path, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
        
        imported_prompts = import_data.get('prompts', {})
        stats = {
            "total": len(imported_prompts),
            "imported": 0,
            "skipped": 0,
            "errors": []
        }
        
        for prompt_data in imported_prompts.values():
            try:
                # Verificar si ya existe un prompt con el mismo nombre
                existing = None
                for existing_prompt in self._prompts.values():
                    if existing_prompt['name'] == prompt_data['name']:
                        existing = existing_prompt
                        break
                
                if existing and not overwrite:
                    stats["skipped"] += 1
                    continue
                
                # Generar nuevo ID si es necesario
                if existing and overwrite:
                    # Actualizar existente
                    self.update(existing['id'], **{
                        k: v for k, v in prompt_data.items() 
                        if k not in ['id', 'created_at', 'use_count']
                    })
                else:
                    # Crear nuevo
                    self.save(
                        name=prompt_data['name'],
                        prompt=prompt_data['prompt'],
                        description=prompt_data.get('description', ''),
                        category=prompt_data.get('category', 'general'),
                        tags=prompt_data.get('tags', [])
                    )
                
                stats["imported"] += 1
                
            except Exception as e:
                stats["errors"].append(f"Error importing '{prompt_data.get('name', 'unknown')}': {e}")
        
        return stats