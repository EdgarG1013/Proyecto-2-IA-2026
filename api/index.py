"""
Punto de entrada para Vercel. Vercel ejecuta este archivo como función serverless
y recibe aquí todas las rutas /api/* (ver vercel.json). Solo reexporta la app de backend/.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from main import app  # noqa: E402,F401
