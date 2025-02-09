from setuptools import setup, find_packages

setup(
    name="ai_math_solver",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        'sympy>=1.12',
        'numpy>=1.21.0',
        'tensorflow>=2.11.0'
    ]
)
