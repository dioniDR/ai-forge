#!/usr/bin/env python3
"""
AI Forge - Calculator App Runner
Ejecuta la aplicación especializada de calculadora matemática
"""

import uvicorn
from main import app

if __name__ == "__main__":
    print("🧮 Starting Calculator AI...")
    print("📐 Specialized mathematical problem solver")
    print("🔗 Open http://localhost:8001 in your browser")
    print("💡 Examples: equations, derivatives, integrals, conversions")
    print("=" * 50)
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8001, 
        reload=True,
        log_level="info"
    )