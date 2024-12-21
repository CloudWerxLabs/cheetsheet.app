from wand.image import Image
from wand.color import Color

def convert_svg_to_ico(svg_path, ico_path):
    # Open the SVG with high resolution
    with Image(filename=svg_path, resolution=300) as img:
        # Convert to PNG with transparency
        img.format = 'png'
        img.alpha_channel = True
        img.background_color = Color('transparent')
        
        # Create a new image with multiple sizes
        with Image() as ico:
            # Add different sizes (Windows recommends these sizes for icons)
            sizes = [16, 32, 48, 256]
            for size in sizes:
                with img.clone() as i:
                    i.resize(size, size)
                    ico.sequence.append(i)
            
            # Save as ICO
            ico.format = 'ico'
            ico.save(filename=ico_path)

if __name__ == '__main__':
    convert_svg_to_ico('logo.svg', 'app.ico')
