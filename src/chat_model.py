import re
from difflib import SequenceMatcher
from datetime import datetime
import random
import json
from pathlib import Path
from fractions import Fraction
import sympy
from sympy.solvers import solve
from sympy.parsing.sympy_parser import parse_expr

class SimpleMathModel:
    def __init__(self):
        self.initialized = True
        # Define safe math operations
        self.safe_operators = {
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y,
            '^': lambda x, y: x ** y
        }

    def _identify_problem_type(self, problem):
        """Identify the type of math problem"""
        if '+' in problem: return "Addition"
        if '-' in problem: return "Subtraction"
        if '*' in problem: return "Multiplication"
        if '/' in problem: return "Division"
        if '^' in problem: return "Exponent"
        if 'x' in problem or '=' in problem: return "Algebraic"
        return "Unknown"

    def _safe_eval(self, problem):
        """Safely evaluate math expression without using eval()"""
        # Clean and tokenize the expression
        problem = problem.replace(' ', '')
        problem = problem.replace('^', '**')
        
        # Handle basic arithmetic
        for op in ['+-', '*/', '**']:
            tokens = re.split(f'([{op}])', problem)
            if len(tokens) > 1:
                tokens = [t for t in tokens if t.strip()]
                try:
                    nums = [float(tokens[0])]
                    for i in range(1, len(tokens), 2):
                        op = tokens[i]
                        num = float(tokens[i + 1])
                        if op == '+': nums.append(num)
                        elif op == '-': nums.append(-num)
                        elif op == '*': nums[-1] *= num
                        elif op == '/': nums[-1] /= num
                        elif op == '**': nums[-1] **= num
                    return sum(nums)
                except (ValueError, IndexError):
                    raise ValueError("Invalid math expression")
        
        # If no operators found, try to parse as a single number
        try:
            return float(problem)
        except ValueError:
            raise ValueError("Invalid math expression")

    def _format_fraction(self, result):
        """Format result as a fraction if needed"""
        if isinstance(result, (int, float)):
            try:
                fraction = Fraction(str(float(result))).limit_denominator()
                if fraction.denominator != 1:
                    return {
                        "decimal": float(result),
                        "fraction": f"{fraction.numerator}/{fraction.denominator}",
                        "display": f"<sup>{fraction.numerator}</sup>⁄<sub>{fraction.denominator}</sub>"
                    }
            except (ValueError, ZeroDivisionError):
                pass
        return {"decimal": result}

    def solve(self, problem):
        try:
            # Handle algebraic equations first
            if 'x' in problem or '=' in problem:
                eq_parts = problem.split('=')
                if len(eq_parts) == 2:
                    # Import transformations for implicit multiplication
                    from sympy.parsing.sympy_parser import standard_transformations, implicit_multiplication_application
                    transformations = standard_transformations + (implicit_multiplication_application,)
                    # Use transformations to handle cases like "2x" -> "2*x"
                    lhs = parse_expr(eq_parts[0].strip(), transformations=transformations)
                    rhs = parse_expr(eq_parts[1].strip(), transformations=transformations)
                    equation = lhs - rhs
                    solution = solve(equation, 'x')
                    return {
                        "answer": f"x = {solution[0]}",
                        "type": "Algebraic",
                        "confidence": 100,
                        "steps": [
                            f"1. Original equation: {problem}",
                            f"2. Rearranged to: {equation} = 0",
                            f"3. Solved for x: x = {solution[0]}"
                        ]
                    }

            # Clean the input
            clean_problem = problem.strip()
            
            # Calculate using safe evaluation
            result = self._safe_eval(clean_problem)
            problem_type = self._identify_problem_type(clean_problem)
            
            # Format the result
            formatted = self._format_fraction(result)
            
            return {
                "answer": formatted.get("decimal"),
                "fraction": formatted.get("fraction"),
                "display": formatted.get("display"),
                "confidence": 100,
                "steps": [
                    f"1. Read {problem_type} problem: {clean_problem}",
                    f"2. Calculate result: {formatted.get('display', formatted['decimal'])}"
                ],
                "type": problem_type
            }
        except Exception as e:
            return {
                "error": str(e),
                "confidence": 0
            }

