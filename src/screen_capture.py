import sys
import json
import re
import pytesseract
from PIL import Image

def is_math_expression(text):
    # Pattern for basic math operators and numbers
    math_pattern = r'[\d+\-*/()=x²³¹⁴⁵⁶⁷⁸⁹⁰]+'
    return bool(re.search(math_pattern, text))

def process_image(image_path):
    try:
        # Open and process image
        image = Image.open(image_path)
        
        # Convert to grayscale for better OCR
        gray = image.convert('L')
        
        # Run OCR
        text = pytesseract.image_to_string(gray)
        
        # Clean up the text
        text = text.strip().replace('\n', ' ')
        
        return text
    except Exception as e:
        print(f"Error processing image: {str(e)}", file=sys.stderr)
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("No image path provided", file=sys.stderr)
        sys.exit(1)

    try:
        result = process_image(sys.argv[1])
        if result:
            # Output in JSON format
            response = {
                "text": result,
                "isMath": is_math_expression(result)
            }
            print(json.dumps(response))
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
