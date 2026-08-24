"""
Vercel Serverless Function Entrypoint
=====================================
This file is the ONLY entrypoint Vercel invokes.
It adds the project root to sys.path so that all
project-level modules (app, config, activity_log, etc.)
can be imported correctly from within the api/ subdirectory.

DO NOT duplicate the Flask application here.
The single source of truth is app.py in the project root.
"""
import sys
import os
from pathlib import Path

# Resolve the project root (parent of this api/ directory)
_project_root = Path(__file__).resolve().parent.parent

# Insert at position 0 so project modules take precedence
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Change working directory to project root so relative lookups
# (templates/, static/, data/, assets/) resolve correctly on Vercel
os.chdir(str(_project_root))

from app import app  # noqa: E402 — must come after sys.path fix
