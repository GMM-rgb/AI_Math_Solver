import sys
import os
import json
import re
from sympy import symbols, Eq, solve, simplify, sympify, nsimplify
from fractions import Fraction

# Define MATH_SYMBOLS within the script
MATH_SYMBOLS = {
    'x': ['x', '𝑥', '𝓍', '𝔵', 'χ'],
    'y': ['y', '𝑦', '𝓎', '𝔶', 'γ'],
    'z': ['z', '𝑧', '𝓏', '𝔷', 'ζ'],
    '+': ['+', '＋', '➕', '∑'],
    '-': ['-', '−', '－', '➖'],
    '*': ['*', '×', '⋅', '∗', '⨯'],
    '/': ['/', '÷', '∕', '⁄'],
    '=': ['=', '＝', '≡', '≈', '≋'],
    '^': ['^', '⁰', '¹', '²', '³', '⁴', '⁵', '⁶', '⁷', '⁸', '⁹']
}

class SimpleMathModel:
    def __init__(self):
        self.x, self.y, self.z = symbols('x y z')
        self.symbol_map = self._create_symbol_map()

    def _create_symbol_map(self):
        """Create a mapping of all possible symbols to their standard form"""
        mapping = {}
        for standard, variations in MATH_SYMBOLS.items():
            for variant in variations:
                mapping[variant] = standard
        return mapping

    def _normalize_expression(self, expression):
        """Convert all mathematical symbols to their standard form"""
        normalized = ''
        i = 0
        while i < len(expression):
            found = False
            # Try to match multi-char symbols first
            for variant, standard in self.symbol_map.items():
                if expression[i:].startswith(variant):
                    normalized += standard
                    i += len(variant)
                    found = True
                    break
            if not found:
                normalized += expression[i]
                i += 1
        return normalized

    def _identify_problem_type(self, problem):
        """Identify the type of math problem"""
        problem = problem.lower()
        if any(phrase in problem for phrase in ['equation of a line', 'find equation', 'write equation', 'line with slope']):
            if any(keyword in problem for keyword in ['slope', 'passing through', 'point']):
                return "LinearEquation"
        if 'solve' in problem or 'x' in problem or '=' in problem:
            return "Algebraic"
        if '+' in problem or ' plus ' in problem: return "Addition"
        if '-' in problem or ' minus ' in problem: return "Subtraction"
        if '*' in problem or ' times ' in problem or ' multiplied by ' in problem: return "Multiplication"
        if '/' in problem or ' divided by ' in problem: return "Division"
        if '^' in problem or ' to the power of ' in problem: return "Exponent"
        return "Unknown"

    def _translate_words_to_symbols(self, problem):
        """Translate worded mathematical operations to symbols."""
        translations = {
            'plus': '+',
            'minus': '-',
            'times': '*',
            'multiplied by': '*',
            'divide': '/',
            'divided by': '/',
            'over': '/',
            'to the power of': '^',
        }
        for word, symbol in translations.items():
            problem = problem.replace(word, symbol)
        return problem

    def handle_arithmetic(self, problem):
        """Handle basic arithmetic calculations."""
        steps = []
        try:
            # Use sympy's sympify to evaluate the expression safely
            problem = self._translate_words_to_symbols(problem)
            result = sympify(problem)
            simplified_result = nsimplify(result)

            steps.append(f"1. Interpreted the expression: {problem}")
            steps.append(f"2. Calculated the result: {simplified_result}")

            return {
                "answer": f"{simplified_result}",
                "type": "Arithmetic",
                "confidence": 100,
                "steps": steps
            }
        except Exception as e:
            return {
                "answer": f"Could not evaluate the expression: {e}",
                "type": "Error",
                "confidence": 0,
                "steps": []
            }

    def handle_linear_equation(self, problem):
        """Handle linear equation problems like finding the equation of a line given slope and point."""
        problem = problem.lower()

        # Extract slope using regex
        slope_match = re.search(r'slope\s*(?:of)?\s*(?:=|is)?\s*([-+]?\d*\.?\d+)', problem)
        if slope_match:
            m = float(slope_match.group(1))
        else:
            return {
                "answer": "Could not find the slope in the problem.",
                "type": "Error",
                "confidence": 0,
                "steps": []
            }

        # Extract point using regex
        point_match = re.search(r'passing through\s*\(?\s*([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)\s*\)?', problem)
        if point_match:
            x0 = float(point_match.group(1))
            y0 = float(point_match.group(2))
        else:
            return {
                "answer": "Could not find the point in the problem.",
                "type": "Error",
                "confidence": 0,
                "steps": []
            }

        # Calculate b using b = y0 - m * x0
        b = y0 - m * x0
        b = round(b, 4)
        m = round(m, 4)

        # Create the equation string
        if b >= 0:
            equation = f"y = {m}x + {b}"
        else:
            equation = f"y = {m}x - {abs(b)}"

        # Prepare steps
        steps = [
            "Using the point-slope form of a line:",
            f"1. Start with y - y₀ = m(x - x₀)",
            f"2. Plug in the slope (m = {m}) and the point (x₀ = {x0}, y₀ = {y0}):",
            f"   y - ({y0}) = {m}(x - ({x0}))",
            "3. Simplify the equation:",
            f"   y - {y0} = {m}x - {m * x0}",
            f"4. Rearranged equation:",
            f"   y = {m}x - {m * x0} + {y0}",
            f"5. Simplify constants:",
            f"   y = {equation.split('=')[1]}"
        ]

        return {
            "answer": equation,
            "type": "LinearEquation",
            "confidence": 100,
            "steps": steps
        }

    def solve_algebraic_equation(self, problem):
        """Solve algebraic equations of one variable."""
        try:
            # Extract left and right sides of the equation
            if '=' in problem:
                lhs_str, rhs_str = map(str.strip, problem.split('='))
            else:
                lhs_str = problem.strip()
                rhs_str = '0'
            lhs = sympify(lhs_str)
            rhs = sympify(rhs_str)
            equation = Eq(lhs, rhs)
            solutions = solve(equation)

            steps = [
                f"1. Original equation: {lhs_str} = {rhs_str}",
                f"2. Solving for x..."
            ]

            solutions_str = ', '.join([f"x = {sol}" for sol in solutions])

            return {
                "answer": solutions_str,
                "type": "Algebraic",
                "confidence": 100,
                "steps": steps
            }
        except Exception as e:
            return {
                "answer": f"Could not solve the equation: {e}",
                "type": "Error",
                "confidence": 0,
                "steps": []
            }

    def solve(self, problem):
        """Solve the given math problem."""
        problem = self._normalize_expression(problem)
        problem = self._translate_words_to_symbols(problem)
        problem_type = self._identify_problem_type(problem)

        if problem_type == "LinearEquation":
            return self.handle_linear_equation(problem)
        elif problem_type == "Algebraic":
            return self.solve_algebraic_equation(problem)
        elif problem_type in ["Addition", "Subtraction", "Multiplication", "Division", "Exponent"]:
            return self.handle_arithmetic(problem)
        else:
            return {
                "answer": "Hmm... I'm here to help with math! Try asking me a calculation. 💫",
                "type": "Unknown",
                "confidence": 0,
                "steps": []
            }

