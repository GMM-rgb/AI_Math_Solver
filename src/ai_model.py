import sys
import numpy as np
from sklearn.neural_network import MLPRegressor
import re
from training_manager import TrainingManager  # Change to direct import
from .tf_model import MathTFModel  # Now this will work
import sympy
from sympy.solvers import solve
from sympy.parsing.sympy_parser import parse_expr

# Expanded training data
training_data = [
    {"problem": "2 + 2", "answer": 4, "steps": "Added 2 and 2"},
    {"problem": "5 - 3", "answer": 2, "steps": "Subtracted 3 from 5"},
    {"problem": "3 * 4", "answer": 12, "steps": "Multiplied 3 and 4"},
    {"problem": "8 / 2", "answer": 4, "steps": "Divided 8 by 2"},
    {"problem": "10 + 5", "answer": 15, "steps": "Added 10 and 5"},
    {"problem": "7 * 6", "answer": 42, "steps": "Multiplied 7 and 6"},
    # Add more training examples...
]

def extract_features(problem):
    # Add support for algebraic equations
    if 'x' in problem or 'y' in problem:
        return extract_algebraic_features(problem)
    return extract_arithmetic_features(problem)

def extract_arithmetic_features(problem):
    numbers = [float(num) for num in re.findall(r'\d+', problem)]
    operators = re.findall(r'[+\-*/]', problem)
    
    if len(numbers) != 2 or len(operators) != 1:
        return None
    
    features = [
        numbers[0],
        numbers[1],
        1 if '+' in operators else 0,
        1 if '-' in operators else 0,
        1 if '*' in operators else 0,
        1 if '/' in operators else 0
    ]
    return features

def extract_algebraic_features(problem):
    """Extract features for algebraic equations"""
    # Convert equation to canonical form
    problem = problem.replace('=', '')  # Remove equals sign temporarily
    try:
        expr = parse_expr(problem)
        coeffs = expr.as_coefficients_dict()
        return [
            float(coeffs.get('x', 0)),  # coefficient of x
            float(coeffs.get('y', 0)),  # coefficient of y
            float(coeffs.get(1, 0)),    # constant term
            1 if '=' in problem else 0,  # is equation
            1 if '^' in problem else 0,  # has exponents
            1 if '*' in problem else 0   # has multiplication
        ]
    except:
        return None

def evaluate_expression(problem):
    try:
        # Safe eval for basic math
        return eval(problem)
    except:
        return None

def solve_algebraic(problem):
    """Solve algebraic equations"""
    try:
        # Convert to sympy equation
        equation = parse_expr(problem.split('=')[0]) - parse_expr(problem.split('=')[1])
        solution = solve(equation)
        return {
            "type": "algebraic",
            "solution": solution,
            "steps": [
                f"1. Equation: {problem}",
                f"2. Rearranged to: {equation} = 0",
                f"3. Solved for variable: {solution}"
            ]
        }
    except Exception as e:
        return {"error": f"Could not solve equation: {str(e)}"}

class MathAI:
    def __init__(self):
        self.training_manager = TrainingManager()
        self.tf_model = MathTFModel()
        self.train_model()

    def train_model(self):
        X = []
        y = []
        
        for item in self.training_manager.data["math_problems"]:
            features = extract_features(item["input"])
            if features:
                X.append(features)
                y.append(item["answer"])
        
        if X and y:
            self.tf_model.train(np.array(X), np.array(y))

    def solve_math(self, problem):
        # Check if it's an algebraic problem
        if 'x' in problem or 'y' in problem:
            result = solve_algebraic(problem)
            if "error" not in result:
                return {
                    "format": "json",
                    "problem": {
                        "input": problem,
                        "type": "Algebraic Equation"
                    },
                    "solution": {
                        "answer": str(result["solution"]),
                        "confidence": 100,  # Algebraic solutions are exact
                        "steps": result["steps"]
                    }
                }
        
        # If not algebraic, use existing arithmetic solving
        return self._solve_arithmetic(problem)

    def _solve_arithmetic(self, problem):
        features = extract_features(problem)
        if not features:
            return {
                "error": "Invalid problem format. Please use format: number operator number",
                "format": "json"
            }
        
        actual = evaluate_expression(problem)
        predicted = self.tf_model.predict(features)
        
        steps = self._generate_detailed_steps(problem, actual)
        
        confidence_value = (1 - abs(actual - predicted)/actual) * 100
        
        return {
            "format": "json",
            "problem": {
                "input": problem,
                "type": self._identify_problem_type(problem)
            },
            "solution": {
                "answer": actual,
                "predicted": float(predicted),
                "confidence": confidence_value  # Just return the number
            },
            "steps": steps
        }

    def _identify_problem_type(self, problem):
        if '+' in problem: return "Addition"
        if '-' in problem: return "Subtraction"
        if '*' in problem: return "Multiplication"
        if '/' in problem: return "Division"
        return "Unknown"

    def _generate_detailed_steps(self, problem, result):
        numbers = [int(x) for x in re.findall(r'\d+', problem)]
        operator = re.findall(r'[+\-*/]', problem)[0]
        
        if operator == '+':
            return [
                f"1. First number: {numbers[0]}",
                f"2. Second number: {numbers[1]}",
                f"3. Operation: Addition (+)",
                f"4. Add the numbers: {numbers[0]} + {numbers[1]}",
                f"5. Result: {result}"
            ]
        elif operator == '*':
            return [
                f"1. First number: {numbers[0]}",
                f"2. Second number: {numbers[1]}",
                f"3. Operation: Multiplication (*)",
                f"4. Multiply the numbers: {numbers[0]} × {numbers[1]}",
                f"5. Result: {result}"
            ]
        # Add similar steps for other operators...

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("No math problem provided.", file=sys.stderr)
        sys.exit(1)

    problem = sys.argv[1]
    math_ai = MathAI()
    result = math_ai.solve_math(problem)
    print(f"Problem: {result['problem']['input']}")
    print(f"Answer: {result['solution']['answer']}")
    print(f"Model predicted: {result['solution']['predicted']:.2f} (Confidence: {result['solution']['confidence']})")
    print("Steps:")
    for step in result['steps']:
        print(step)
