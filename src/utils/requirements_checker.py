import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check and install required packages"""
    try:
        import pip
        required = [
            'sympy>=1.12',
            'numpy>=1.21.0',
            'tensorflow>=2.13.0'
        ]
        
        for package in required:
            try:
                __import__(package.split('>=')[0])
            except ImportError:
                print(f"Installing {package}...")
                subprocess.check_call([
                    sys.executable, 
                    "-m", 
                    "pip", 
                    "install", 
                    package
                ])
        return True
    except Exception as e:
        print(f"Warning - Requirements check failed: {str(e)}")
        return False
