"""
AI Forge - Configuration Manager
Gestiona la configuración persistente de las aplicaciones
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime


class ConfigManager:
    """
    Gestor de configuración para aplicaciones AI Forge
    
    Permite:
    - Cargar/guardar configuración en JSON
    - Valores por defecto
    - Validación básica
    - Historial de cambios
    """
    
    def __init__(self, config_file: str, defaults: Dict[str, Any] = None):
        self.config_file = config_file
        self.defaults = defaults or {}
        self._config = {}
        self._ensure_data_dir()
        self._load_config()
    
    def _ensure_data_dir(self):
        """Asegura que el directorio de datos existe"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
    
    def _load_config(self):
        """Carga la configuración desde archivo o usa defaults"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                    
                # Merge con defaults para asegurar que existen todas las claves
                for key, value in self.defaults.items():
                    if key not in self._config:
                        self._config[key] = value
            else:
                self._config = self.defaults.copy()
                self._save_config()
                
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"Warning: Could not load config from {self.config_file}, using defaults")
            self._config = self.defaults.copy()
            self._save_config()
    
    def _save_config(self):
        """Guarda la configuración actual al archivo"""
        try:
            # Agregar metadata
            config_to_save = {
                **self._config,
                "_metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error saving config to {self.config_file}: {e}")
    
    def get(self, key: Optional[str] = None, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración
        
        Args:
            key: Clave específica (si None, retorna toda la config)
            default: Valor por defecto si la clave no existe
            
        Returns:
            Valor de configuración o config completa
        """
        if key is None:
            # Retorna copia sin metadata
            return {k: v for k, v in self._config.items() if not k.startswith('_')}
        
        return self._config.get(key, default)
    
    def update(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza múltiples valores de configuración
        
        Args:
            updates: Diccionario con las actualizaciones
            
        Returns:
            Configuración actualizada
        """
        # Filtrar metadata
        filtered_updates = {k: v for k, v in updates.items() if not k.startswith('_')}
        
        self._config.update(filtered_updates)
        self._save_config()
        
        return self.get()
    
    def set(self, key: str, value: Any) -> Any:
        """
        Establece un valor específico
        
        Args:
            key: Clave de configuración
            value: Valor a establecer
            
        Returns:
            Valor establecido
        """
        if not key.startswith('_'):
            self._config[key] = value
            self._save_config()
        
        return value
    
    def reset(self, keys: Optional[list] = None):
        """
        Resetea configuración a defaults
        
        Args:
            keys: Lista de claves específicas a resetear (si None, resetea todo)
        """
        if keys is None:
            self._config = self.defaults.copy()
        else:
            for key in keys:
                if key in self.defaults:
                    self._config[key] = self.defaults[key]
        
        self._save_config()
    
    def backup(self, backup_path: Optional[str] = None) -> str:
        """
        Crea un backup de la configuración actual
        
        Args:
            backup_path: Ruta del backup (si None, usa timestamp)
            
        Returns:
            Ruta del archivo de backup creado
        """
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.config_file}.backup_{timestamp}"
        
        try:
            import shutil
            shutil.copy2(self.config_file, backup_path)
            return backup_path
        except Exception as e:
            raise Exception(f"Failed to create backup: {e}")
    
    def restore(self, backup_path: str):
        """
        Restaura configuración desde un backup
        
        Args:
            backup_path: Ruta del archivo de backup
        """
        try:
            import shutil
            shutil.copy2(backup_path, self.config_file)
            self._load_config()
        except Exception as e:
            raise Exception(f"Failed to restore from backup: {e}")
    
    def get_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre la configuración
        
        Returns:
            Diccionario con metadata e información
        """
        metadata = self._config.get('_metadata', {})
        
        return {
            "config_file": self.config_file,
            "exists": os.path.exists(self.config_file),
            "size": os.path.getsize(self.config_file) if os.path.exists(self.config_file) else 0,
            "last_updated": metadata.get('last_updated'),
            "version": metadata.get('version'),
            "keys_count": len([k for k in self._config.keys() if not k.startswith('_')]),
            "has_defaults": bool(self.defaults)
        }
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Valida la configuración actual
        
        Returns:
            Diccionario con resultados de validación
        """
        issues = []
        warnings = []
        
        # Verificar claves requeridas
        required_keys = ['default_provider', 'default_model', 'system_prompt']
        for key in required_keys:
            if not self.get(key):
                issues.append(f"Missing required key: {key}")
        
        # Verificar tipos de datos
        type_checks = {
            'temperature': (int, float),
            'max_tokens': int,
            'stream': bool
        }
        
        for key, expected_type in type_checks.items():
            value = self.get(key)
            if value is not None and not isinstance(value, expected_type):
                warnings.append(f"Key '{key}' should be {expected_type.__name__}, got {type(value).__name__}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }