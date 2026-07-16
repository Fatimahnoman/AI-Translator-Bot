"""
TranslateHub — Vercel Entry Point
NOTE: Chainlit requires WebSocket support.
Vercel serverless functions do NOT support persistent WebSocket connections.
For production, use Render or Railway instead.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main app
from trans_agent import *
