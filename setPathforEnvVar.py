import os

python_path = r'C:\Users\maxim\AppData\Roaming\Python\Python313\Scripts'
os.environ['PATH'] += os.pathsep + python_path

print(f"Updated PATH: {os.environ['PATH']}")
