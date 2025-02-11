import os
import sys
import json
import codecs

# Debug prints to verify environment and sys.path
print(f"Python executable used: {sys.executable}")
print(f"sys.path: {sys.path}")

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
    from src.models.tf_model import MathTFModel  # Update this line
except ImportError as e:
    print(json.dumps({
        "error": f"Import error: {str(e)}",
        "format": "json",
        "confidence": 0
    }))
    sys.exit(1)

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

def clean_equation(eq):
    """Clean equation string of unwanted characters and normalize format"""
    # Replace special math characters with standard ones
    cleaned = eq.strip()
    cleaned = re.sub(r'[""''‛]', '', cleaned)  # Remove smart quotes
    cleaned = re.sub(r'[×⋅∗⨯]', '*', cleaned)  # Normalize multiplication
    cleaned = re.sub(r'[÷∕⁄]', '/', cleaned)   # Normalize division
    cleaned = re.sub(r'[−–—]', '-', cleaned)   # Normalize minus
    cleaned = re.sub(r'[=＝≡≈≋]', '=', cleaned) # Normalize equals
    cleaned = re.sub(r'\s+', ' ', cleaned)     # Normalize spaces
    return cleaned

def normalize_characters(text):
    """Normalize special mathematical characters to standard ASCII"""
    chars = {
        '−': '-',  # U+2212 minus sign
        '–': '-',  # en dash
        '—': '-',  # em dash
        '⁃': '-',  # hyphen bullet
        '‐': '-',  # hyphen
        '⁄': '/',  # fraction slash
        '∕': '/',  # division slash
        '÷': '/',  # division sign
        '×': '*',  # multiplication sign
        '⋅': '*',  # dot operator
        '∗': '*',  # asterisk operator
        '·': '*',  # middle dot
        '⨯': '*',  # vector multiplication
        '∙': '*',  # bullet operator
        '⁺': '+',  # superscript plus
        '⁻': '-',  # superscript minus
    }
    for special, standard in chars.items():
        text = text.replace(special, standard)
    return text

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
        if '+' in problem: return "Addition"
        if '-' in problem: return "Subtraction"
        if '*' in problem: return "Multiplication"
        if '/' in problem: return "Division"
        if '^' in problem: return "Exponent"
        if 'x' in problem or '=' in problem: return "Algebraic"
        return "Unknown"

    def _safe_eval(self, problem):
        """Safely evaluate math expression without using eval()"""
        # Normalize the expression first
        problem = self._normalize_expression(problem)
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
            from sympy import symbols, solve, simplify
            from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
            
            x, y = symbols('x y')
            transformations = standard_transformations + (implicit_multiplication_application,)
            
            system = []
            for eq in equations:
                eq = normalize_characters(clean_equation(eq))  # Add normalization here
                if '=' in eq:
                    left, right = eq.split('=')
                    # Convert to standard form: ax + by + c = 0
                    expr = parse_expr(left, transformations=transformations) - parse_expr(right, transformations=transformations)
                    system.append(expr)
            
            # Solve the system
            solution = solve(system, [x, y])
            
            # Clean and format solution
            if isinstance(solution, dict):
                return ", ".join(f"{var} = {simplify(val)}" for var, val in solution.items())
            elif isinstance(solution, list):
                if len(solution) == 0:
                    return "No solution"
                elif len(solution) == 1:
                    return f"x = {solution[0][0]}, y = {solution[0][1]}"
                else:
                    solutions = []
                    for sol in solution:
                        x_val = simplify(sol[0])
                        y_val = simplify(sol[1])
                        solutions.append(f"x = {x_val}, y = {y_val}")
                    return " or ".join(solutions)
            
            return str(simplify(solution))
            
        except Exception as e:
            return f"Could not solve system: {str(e)}"

    def solve(self, problem):
        # Normalize the problem first
        problem = self._normalize_expression(problem)
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
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        self.data_file = Path(self.data_dir) / 'training_data.json'
        
        # Load training data
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.training_data = json.load(f)
        except Exception as e:
            print(f"Error loading training data: {e}", file=sys.stderr)
            self.training_data = {
                "conversations": [],
                "personalities": {
                    "friendly": {
                        "prefixes": ["Hey!", "Hi!", "Hello!"],
                        "suffixes": ["😊", "✨", "💫"]
                    }
                }
            }

        # Initialize other attributes
        self.math_patterns = {
            r'calculate|solve|what is|=|\+|\-|\*|\/': self.handle_math,
            r'hi|hello|hey': self.handle_greeting,
            r'help|how|what can|what is': self.handle_help,
            r'bye|goodbye': self.handle_goodbye,
            r'search|find|look up|research|complex': self.handle_complex_query
        }
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
        self.math_model = SimpleMathModel()
        self.wiki_helper = WikiHelper()
        self.self_learner = SelfLearner()
        self.notes_cache = {}
        self.local_notes_dir = os.path.join(self.data_dir, 'math_notes')
        self.tf_model = MathTFModel()  # Add TF model

    def _get_math_notes(self, topic):  # Remove 'async'
        """Fetch relevant math notes for the topic"""
        try:
            if topic in self.notes_cache:
                return self.notes_cache[topic]

            # Check local notes
            local_notes = self._get_local_notes(topic)
            if local_notes:
                self.notes_cache[topic] = local_notes
                return local_notes

            # Try to load from file
            notes_file = os.path.join(self.local_notes_dir, f"{topic.lower()}.json")
            if os.path.exists(notes_file):
                with open(notes_file, 'r') as f:
                    notes = json.load(f)
                    self.notes_cache[topic] = notes
                    return notes

            return None
        except Exception as e:
            print(f"Error fetching math notes: {e}", file=sys.stderr)
            return None

    def _get_local_notes(self, topic):
        """Get notes from local model"""
        try:
            notes_file = os.path.join(self.local_notes_dir, f"{topic.lower()}.json")
            if os.path.exists(notes_file):
                with open(notes_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error reading local notes: {e}", file=sys.stderr)
        return None

    def solve_with_notes(self, problem, topic):  # Remove 'async'
        """Solve problem with help from notes"""
        notes = self._get_math_notes(topic)  # Remove 'await'
        if notes:
            # Add notes to solution steps
            result = self.math_model.solve(problem)
            if "steps" in result:
                result["steps"].insert(1, f"Using {topic} formula: {notes.get('formulas', {}).get(topic, '')}")
                result["steps"].insert(2, f"Related example: {notes.get('examples', {}).get(topic, '')}")
            return result
        return self.math_model.solve(problem)

    def handle_math(self, message):  # Remove 'async' here
        math_problem = self.extract_math_problem(message)
        
        if math_problem:
            try:
                # Identify topic from problem
                topic = self._identify_math_topic(math_problem)
                result = self.solve_with_notes(math_problem, topic)  # Remove 'await' here
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
        """Format the system of equations solution with cleaner HTML"""
        steps = [
            "Original system:",
            *[f"  {eq}" for eq in equations],
            "Solution:",
            f"  {result}"
        ]

        return f"""
<div class="math-solution">
    <div class="problem">System of Equations</div>
    <div class="steps">
        {''.join(f'<div class="step">{step}</div>' for step in steps)}
    </div>
    <div class="result">{result}</div>
</div>"""

    def handle_greeting(self, message):
        hour = datetime.now().hour
        if (hour < 12):
            return self.add_personality("Good morning! Ready for some math?", 'happy', ['time', 'math'])
        elif (hour < 17):
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
        try:
            # Check if it's a math problem
            math_problem = self.extract_math_problem(message)
            if math_problem:
                return self.handle_math(message)
            
            # Get conversation response from TF model
            response = self.tf_model.get_response(message)
            prefix = self.tf_model.get_personality(prefix=True)
            suffix = self.tf_model.get_personality(prefix=False)
            return f"{prefix} {response} {suffix}"
            
        except Exception as e:
            print(f"Error in get_response: {e}", file=sys.stderr)
            import traceback
            print(traceback.format_exc(), file=sys.stderr)
            return self.add_personality(
                "I had trouble with that. Could you try again?",
                'error',
                ['think']
            )

    def _identify_math_topic(self, problem):
        """Identify the mathematical topic of the problem"""
        topics = {
            'algebra': r'[a-z]|=',
            'calculus': r'derivative|integral|lim',
            'trigonometry': r'sin|cos|tan',
            'geometry': r'area|volume|perimeter',
            'statistics': r'mean|median|mode|variance'
        }

        for topic, pattern in topics.items():
            if re.search(pattern, problem, re.IGNORECASE):
                return topic
        return 'basic_math'

    def add_personality(self, message, mood='happy', context=None):
        """Add emoji and personality to responses"""
        try:
            emoji_set = set()
            # Add mood emoji
            emoji_set.add(random.choice(self.emojis.get(mood, ['😊'])))
            
            # Add context emojis
            if context:
                if isinstance(context, list):
                    for ctx in context:
                        if ctx in self.emojis:
                            emoji_set.add(random.choice(self.emojis[ctx]))
                elif context in self.emojis:
                    emoji_set.add(random.choice(self.emojis[context]))
            
            emojis = list(emoji_set)
            prefix = ' '.join(emojis[:2])
            suffix = ' ' + random.choice(emojis) if len(emojis) > 2 else ''
            
            return f"{prefix} {message}{suffix}"
        except Exception as e:
            print(f"Error adding personality: {e}", file=sys.stderr)
            return message

    def extract_math_problem(self, message):
        """Extract math problem from message"""
        try:
            # Clean and normalize message
            clean_msg = message.lower().strip()
            
            # Check for system of equations
            if ('system' in clean_msg or ',' in clean_msg) and '=' in clean_msg:
                equations = []
                for eq in re.split('[,\n]', clean_msg):
                    eq = eq.strip()
                    if '=' in eq:
                        match = re.search(r'([0-9]*[xy][^=]*=[^,\n]+)', eq)
                        if match:
                            equations.append(match.group(1).strip())
                if len(equations) > 1:
                    return '\n'.join(equations)
            
            # Remove common words
            words_to_remove = ['solve', 'calculate', 'what is', 'evaluate', 'compute']
            for word in words_to_remove:
                clean_msg = clean_msg.replace(word, '')
            
            # Clean unwanted characters
            clean_msg = re.sub(r'[^\w\s+\-*/()=.,]', '', clean_msg)
            
            # Try to match algebraic equation
            if 'x' in clean_msg or '=' in clean_msg:
                match = re.search(r'([0-9x]+\s*[+\-*/]?\s*[0-9x]*\s*=\s*[0-9x]+)', clean_msg)
                if match:
                    return match.group(1).strip()
            
            # Try to match arithmetic expression
            match = re.search(r'(\d+\s*[+\-*/]\s*\d+)', clean_msg)
            if match:
                return match.group(1).strip()
            
            return None
        except Exception as e:
            print(f"Error extracting math problem: {e}", file=sys.stderr)
            return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("No message provided", file=sys.stderr)
        sys.exit(1)

    try:
        chatbot = ChatBot()
        response = chatbot.get_response(sys.argv[1])
        print(response)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
