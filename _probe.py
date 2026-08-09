import json, urllib.request, urllib.parse

UA = {'User-Agent': 'AuctionSystemDemo/1.0 (student project; contact: local)'}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read())

def commons(term, limit=6):
    params = {
        'action': 'query', 'format': 'json', 'generator': 'search',
        'gsrsearch': f'{term} filetype:bitmap', 'gsrnamespace': '6', 'gsrlimit': str(limit),
        'prop': 'imageinfo', 'iiprop': 'url|size|extmetadata', 'iiurlwidth': '1400',
    }
    url = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(params)
    d = get(url)
    pages = (d.get('query') or {}).get('pages', {})
    out = []
    for p in pages.values():
        ii = (p.get('imageinfo') or [{}])[0]
        thumb = ii.get('thumburl')
        w, h = ii.get('width', 0), ii.get('height', 0)
        if thumb and w >= h:  # prefer landscape
            out.append((p.get('title', '')[5:], thumb, f'{w}x{h}'))
    return out

for term in ['Rolex Submariner watch', 'Fender Stratocaster', 'mountain bicycle trek',
             'antique writing desk', 'diamond necklace jewellery']:
    print('==', term)
    try:
        for t, u, dim in commons(term)[:4]:
            print(f'   {dim:>12}  {t[:52]}')
    except Exception as e:
        print('   failed:', e)
