"""
AI Forge - Calculator App
Aplicación especializada para cálculos matemáticos con IA
"""

import sys
import os

# Agregar el directorio raíz al path para importar core
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from core.base_app import BaseAIApp


class CalculationRequest(BaseModel):
    problem: str
    show_steps: bool = True
    precision: Optional[int] = None


# Configuración específica para calculadora
CALCULATOR_CONFIG = {
    "app_name": "Calculator AI",
    "default_provider": "ollama",
    "default_model": "llama3.2",
    "temperature": 0.1,  # Baja temperatura para mayor precisión
    "system_prompt": """Eres una calculadora AI experta en matemáticas. 

INSTRUCCIONES:
- Resuelve problemas matemáticos paso a paso
- Muestra tu trabajo de manera clara y organizada  
- Usa formato markdown para ecuaciones cuando sea útil
- Si es un cálculo simple, da la respuesta directa
- Si es complejo, explica cada paso
- Solo responde temas matemáticos, no otras preguntas
- Sé preciso y conciso

FORMATO DE RESPUESTA:
📊 **Problema:** [repite el problema]
🔢 **Respuesta:** [resultado final]
📝 **Explicación:** [pasos si es necesario]""",
    "max_tokens": 1000,
    "stream": True
}


def setup_calculator_routes(app: BaseAIApp):
    """Configura rutas específicas para la calculadora"""
    
    @app.app.get("/", response_class=HTMLResponse)
    async def calculator_home():
        """Página principal de la calculadora"""
        html_content = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧮 Calculator AI - AI Forge</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧮</text></svg>" />
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .calculator {
            padding: 40px;
        }
        
        .input-section {
            margin-bottom: 30px;
        }
        
        .input-section label {
            display: block;
            font-weight: 600;
            margin-bottom: 10px;
            color: #555;
        }
        
        .problem-input {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 1.1rem;
            transition: border-color 0.3s ease;
        }
        
        .problem-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .options {
            display: flex;
            gap: 20px;
            margin: 20px 0;
            align-items: center;
        }
        
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .calculate-btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 1.1rem;
            font-weight: 600;
            border-radius: 10px;
            cursor: pointer;
            transition: transform 0.2s ease;
            width: 100%;
        }
        
        .calculate-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        .calculate-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .result-section {
            margin-top: 30px;
            min-height: 200px;
        }
        
        .result {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #667eea;
        }
        
        .result.loading {
            text-align: center;
            color: #666;
        }
        
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .examples {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }
        
        .examples h3 {
            color: #333;
            margin-bottom: 15px;
        }
        
        .example-item {
            background: white;
            padding: 10px 15px;
            margin: 8px 0;
            border-radius: 6px;
            cursor: pointer;
            transition: background-color 0.2s ease;
            border: 1px solid #e1e5e9;
        }
        
        .example-item:hover {
            background-color: #e3f2fd;
            border-color: #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧮 Calculator AI</h1>
            <p>Resuelve problemas matemáticos con inteligencia artificial</p>
        </div>
        
        <div class="calculator">
            <div class="input-section">
                <label for="problem">Problema matemático:</label>
                <textarea 
                    id="problem" 
                    class="problem-input" 
                    rows="3" 
                    placeholder="Ejemplo: Calcula la derivada de x² + 3x - 2"
                ></textarea>
            </div>
            
            <div class="options">
                <div class="checkbox-group">
                    <input type="checkbox" id="show-steps" checked>
                    <label for="show-steps">Mostrar pasos detallados</label>
                </div>
            </div>
            
            <button class="calculate-btn" onclick="calculate()">
                🔢 Calcular
            </button>
            
            <div class="result-section">
                <div id="result"></div>
            </div>
            
            <div class="examples">
                <h3>💡 Ejemplos de problemas:</h3>
                <div class="example-item" onclick="setExample('Resuelve: 2x + 5 = 13')">
                    📐 Ecuación simple: 2x + 5 = 13
                </div>
                <div class="example-item" onclick="setExample('Calcula la integral de x² dx')">
                    ∫ Integral: ∫ x² dx
                </div>
                <div class="example-item" onclick="setExample('Si tengo $1000 al 5% anual por 3 años, ¿cuánto tendré?')">
                    💰 Interés compuesto
                </div>
                <div class="example-item" onclick="setExample('Convierte 50 millas por hora a metros por segundo')">
                    🔄 Conversión de unidades
                </div>
                <div class="example-item" onclick="setExample('Encuentra el área de un círculo con radio 7 cm')">
                    🔵 Geometría básica
                </div>
            </div>
        </div>
    </div>

    <script>
        let isCalculating = false;

        function setExample(text) {
            document.getElementById('problem').value = text;
        }

        async function calculate() {
            const problemInput = document.getElementById('problem');
            const showSteps = document.getElementById('show-steps').checked;
            const resultDiv = document.getElementById('result');
            const calculateBtn = document.querySelector('.calculate-btn');
            
            const problem = problemInput.value.trim();
            
            if (!problem) {
                alert('Por favor, ingresa un problema matemático');
                return;
            }
            
            if (isCalculating) return;
            
            isCalculating = true;
            calculateBtn.disabled = true;
            calculateBtn.textContent = '🤔 Calculando...';
            
            // Mostrar loading
            resultDiv.innerHTML = `
                <div class="result loading">
                    <div class="spinner"></div>
                    Resolviendo problema matemático...
                </div>
            `;
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message: problem,
                        stream: true
                    })
                });
                
                if (!response.ok) {
                    throw new Error('Error en la respuesta del servidor');
                }
                
                // Leer respuesta streaming
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let fullResponse = '';
                
                resultDiv.innerHTML = '<div class="result"></div>';
                const resultContent = resultDiv.querySelector('.result');
                
                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                if (data.response) {
                                    fullResponse += data.response;
                                    resultContent.innerHTML = formatMathResponse(fullResponse);
                                }
                                if (data.done) {
                                    break;
                                }
                            } catch (e) {
                                // Ignorar errores de parsing
                            }
                        }
                    }
                }
                
            } catch (error) {
                resultDiv.innerHTML = `
                    <div class="result" style="border-left-color: #ff6b6b;">
                        <strong>❌ Error:</strong> ${error.message}
                    </div>
                `;
            } finally {
                isCalculating = false;
                calculateBtn.disabled = false;
                calculateBtn.textContent = '🔢 Calcular';
            }
        }

        function formatMathResponse(text) {
            // Convertir markdown básico a HTML
            return text
                .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
                .replace(/`(.*?)`/g, '<code>$1</code>')
                .replace(/\n/g, '<br>')
                .replace(/📊/g, '<span style=\"color: #4ECDC4;\">📊</span>')
                .replace(/🔢/g, '<span style=\"color: #FF6B6B;\">🔢</span>')
                .replace(/📝/g, '<span style=\"color: #667eea;\">📝</span>');
        }

        // Permitir envío con Enter (Ctrl+Enter para nueva línea)
        document.getElementById('problem').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.ctrlKey) {
                e.preventDefault();
                calculate();
            }
        });
    </script>
</body>
</html>
        """
        return HTMLResponse(content=html_content)
    
    @app.app.post("/calculate")
    async def calculate_problem(request: CalculationRequest):
        """Endpoint específico para cálculos matemáticos"""
        try:
            # Enviar al sistema de chat con el prompt especializado
            response = await app.providers.get_provider("ollama").chat(
                message=request.problem,
                model=app.config.get("default_model"),
                system_prompt=app.config.get("system_prompt"),
                temperature=app.config.get("temperature", 0.1),
                stream=False
            )
            
            return {
                "problem": request.problem,
                "solution": response,
                "show_steps": request.show_steps
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# Crear la aplicación
def create_app():
    """Crea y configura la aplicación de calculadora"""
    app = BaseAIApp("calculator", CALCULATOR_CONFIG, setup_calculator_routes)
    return app


# Para importar desde run.py
app_instance = create_app()
app = app_instance.get_app()