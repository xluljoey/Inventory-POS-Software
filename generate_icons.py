
import os
from PIL import Image, ImageDraw, ImageFont
from core.config import ICON_DIR

def create_icon(name, text, color):
    img = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a circle
    draw.ellipse((4, 4, 60, 60), fill=color)
    
    # Draw text (first letter)
    # Default font
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 32)
    except IOError:
        font = ImageFont.load_default()

    # Center text (approximation for default font)
    # For default font, we can't easily measure, so we guess.
    draw.text((20, 16), text, fill="white", font=font)
    
    filepath = os.path.join(ICON_DIR, f"{name}.png")
    img.save(filepath)
    print(f"Created {filepath}")

if __name__ == "__main__":
    if not os.path.exists(ICON_DIR):
        os.makedirs(ICON_DIR)
        
    icons = [
        ("dashboard", "D", "#1976D2"),
        ("inventory", "I", "#388E3C"),
        ("sales", "S", "#F57C00"),
        ("customers", "C", "#7B1FA2"),
        ("reports", "R", "#D32F2F"),
        ("settings", "S", "#616161"),
        ("logout", "L", "#455A64")
    ]
    
    for name, text, color in icons:
        create_icon(name, text, color)
