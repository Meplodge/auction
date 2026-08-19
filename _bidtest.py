"""Temporary check: first bid may equal the seller's starting price."""
import urllib.request, urllib.parse, http.cookiejar, MySQLdb

BASE = 'http://127.0.0.1:5000'
db = MySQLdb.connect(host='localhost', user='root', passwd='', db='auction_db',
                     cursorclass=MySQLdb.cursors.DictCursor)
cur = db.cursor()
cur.execute("SELECT user_id FROM users WHERE email='jane@email.com'")
jane = cur.fetchone()['user_id']
cur.execute("""SELECT auction_id, starting_price, min_bid_increment FROM auctions
               WHERE status='active' AND total_bids=0 AND seller_id <> %s LIMIT 1""", (jane,))
lot = cur.fetchone()
print('lot:', lot)
if not lot:
    raise SystemExit('no zero-bid active lot to test with')

op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
op.open(BASE + '/login', data=urllib.parse.urlencode(
    {'email': 'jane@email.com', 'password': 'password123'}).encode(), timeout=25)

page = op.open(f"{BASE}/auction/{lot['auction_id']}", timeout=25).read().decode('utf-8', 'replace')
i = page.find('name="bid_amount"')
print('form input:', page[i:i + 120].split('>')[0] if i > 0 else 'NOT FOUND')

body = op.open(BASE + '/place_bid', data=urllib.parse.urlencode({
    'auction_id': lot['auction_id'],
    'bid_amount': f"{lot['starting_price']:.2f}",
}).encode(), timeout=25).read().decode('utf-8', 'replace')
print('accepted flash:', 'accepted' in body, '| minimum flash:', 'Minimum bid' in body)

cur.execute("SELECT COUNT(*) c, MAX(bid_amount) m FROM bids WHERE auction_id=%s AND status='accepted'",
            (lot['auction_id'],))
print('bids row:', cur.fetchone())

# Second bid at the same price must now be rejected (needs an increment).
op2 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
op2.open(BASE + '/login', data=urllib.parse.urlencode(
    {'email': 'admin@auction.com', 'password': 'password123'}).encode(), timeout=25)
cur.execute("SELECT email FROM users WHERE user_type='buyer' AND user_id <> %s LIMIT 1", (jane,))
other = cur.fetchone()
if other:
    op3 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    op3.open(BASE + '/login', data=urllib.parse.urlencode(
        {'email': other['email'], 'password': 'password123'}).encode(), timeout=25)
    b2 = op3.open(BASE + '/place_bid', data=urllib.parse.urlencode({
        'auction_id': lot['auction_id'],
        'bid_amount': f"{lot['starting_price']:.2f}",
    }).encode(), timeout=25).read().decode('utf-8', 'replace')
    print('second bid at same price rejected:', 'Minimum bid' in b2)
