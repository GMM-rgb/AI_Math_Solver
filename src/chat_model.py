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

    # Then import the rest of the modules
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
        from sympy import symbols
        self.x, self.y, self.z = symbols('x y z')

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

    def solve_system_of_equations(self, equations):
        """Solve a system of linear equations"""
        try:
            from sympy import symbols, solve, simplify, latex
            from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
            
            x, y = symbols('x y')
            transformations = standard_transformations + (implicit_multiplication_application,)
            
            system = []
            for eq in equations:
                if '=' in eq:
                    left, right = eq.split('=')
                    expr = parse_expr(left, transformations=transformations) - parse_expr(right, transformations=transformations)
                    system.append(expr)
            
            solution = solve(system, [x, y])
            
            def clean_solution(expr):
                try:
                    # First try standard simplification
                    simp = simplify(expr)
                    # Convert to a string and clean up
                    result = str(simp)
                    # Replace mathematical notations with cleaner versions
                    result = (result.replace('sqrt', '√')
                                  .replace('**', '^')
                                  .replace('*', '×')
                                  .replace('+-', '-')
                                  .replace('-+', '-'))
                    # Remove unnecessary symbols and spaces
                    result = result.replace('×1', '').replace('1×', '')
                    # Clean up negative signs
                    result = result.replace('+ -', '- ').replace('- -', '+ ')
                    return result
                except:
                    return str(expr)

            # Format the solution based on its type
            if isinstance(solution, dict):
                return ", ".join(f"{var} = {clean_solution(val)}" for var, val in solution.items())
            elif isinstance(solution, list):
                formatted = []
                for sol in solution:
                    if isinstance(sol, tuple):
                        x_val = clean_solution(sol[0])
                        y_val = clean_solution(sol[1])
                        # Further simplify if possible
                        formatted.append(f"x = {x_val}, y = {y_val}")
                return " or ".join(formatted)
            
            return clean_solution(solution)
            
        except Exception as e:
            return f"Error solving system: {str(e)}"

    def solve(self, problem):
        # Handle system of equations first
        if '\n' in problem or ',' in problem:
            equations = [eq.strip() for eq in problem.replace(',', '\n').split('\n') if eq.strip()]
            if len(equations) > 1:
                solution = self.solve_system_of_equations(equations)
                return {
                    "answer": solution,
                    "type": "System of Equations",
                    "confidence": 100,
                    "steps": [
                        f"1. Original system:",
                        *[f"   {eq}" for eq in equations],
                        "2. Solving simultaneously...",
                        f"3. Solution: {solution}"
                    ]
                }

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
        clean_msg = message.lower()
        
        # Improved system of equations detection
        if any(word in clean_msg for word in ['system', 'equations']) or (',' in clean_msg and '=' in clean_msg):
            # Remove common words that might interfere
            clean_msg = clean_msg.replace('solve', '').replace('the', '').replace('system', '').replace('of', '').replace('equations', '')
            
            # Split by comma or newline and clean each equation
            equations = []
            for eq in re.split('[,\n]', clean_msg):
                # Enhanced equation pattern matching
                eq = eq.strip()
                if '=' in eq:
                    # Match pattern like "2x + 3y = 12" or "x - y = 4"
                    match = re.search(r'([0-9]*[xy][^=]*=[^,\n]+)', eq)
                    if match:
                        equations.append(match.group(1).strip())
            
            if len(equations) > 1:
                return '\n'.join(equations)
        
        # Continue with existing single equation/expression extraction
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
            return random.choice(phrases)
        except UnicodeEncodeError:
            return message

    def handle_math(self, message):
        math_problem = self.extract_math_problem(message)
        
        if math_problem:
            try:
                # Improved system of equations handling
                if ',' in message or '\n' in math_problem:
                    equations = [eq.strip() for eq in math_problem.split('\n') if eq.strip()]
                    if len(equations) > 1:
                        result = self.math_model.solve_system_of_equations(equations)
                        return self._format_system_solution(equations, result)
                
                # Continue with existing single equation/expression handling
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
    <div class="feedback">
        <button onclick="handleFeedback(true)" class="feedback-btn positive">
            <span class="emoji">👍</span> Helpful
        </button>
    </div>
</div>"""

                    # Update the styles section with better animations
                    return f"""
