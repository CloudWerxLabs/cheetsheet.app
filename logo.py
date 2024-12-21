from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import os

def create_advanced_logo(size=1024, 
                          background_color=(52, 152, 219),  # Bright blue
                          accent_color=(41, 128, 185)):     # Slightly darker blue
    # Create a high-resolution image
    image = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)

    # Sophisticated gradient background
    for y in range(size):
        # Create a radial gradient effect
        for x in range(size):
            # Calculate distance from center
            dx = x - size/2
            dy = y - size/2
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Gradient intensity based on distance
            intensity = 1 - (distance / (size/2))
            intensity = max(0, min(1, intensity))
            
            # Blend background and accent colors
            r = int(background_color[0] * (1-intensity) + accent_color[0] * intensity)
            g = int(background_color[1] * (1-intensity) + accent_color[1] * intensity)
            b = int(background_color[2] * (1-intensity) + accent_color[2] * intensity)
            
            draw.point((x, y), fill=(r, g, b, 220))

    # Create a mask for the main shape
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)

    # Draw a stylized key icon
    key_width = size * 0.6
    key_height = size * 0.4
    x_start = (size - key_width) / 2
    y_start = (size - key_height) / 2

    # Key body
    mask_draw.rounded_rectangle(
        [x_start, y_start, x_start + key_width, y_start + key_height], 
        radius=int(size*0.1), 
        fill=255
    )

    # Key teeth
    teeth_width = key_width * 0.2
    teeth_height = key_height * 0.4
    teeth_y = y_start + (key_height - teeth_height) / 2

    mask_draw.rectangle(
        [x_start + key_width - teeth_width, teeth_y, 
         x_start + key_width, teeth_y + teeth_height], 
        fill=255
    )

    # Add some key details
    detail_color = 200
    mask_draw.ellipse(
        [x_start + key_width * 0.1, y_start + key_height * 0.3, 
         x_start + key_width * 0.2, y_start + key_height * 0.4], 
        fill=detail_color
    )

    # Apply the mask
    image.putalpha(mask)

    # Add a subtle shadow effect
    shadow = image.copy()
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=int(size*0.03)))
    shadow = shadow.point(lambda p: p * 0.5)  # Reduce opacity

    # Composite shadow first, then the main image
    final_image = Image.new('RGBA', (size, size))
    final_image.paste(shadow, (int(-size*0.02), int(size*0.02)), shadow)
    final_image.paste(image, (0, 0), image)

    # Add a subtle glow effect
    glow = final_image.copy()
    glow = glow.filter(ImageFilter.GaussianBlur(radius=int(size*0.05)))
    
    # Blend glow with original image
    final_image = Image.blend(glow, final_image, 0.3)

    # Add text
    try:
        # Try to use a nice font
        font_path = os.path.join(os.path.dirname(__file__), 'arial.ttf')
        font = ImageFont.truetype(font_path, size=int(size * 0.15))
    except IOError:
        font = ImageFont.load_default()

    # Create a new drawing context for text
    text_layer = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    text_draw = ImageDraw.Draw(text_layer)

    # Add "KeyWhiz" text
    text_draw.text(
        (size * 0.5, size * 0.85), 
        "KeyWhiz", 
        font=font, 
        fill=(255, 255, 255, 200), 
        anchor="ms"  # Middle, South alignment
    )

    # Composite text layer
    final_image = Image.alpha_composite(final_image, text_layer)

    # Save the logo
    logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
    final_image.save(logo_path)
    print(f"Advanced logo saved to {logo_path}")

    # Also save different sizes for various use cases
    sizes = [16, 32, 64, 128, 256, 512]
    for size in sizes:
        resized_logo = final_image.resize((size, size), Image.LANCZOS)
        resized_path = os.path.join(os.path.dirname(__file__), f'logo_{size}x{size}.png')
        resized_logo.save(resized_path)
        print(f"Saved {size}x{size} logo")

if __name__ == '__main__':
    create_advanced_logo()
