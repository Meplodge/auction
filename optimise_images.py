"""
Downscale and re-encode the seeded lot photographs so pages stay light.

Images are resized to fit within 1600x1600 and saved as progressive JPEG at
quality 82. Run after seed_images.py:

    env\\Scripts\\python.exe optimise_images.py
"""
import os

from PIL import Image, ImageOps

UPLOAD_DIR = os.path.join('static', 'uploads')
MAX_EDGE = 1600
QUALITY = 82


def main():
    if not os.path.isdir(UPLOAD_DIR):
        print(f'No such directory: {UPLOAD_DIR}')
        return

    before_total = after_total = 0

    for name in sorted(os.listdir(UPLOAD_DIR)):
        if not name.lower().startswith('seed_'):
            continue

        path = os.path.join(UPLOAD_DIR, name)
        before = os.path.getsize(path)

        try:
            with Image.open(path) as im:
                im = ImageOps.exif_transpose(im)
                if im.mode not in ('RGB', 'L'):
                    im = im.convert('RGB')
                im.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)
                im.save(path, 'JPEG', quality=QUALITY, optimize=True, progressive=True)
        except Exception as e:
            print(f'  skip {name}: {e}')
            continue

        after = os.path.getsize(path)
        before_total += before
        after_total += after
        print(f'  {name}: {before // 1024} KB -> {after // 1024} KB')

    if before_total:
        saved = 100 - (after_total * 100 // before_total)
        print(f'\nTotal {before_total // 1024} KB -> {after_total // 1024} KB ({saved}% smaller)')


if __name__ == '__main__':
    main()