<style>
    @keyframes revealText {{
        from {{ color: rgba(51, 51, 51, 0.5); }}
        to {{ color: rgba(51, 51, 51, 1); }}
    }}
    @keyframes smoothFade {{
        from {{ opacity: 0.7; transform: translateY(-5px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .math-text {{
        color: #333;
        animation: revealText 0.5s ease-out;
        white-space: pre-wrap;
    }}
    .divider {{
        height: 1px;
        background: #ddd;
        margin: 10px 0;
    }}
    .fade-in {{
        opacity: 1;
        animation: smoothFade 0.5s ease-out;
    }}
    .step-item {{
        opacity: 1;
        animation: smoothFade 0.4s ease-out;
        animation-delay: calc(var(--index) * 0.1s);
        padding: 5px;
        border-radius: 4px;
        color: #555;
    }}
    .step-item:hover {{
        background-color: rgba(33, 150, 243, 0.05);
    }}
    .feedback {{
        margin-top: 15px;
        text-align: right;
    }}
    .feedback-btn {{
        background: #fff;
        border: 1px solid #ddd;
        border-radius: 20px;
        padding: 8px 16px;
        cursor: pointer;
        transition: all 0.2s ease;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }}
    .feedback-btn:hover {{
        background: #f0f0f0;
    }}
    .feedback-btn.positive {{
        color: #4CAF50;
    }}
    .feedback-btn .emoji {{
        font-size: 1.2em;
    }}
</style>
<script>
function handleFeedback(isPositive) {{
    if (isPositive) {{
        const btn = event.target.closest('.feedback-btn');
        btn.style.background = '#4CAF50';
        btn.style.color = '#fff';
        btn.innerHTML = '<span class="emoji">✨</span> Thanks!';
        btn.disabled = true;
        
        // Send feedback to server
        fetch('/feedback', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ 
                positive: true,
                solution: "{result['answer'] if 'answer' in result else result.get('decimal')}",
                equations: "{math_problem}"
            }})
        }});
    }}
}}
</script>
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
    
    def _format_system_solution(self, equations, result):
        """Format the system of equations solution with HTML"""
        # Get detailed steps from training data
        steps = []
        for problem in self.training_data["math_problems"]:
            if all(eq in problem["input"] for eq in equations):
                steps = problem["steps"]
                break
        
        if not steps:
            # Default steps if not found in training data
            steps = [
                "1. Original system of equations:",
                *[f"   {eq}" for eq in equations],
                "2. Solving the system...",
                f"3. Solution: {result}"
            ]

        return f"""
<div class="math-solution">
    <div class="math-problem">
        <h3>System of Equations:</h3>
        <div class="equations">
            {'<br>'.join(f'<div class="equation">{eq}</div>' for eq in equations)}
        </div>
    </div>
    <div class="solution">
        <h3>Solution Steps:</h3>
        <div class="steps">
            {''.join(f'<div class="step" style="--index: {i+1}">{step}</div>' for i, step in enumerate(steps))}
        </div>
        <div class="final-result">
            <h3>Final Answer:</h3>
            <div class="result">{result}</div>
        </div>
    </div>
    <div class="feedback">
        <button onclick="handleFeedback(true)" class="feedback-btn positive">
            <span class="emoji">👍</span> Helpful
        </button>
    </div>
</div>
<style>
    .math-solution {{
        visibility: visible !important;
        opacity: 1 !important;
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        font-family: 'Arial', sans-serif;
    }}
    .math-solution * {{
        visibility: visible !important;
        opacity: 1 !important;
    }}
    .feedback {{
        margin-top: 15px;
        text-align: right;
    }}
    .feedback-btn {{
        background: #fff;
        border: 1px solid #ddd;
        border-radius: 20px;
        padding: 8px 16px;
        cursor: pointer;
        transition: all 0.2s ease;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }}
    .feedback-btn:hover {{
        background: #f0f0f0;
    }}
    .feedback-btn.positive {{
        color: #4CAF50;
    }}
    .feedback-btn .emoji {{
        font-size: 1.2em;
    }}
    .equation, .step {{
        display: block;
        opacity: 1 !important;
        transform: none;
        animation: gentleFade 0.5s ease-out;
        animation-delay: calc(var(--index) * 0.1s);
    }}
    @keyframes gentleFade {{
        from {{ 
            opacity: 0.9 !important;
            transform: translateY(-2px);
        }}
        to {{ 
            opacity: 1 !important;
            transform: translateY(0);
        }}
    }}
    .math-solution h3 {{
        color: #2196F3;
        margin: 0 0 10px 0;
        font-size: 1.2em;
    }}
    .equations {{
        margin: 10px 0;
        padding: 10px;
        background-color: white;
        border-radius: 4px;
    }}
    .equation {{
        font-family: 'Consolas', monospace;
        font-size: 1.1em;
        margin: 5px 0;
        color: #333;
        padding: 5px;
        border-radius: 4px;
    }}
    .equation:hover {{
        background-color: rgba(33, 150, 243, 0.05);
    }}
    .solution {{
        margin-top: 15px;
        padding-top: 15px;
        border-top: 1px solid #e9ecef;
    }}
    .steps {{
        margin: 15px 0;
        padding: 10px;
        background-color: white;
        border-radius: 4px;
    }}
    .step {{
        margin: 8px 0;
        padding: 8px;
        color: #555;
        font-size: 1em;
        border-radius: 4px;
        transition: background-color 0.2s ease;
    }}
    .step:hover {{
        background-color: rgba(33, 150, 243, 0.05);
    }}
    .result {{
        font-size: 1.2em;
        color: #28a745;
        font-weight: bold;
        padding: 10px;
        background-color: white;
        border-radius: 4px;
    }}
    @keyframes highlightAnswer {{
        0% {{ background-color: rgba(40, 167, 69, 0.1); }}
        50% {{ background-color: rgba(40, 167, 69, 0.05); }}
        100% {{ background-color: white; }}
    }}
</style>
<script>
function handleFeedback(isPositive) {{
    if (isPositive) {{
        const btn = event.target.closest('.feedback-btn');
        btn.style.background = '#4CAF50';
        btn.style.color = '#fff';
        btn.innerHTML = '<span class="emoji">✨</span> Thanks!';
        btn.disabled = true;
        
        // Send feedback to server
        fetch('/feedback', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ 
                positive: true,
                solution: "{result}",
                equations: {equations}
            }})
        }});
    }}
}}
</script>"""

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
        locale.setlocale(locale.LC_ALL, '')
        
        if len(sys.argv) < 2:
            print("No message provided")
            sys.exit(1)
        
        chatbot = ChatBot()
        response = chatbot.get_response(sys.argv[1])
        
        # For math solutions that contain HTML
        if isinstance(response, str) and response.strip().startswith('<'):  # Fix: startswith instead of startsWith
            print(response)  # Print HTML as-is
        else:
            # For regular chat messages, just print the text directly
            print(response)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
