import sys
import subprocess

def check_requirements():
    """Simple check for basic requirements"""
    try:
        import sympy
        import numpy
        import json
        return True
    except ImportError as e:
        print(f"Warning: Missing basic requirement - {str(e)}")
        return False
