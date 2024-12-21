from PIL import Image, ImageDraw

# Create a new image with a transparent background
img = Image.new('RGBA', (256, 256), (255, 255, 255, 0))

# Create a drawing context
draw = ImageDraw.Draw(img)

# Draw a stylized keyboard shortcut icon
# Background rectangle
draw.rectangle([50, 50, 206, 206], fill=(52, 152, 219, 230), outline=(41, 128, 185, 255), width=10)

# Key representations
draw.rectangle([70, 80, 100, 110], fill=(255, 255, 255, 200), outline=(0, 0, 0, 100))
draw.rectangle([110, 80, 140, 110], fill=(255, 255, 255, 200), outline=(0, 0, 0, 100))
draw.rectangle([150, 80, 180, 110], fill=(255, 255, 255, 200), outline=(0, 0, 0, 100))

# Text on keys
draw.text((78, 88), "Ctrl", fill=(0, 0, 0, 220), font=None)
draw.text((118, 88), "Alt", fill=(0, 0, 0, 220), font=None)
draw.text((158, 88), "Shift", fill=(0, 0, 0, 220), font=None)

# Save the icon
img.save('icon.png', 'PNG')