class ChatBot:
    def __init__(self):
        self.math_patterns = {
            r'calculate|solve|what is|=|\+|\-|\*|\/': self.handle_math,
            r'hi|hello|hey': self.handle_greeting,
            r'help|how|what can|what is': self.handle_help,
            r'bye|goodbye': self.handle_goodbye,
            r'search|find|look up|research|complex': self.handle_complex_query
        }
        # Load training data
        self.data_file = Path(__file__).parent.parent / 'data' / 'training_data.json'
        self.training_data = {}
        self.load_training_data()
        self.emojis = {
            'happy': ['😊', '😄', '🙂'],
            'math': ['🔢', '📐', '✏️'],
            'think': ['🤔', '💭', '🧐'],
            'success': ['✅', '🎉', '👍'],
            'help': ['💡', '🤝', '❓'],
            'error': ['😅', '🤨', '🤷‍♂️']
        }
        self.math_model = SimpleMathModel()  # Replace TensorFlow model with simple math

    def _identify_problem_type(self, problem):
        """Identify the type of math problem"""
        if '+' in problem: return "Addition"
        if '-' in problem: return "Subtraction"
        if '*' in problem: return "Multiplication"
        if '/' in problem: return "Division"
        return "Unknown"

    def load_training_data(self):
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.training_data = json.load(f)
        except Exception as e:
            print("Failed to load training data:", e)
            self.training_data = {}

    def extract_math_problem(self, message):
        """Extract math problem from natural language question"""
        # Remove common phrases and unwanted punctuation
        clean_msg = message.lower()
        
        # Remove text like "python" and other unwanted words
        words_to_remove = ['python', 'solve', 'calculate', 'what is', 'evaluate', 'compute']
        for word in words_to_remove:
            clean_msg = clean_msg.replace(word, '')
        
        # Clean unwanted characters
        clean_msg = clean_msg.translate(str.maketrans('', '', '\'"`;#'))
        clean_msg = clean_msg.replace('?', '').replace('please', '').strip()
        
        # Convert word operators to symbols
        clean_msg = (clean_msg.replace('plus', '+')
                             .replace('minus', '-')
                             .replace('times', '*')
                             .replace('multiplied by', '*')
                             .replace('divided by', '/')
                             .replace('over', '/'))
        
        # Try to match algebraic equation first (with better pattern)
        algebraic_match = re.search(r'([0-9x]+\s*[\+\-\*\/]?\s*[0-9x]*\s*=\s*[0-9x]+)', clean_msg)
        if (algebraic_match and ('x' in clean_msg or '=' in clean_msg)):
            return algebraic_match.group(1).strip()
            
        # Then try arithmetic (with better pattern)
        arithmetic_match = re.search(r'(\d+\s*[\+\-\*\/]\s*\d+)', clean_msg)
        if arithmetic_match:
            return arithmetic_match.group(1).strip()
            
        return None

    def add_personality(self, message, mood='happy'):
        """Add personality to responses with emojis and natural language"""
        emoji = random.choice(self.emojis.get(mood, ['😊']))
        phrases = [
            f"{emoji} {message}",
            f"{message} {emoji}",
            f"Hmm, let me think... {message} {emoji}",
            f"Oh! {message} {emoji}",
            f"I think {message} {emoji}"
        ]
        return random.choice(phrases)

    def handle_math(self, message):
        math_problem = self.extract_math_problem(message)
        if (math_problem):
            try:
                result = self.math_model.solve(math_problem)
                if "error" not in result:
                    return json.dumps({
                        "format": "json",
                        "problem": {
                            "input": math_problem,
                            "type": self._identify_problem_type(math_problem)  # Using self here
                        },
                        "solution": result
                    })
                return self.add_personality(
                    f"Sorry, I couldn't solve that: {result['error']}", 
                    'error'
                )
            except Exception as e:
                return self.add_personality(
                    f"Sorry, I had trouble with that math problem: {str(e)}", 
                    'error'
                )
        return self.add_personality(
            "I don't see any proper math problem. Try asking something like '5 + 3' or '7 times 4'",
            'help'
        )
    
    def handle_greeting(self, message):
        hour = datetime.now().hour
        if hour < 12:
            return self.add_personality("Good morning! Ready for some math?", 'happy')
        elif hour < 17:
            return self.add_personality("Good afternoon! Let's solve some problems!", 'happy')
        else:
            return self.add_personality("Good evening! Time for some math fun!", 'happy')

    def handle_help(self, message):
        return ("I can solve math problems and provide step-by-step solutions. " +
                "Try asking something like '2 + 2' or 'solve 2x+3=7'.")

    def handle_goodbye(self, message):
        return "Goodbye! Have a great day!"
    
    def handle_complex_query(self, message):
        return "I'm built primarily to solve math problems. Could you please rephrase or try a math problem?"

    def similarity_ratio(self, a, b):
        return SequenceMatcher(None, a, b).ratio()

    def find_best_match(self, user_input, possible_matches):
        best_match = None
        best_ratio = 0
        for match in possible_matches:
            ratio = self.similarity_ratio(user_input, match)
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = match
        return best_match

    def randomize_response(self, base_response):
        variations = self.training_data.get("conversations", [])
        # Find a conversation entry matching the base response keyword
        candidates = [entry for entry in variations if base_response.lower() in entry.get("input", "").lower()]
        if candidates:
            entry = random.choice(candidates)
            response = random.choice(entry.get("responses", [base_response]))
            return self.add_personality(response, 'happy')
        return self.add_personality(base_response, 'think')

    def get_response(self, message):
        for pattern, handler in self.math_patterns.items():
            if re.search(pattern, message, re.IGNORECASE):
                return handler(message)
        # If no math pattern matched, try to generate a smart fallback.
        fallback = self.randomize_response(message)
        if fallback:
            return fallback
        return "I'm not sure I understand. Could you please rephrase?"

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("No message provided.", file=sys.stderr)
        sys.exit(1)
    
    chatbot = ChatBot()
    response = chatbot.get_response(sys.argv[1])
    print(response)
