#!/bin/bash

# Script para migrar funcionalidades desde ollama-lab a ai-forge
echo "🔄 Migrando funcionalidades desde ollama-lab..."

# Verificar que estamos en el directorio correcto
if [ ! -d "ai-forge" ]; then
    echo "❌ Error: Ejecuta este script desde /home/dioni (donde está ai-forge)"
    exit 1
fi

if [ ! -d "ollama-lab" ]; then
    echo "❌ Error: No se encuentra el directorio ollama-lab"
    exit 1
fi

cd ai-forge

echo "📋 Copiando archivos de configuración desde ollama-lab..."

# Copiar archivos de datos si existen
if [ -f "../ollama-lab/config.json" ]; then
    cp "../ollama-lab/config.json" "data/ollama_config.json"
    echo "✅ Copiado: config.json → data/ollama_config.json"
fi

if [ -f "../ollama-lab/saved_prompts.json" ]; then
    cp "../ollama-lab/saved_prompts.json" "data/ollama_prompts.json"
    echo "✅ Copiado: saved_prompts.json → data/ollama_prompts.json"
fi

# Copiar algunos assets útiles desde static (si queremos reutilizar estilos)
if [ -d "../ollama-lab/static" ]; then
    echo "📁 Copiando recursos estáticos útiles..."
    
    # Crear directorio de assets desde ollama-lab
    mkdir -p shared/static/legacy
    
    # Copiar solo los archivos que podríamos reutilizar
    if [ -f "../ollama-lab/static/index.html" ]; then
        cp "../ollama-lab/static/index.html" "shared/static/legacy/original_chat.html"
        echo "✅ Copiado: index.html como referencia"
    fi
fi

echo ""
echo "📊 Archivos migrados:"
echo "├── data/"
[ -f "data/ollama_config.json" ] && echo "│   ├── ollama_config.json ✅"
[ -f "data/ollama_prompts.json" ] && echo "│   └── ollama_prompts.json ✅"
echo "└── shared/static/legacy/"
[ -f "shared/static/legacy/original_chat.html" ] && echo "    └── original_chat.html (referencia) ✅"

echo ""
echo "🎯 Próximo paso: Crear el código base de ai-forge"
echo "   Los datos de configuración y prompts de ollama-lab han sido preservados"