"""
Fetch openly-licensed (CC0 / public domain) photographs for the demo auctions
and register them in the auction_images table.

Images come from the Openverse API and are saved into static/uploads.
Run once after seeding mock_data.sql:

    env\\Scripts\\python.exe seed_images.py
"""
import json
import os
import re
import urllib.parse
import urllib.request

import MySQLdb

UPLOAD_DIR = os.path.join('static', 'uploads')
UA = {'User-Agent': 'AuctionSystemDemo/1.0 (student project)'}

DB = dict(host='localhost', user='root', passwd='', db='auction_db', charset='utf8mb4')

# Auction title -> Openverse search terms (most specific first)
QUERIES = {
    'Vintage Rolex Submariner Watch':                 ['wristwatch dial', 'luxury watch', 'wristwatch'],
    'Antique Oak Writing Desk':                       ['antique writing desk', 'wooden desk furniture', 'writing desk'],
    'Gaming Laptop - RTX 4080, 32GB RAM':             ['gaming laptop', 'laptop computer', 'notebook computer'],
    'Rare Silver Age Comic Book Collection':          ['comic books', 'vintage comic book', 'comics'],
    'Trek X-Caliber Mountain Bike':                   ['mountain bike', 'bicycle', 'mountain bicycle'],
    'Diamond Pendant Necklace, 18k Gold':             ['diamond necklace', 'gold necklace pendant', 'jewellery necklace'],
    'Fender Stratocaster Electric Guitar':            ['electric guitar', 'stratocaster guitar', 'guitar'],
    'Original Oil Painting - Countryside Landscape':  ['landscape oil painting', 'countryside painting', 'landscape painting'],
}

IMAGES_PER_AUCTION = 3


def http_get(url, timeout=45):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def search(term, want):
    """Return candidate image URLs from Openverse, preferring public domain."""
    results = []
    # cc0/pdm first so no attribution is required, then widen if needed
    for license_filter in ('cc0,pdm', 'cc0,pdm,by', ''):
        params = {
            'q': term,
            'page_size': 20,
            'size': 'large',
            'aspect_ratio': 'wide',
            'mature': 'false',
        }
        if license_filter:
            params['license'] = license_filter

        url = 'https://api.openverse.org/v1/images/?' + urllib.parse.urlencode(params)
        try:
            data = json.loads(http_get(url))
        except Exception as e:
            print(f'      search error ({term}): {e}')
            continue

        for item in data.get('results', []):
            link = item.get('url')
            if link and link.startswith('http') and link not in results:
                results.append(link)

        if len(results) >= want * 3:
            break

    return results


def download(url, destination):
    data = http_get(url)
    # Reject anything suspiciously small (broken/placeholder responses)
    if len(data) < 12000:
        raise ValueError(f'image too small ({len(data)} bytes)')
    with open(destination, 'wb') as fh:
        fh.write(data)
    return len(data)


def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')[:40]


def main():
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    conn = MySQLdb.connect(**DB)
    cur = conn.cursor()

    cur.execute('SELECT auction_id, title FROM auctions ORDER BY auction_id')
    auctions = cur.fetchall()

    total = 0

    for auction_id, title in auctions:
        terms = QUERIES.get(title)
        if not terms:
            print(f'- skipping "{title}" (no search term configured)')
            continue

        cur.execute('SELECT COUNT(*) FROM auction_images WHERE auction_id = %s', (auction_id,))
        if cur.fetchone()[0]:
            print(f'- "{title}" already has images, skipping')
            continue

        print(f'- {title}')

        candidates = []
        for term in terms:
            candidates.extend(u for u in search(term, IMAGES_PER_AUCTION) if u not in candidates)
            if len(candidates) >= IMAGES_PER_AUCTION * 4:
                break

        saved = 0
        slug = slugify(title)

        for index, url in enumerate(candidates):
            if saved >= IMAGES_PER_AUCTION:
                break

            extension = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower()
            if extension not in ('.jpg', '.jpeg', '.png', '.webp'):
                extension = '.jpg'

            filename = f'seed_{auction_id}_{slug}_{index}{extension}'
            path = os.path.join(UPLOAD_DIR, filename)

            try:
                size = download(url, path)
            except Exception as e:
                print(f'      skip: {e}')
                continue

            cur.execute(
                'INSERT INTO auction_images (auction_id, image_url, is_primary) VALUES (%s, %s, %s)',
                (auction_id, filename, saved == 0)
            )
            saved += 1
            total += 1
            print(f'      saved {filename} ({size // 1024} KB)')

        if not saved:
            print('      WARNING: no images could be downloaded')

    conn.commit()
    cur.close()
    conn.close()

    print(f'\nDone. {total} images downloaded into {UPLOAD_DIR}.')


if __name__ == '__main__':
    main()
