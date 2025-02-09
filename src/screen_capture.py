import sys
import pytesseract
from PIL import Image

def process_image(image_path=None):
    if image_path:
        # Process uploaded image
        image = Image.open(image_path)
    else:
        # Capture screenshot
        import pyautogui
        image = pyautogui.screenshot()

    # Run OCR
    text = pytesseract.image_to_string(image)
    # Clean up the text and look for math expressions
    text = text.strip().replace('\n', ' ')
    return text

if __name__ == "__main__":
    try:
        # If path provided, process that image, otherwise take screenshot
        image_path = sys.argv[1] if len(sys.argv) > 1 else None
        text = process_image(image_path)
        print(text)
    except Exception as e:
        print(f"Error processing image: {str(e)}", file=sys.stderr)
        sys.exit(1)
