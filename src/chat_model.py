import os
import sys
import json
import codecs

# Set up UTF-8 encoding for output
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

try:
    from src.utils.requirements_checker import check_requirements
    # Run requirements check first
    check_requirements()

    # Then import the rest
    import re
    from difflib import SequenceMatcher
    from datetime import datetime
    import random
    from pathlib import Path
    from fractions import Fraction
    from sympy.solvers import solve
    from sympy.parsing.sympy_parser import parse_expr
    from src.utils.wiki_helper import WikiHelper
    from src.learning.self_learner import SelfLearner
except ImportError as e:
    print(json.dumps({
        "error": f"Import error: {str(e)}",
        "format": "json",
        "confidence": 0
    }))
    sys.exit(1)

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
            'error': ['😅', '🤨', '🤷‍♂️'],
            'calculate': ['🧮', '➗', '📊'],
            'time': ['🕐', '⏰', '⌚'],
            'smart': ['🎓', '🧠', '📚'],
            'magic': ['✨', '💫', '🌟']
        }
        self.math_model = SimpleMathModel()  # Replace TensorFlow model with simple math
        self.wiki_helper = WikiHelper()
        self.self_learner = SelfLearner()

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

    def get_contextual_emojis(self, message, mood='happy', context=None):
        """Get multiple emojis based on message context"""
        emoji_set = set()
        
        # Always include one mood emoji
        emoji_set.add(random.choice(self.emojis.get(mood, ['😊'])))
        
        # Add context-specific emojis
        if context:
            if isinstance(context, list):
                for ctx in context:
                    if ctx in self.emojis:
                        emoji_set.add(random.choice(self.emojis[ctx]))
            elif context in self.emojis:
                emoji_set.add(random.choice(self.emojis[context]))
        
        # Add contextual emojis based on message content
        if 'calculate' in message.lower() or any(op in message for op in ['+', '-', '*', '/']):
            emoji_set.add(random.choice(self.emojis['calculate']))
        if 'help' in message.lower() or '?' in message:
            emoji_set.add(random.choice(self.emojis['help']))
        if 'smart' in message.lower() or 'clever' in message.lower():
            emoji_set.add(random.choice(self.emojis['smart']))
        
        return list(emoji_set)

    def add_personality(self, message, mood='happy', context=None):
        """Add personality to responses with multiple emojis"""
        try:
            emojis = self.get_contextual_emojis(message, mood, context)
            emoji_prefix = ' '.join(emojis[:2])  # Use up to 2 emojis at start
            emoji_suffix = ' ' + random.choice(emojis) if len(emojis) > 2 else ''
            
            phrases = [
                f"{emoji_prefix} {message}{emoji_suffix}",
                f"{message} {' '.join(emojis)}",
                f"{emoji_prefix}... {message}{emoji_suffix}",
                f"Oh! {emoji_prefix} {message}{emoji_suffix}",
            ]
            response = random.choice(phrases)
            return response.encode('utf-8').decode('utf-8')
        except UnicodeEncodeError:
            return message

    def handle_math(self, message):
        math_problem = self.extract_math_problem(message)
        if (math_problem):
            try:
                result = self.math_model.solve(math_problem)
                if "error" not in result:
                    # Create the math solution HTML first
                    math_solution = f"""
<div style="background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin: 10px 0;">
    <div class="math-text" style="font-size: 18px; color: #333;">Problem: {math_problem}</div>
    <div class="divider" style="margin: 10px 0;"></div>
    <div class="fade-in" style="color: #2196F3; font-size: 20px;">
        Answer: {result['answer'] if 'answer' in result else result.get('decimal')}
    </div>
    {f'<div class="fade-in" style="color: #666; margin-top: 5px;">Fraction: {result["fraction"]}</div>' if 'fraction' in result else ''}
    <div class="fade-in" style="margin-top: 10px; color: #666;">
        <div>Steps:</div>
        <ul style="margin: 5px 0; padding-left: 20px;">
            {''.join(f'<li class="step-item" style="--index: {i+1}">{step}</li>' for i, step in enumerate(result["steps"]))}
        </ul>
    </div>
</div>"""

                    # Combine with animations and thinking container
                    return f"""
<style>
    @keyframes typeIn {{
        from {{ width: 0; }}
        to {{ width: 100%; }}
    }}
    @keyframes fadeIn {{
        from {{ opacity: 0; }}
        to {{ opacity: 1; }}
    }}
    @keyframes slideIn {{
        from {{ width: 0; }}
        to {{ width: 100%; }}
    }}
    @keyframes bounce {{
        0%, 100% {{ transform: translateY(0); }}
        50% {{ transform: translateY(-6px); }}
    }}
    @keyframes pulse {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.05); }}
        100% {{ transform: scale(1); }}
    }}
    .math-text {{
        overflow: hidden;
        white-space: nowrap;
        animation: typeIn 1s steps(40, end);
    }}
    .divider {{
        width: 100%;
        height: 1px;
        background: #ddd;
        animation: slideIn 0.8s ease-out;
    }}
    .fade-in {{
        opacity: 0;
        animation: fadeIn 0.5s ease-out forwards;
    }}
    .step-item {{
        animation: fadeIn 0.5s ease-out forwards;
        animation-delay: calc(var(--index) * 0.2s);
        opacity: 0;
    }}
</style>
{math_solution}"""

                return self.add_personality(
                    f"Sorry, I couldn't solve that: {result['error']}", 
                    'error',
                    ['think', 'math']
                )
            except Exception as e:
                return self.add_personality(
                    f"Sorry, I had trouble with that math problem: {str(e)}", 
                    'error',
                    ['think', 'math']
                )
        return self.add_personality(
            "I don't see any proper math problem. Try asking something like '5 + 3' or '7 times 4'",
            'help',
            ['math', 'think']
        )
    
    def handle_greeting(self, message):
        hour = datetime.now().hour
        if hour < 12:
            return self.add_personality("Good morning! Ready for some math?", 'happy', ['time', 'math'])
        elif hour < 17:
            return self.add_personality("Good afternoon! Let's solve some problems!", 'happy', ['time', 'math'])
        else:
            return self.add_personality("Good evening! Time for some math fun!", 'happy', ['time', 'math'])

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
        response = None
        
        # Check for definition requests
        if 'what is' in message.lower() or 'define' in message.lower():
            term = message.lower().replace('what is', '').replace('define', '').strip()
            definition = self.self_learner.get_definition(term)
            
            if not definition:
                # Try Wikipedia
                definition = self.wiki_helper.get_definition(term)
                if definition:
                    self.self_learner.add_definition(term, definition)
            
            if definition:
                return self.add_personality(f"Here's what I found: {definition}", 'smart', ['help'])

        # Regular pattern matching
        for pattern, handler in self.math_patterns.items():
            if re.search(pattern, message, re.IGNORECASE):
                response = handler(message)
                break
                
        if not response:
            # Check similar conversations
            similar = self.self_learner.find_similar_conversations(message)
            if similar:
                response = self.add_personality(
                    f"Based on similar conversations, I think: {similar[0]['ai_response']}", 
                    'think', 
                    ['smart']
                )
            else:
                response = "I'm not sure I understand. Could you please rephrase?"

        # Learn from this conversation
        self.self_learner.learn_from_conversation(message, response)
        return response

if __name__ == "__main__":
    try:
        # Set up UTF-8 encoding
        import locale
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            
        if len(sys.argv) < 2:
            print(json.dumps({
                "error": "No message provided",
                "format": "json",
                "confidence": 0
            }))
            sys.exit(1)
        
        chatbot = ChatBot()
        response = chatbot.get_response(sys.argv[1])
        
        # Ensure response is properly encoded
        if isinstance(response, str):
            if not response.startswith('{'):
                response = json.dumps({
                    "text": response,
                    "format": "json",
                    "confidence": 100
                }, ensure_ascii=False)
        print(response.encode('utf-8').decode('utf-8'))
        sys.exit(0)
    except Exception as e:
        print(json.dumps({
            "error": str(e),
            "format": "json",
            "confidence": 0
        }, ensure_ascii=False))
        sys.exit(1)