class ChatBot:
    def __init__(self):
        self.math_model = SimpleMathModel()
        # Load training data
        data_file_path = os.path.join(os.path.dirname(__file__), 'training_data.json')
        with open(data_file_path, 'r', encoding='utf-8') as f:
            self.training_data = json.load(f)

    def _normalize_text(self, text):
        """Normalize text by making it lowercase and removing extra spaces."""
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def find_in_training_data(self, problem):
        """Find a matching problem in the training data using regex patterns."""
        problem_normalized = self._normalize_text(problem)
        for item in self.training_data['math_problems']:
            for variation in item['variations']:
                pattern = re.compile(variation)
                if pattern.fullmatch(problem_normalized):
                    # Extract numbers from the user's problem
                    numbers = list(map(float, re.findall(r'\d+', problem)))
                    # Perform the calculation
                    if '+' in problem:
                        result = numbers[0] + numbers[1]
                    elif '-' in problem:
                        result = numbers[0] - numbers[1]
                    elif '*' in problem or 'times' in problem:
                        result = numbers[0] * numbers[1]
                    elif '/' in problem or 'divided by' in problem:
                        result = numbers[0] / numbers[1]
                    else:
                        result = item['answer']  # Use the answer from training data if operator not found

                    # Prepare the answer and steps
                    answer = str(result)
                    steps = [step.replace('a', str(numbers[0])).replace('b', str(numbers[1])) for step in item['steps']]
                    item_copy = item.copy()
                    item_copy['answer'] = answer
                    item_copy['steps'] = steps
                    return item_copy
        return None

    def handle_math_problem(self, problem):
        """Handle math problem using training data or the SimpleMathModel."""
        # Try to find the problem in training data
        training_item = self.find_in_training_data(problem)
        if training_item:
            return {
                'answer': training_item['answer'],
                'type': 'FromTrainingData',
                'confidence': 100,
                'steps': training_item['steps']
            }

        # If not found, use the math model
        result = self.math_model.solve(problem)
        return result

    def generate_response(self, message):
        """Generate response based on the user's message."""
        result = self.handle_math_problem(message)
        if result['confidence'] > 0:
            response = f"Answer: {result['answer']}\nSteps:\n" + "\n".join(result['steps'])
        else:
            response = "Hmm... I'm here to help with math! Try asking me a calculation. 💫"
        return response

# Main execution
if __name__ == "__main__":
    # Get user input from command-line arguments
    if len(sys.argv) > 1:
        user_input = sys.argv[1]
    else:
        user_input = input("Enter a math problem: ")

    chatbot = ChatBot()
    response = chatbot.generate_response(user_input)
    print(response)
