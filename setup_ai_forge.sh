#!/bin/bash

# Crear ai-forge - Framework universal para aplicaciones especializadas de IA
echo "🔥 Creando AI Forge..."

# Crear directorio principal
mkdir -p ai-forge
cd ai-forge

# Crear estructura de directorios
echo "📁 Creando estructura de directorios..."
mkdir -p {core,apps,providers,shared,data,docs,templates}
mkdir -p core/ai_providers
mkdir -p shared/{static,templates}
mkdir -p shared/static/{css,js}
mkdir -p templates/new_app_template
mkdir -p apps/{calculator,translator,coder,writer}

# Crear archivos __init__.py para módulos Python
touch core/__init__.py
touch core/ai_providers/__init__.py

# Crear archivos de configuración base
echo "⚙️ Creando archivos de configuración..."

# requirements.txt
cat > requirements.txt << 'EOF'
# Core dependencies
fastapi
uvicorn[standard]
pydantic
pydantic-settings

# AI Providers
httpx  # Para requests a APIs
ollama  # Cliente oficial Ollama
openai  # OpenAI API
anthropic  # Claude API
google-generativeai  # Gemini API

# Storage y utilidades
aiofiles
python-multipart
jinja2
pyyaml
python-dotenv

# Opcional para desarrollo
pytest
pytest-asyncio
black
flake8
EOF

# .env.example
cat > .env.example << 'EOF'
# AI Provider API Keys (opcional - solo si usas servicios cloud)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_AI_API_KEY=your_google_ai_key_here
AZURE_OPENAI_KEY=your_azure_key_here

# Ollama Configuration (local)
OLLAMA_BASE_URL=http://localhost:11434

# App Configuration
DEFAULT_PROVIDER=ollama
ENABLE_FALLBACK=true
LOG_LEVEL=INFO
EOF

# .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environment
venv/
env/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Environment variables
.env

# Data files
data/*.json
data/*.yaml
data/*.db

# Logs
*.log
logs/

# Temporary files
tmp/
temp/
*.tmp
*.backup

# AI Forge specific
providers/local_*.yaml
EOF

echo "✅ Estructura básica de ai-forge creada!"
echo ""
echo "📂 Estructura creada:"
tree -a -I '.git' . || ls -la

echo ""
echo "🔄 Próximos pasos:"
echo "1. cd ai-forge"
echo "2. Copiar funcionalidades desde ollama-lab"
echo "3. Crear entorno virtual: python -m venv venv"
echo "4. Activar entorno: source venv/bin/activate"
echo "5. Instalar dependencias: pip install -r requirements.txt"