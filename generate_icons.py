import os
from wand.image import Image
from wand.color import Color

def generate_icons(svg_path, output_dir='app_icons'):
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Common icon sizes for different platforms
    sizes = [
        16, 32, 48, 64, 128, 256, 512,  # Windows/Linux sizes
        180,  # iOS app icon
        192, 384,  # Android/PWA icons
        1024,  # App Store icon
    ]
    
    # Open the SVG file with high resolution
    with Image(filename=svg_path, resolution=300, background=Color('transparent')) as img:
        # Ensure transparency is preserved
        img.alpha_channel = True
        img.background_color = Color('transparent')
        img.format = 'png32'  # Use PNG32 for better alpha support
        
        for size in sizes:
            # Create a copy of the image
            with img.clone() as i:
                # Use high quality settings
                i.filter = 'lanczos'
                i.resize(size, size)
                # Ensure transparency is preserved in the resized image
                i.alpha_channel = True
                # Save with maximum quality
                output_file = os.path.join(output_dir, f'icon_{size}x{size}.png')
                i.compression_quality = 100
                i.save(filename=output_file)
                print(f"Generated {size}x{size} icon: {output_file}")

if __name__ == '__main__':
    svg_path = 'logo.svg'
    generate_icons(svg_path)
