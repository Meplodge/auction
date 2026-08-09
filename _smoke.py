"""Temporary smoke test: log in as each role and hit every page."""
import urllib.request, urllib.parse, urllib.error, http.cookiejar

BASE = 'http://127.0.0.1:5000'
PUBLIC = ['/', '/search', '/search?q=watch', '/search?category=Jewelry&status=all',
          '/search?status=closed', '/auction/1', '/auction/4', '/auction/7',
          '/login', '/register', '/nope']
BY_ROLE = {
    'admin@auction.com': ['/dashboard', '/admin/dashboard', '/profile', '/create_auction'],
    'john@email.com':    ['/dashboard', '/seller/dashboard', '/profile', '/create_auction'],
    'jane@email.com':    ['/dashboard', '/buyer/dashboard', '/profile', '/payments'],
}
MARKERS = ('jinja2.exceptions', 'UndefinedError', 'TemplateSyntaxError',
           'TemplateNotFound', 'Traceback (most recent call last)')
failures = []


def fetch(op, path):
    try:
        with op.open(BASE + path, timeout=25) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')


def check(label, path, status, body, expect=200):
    bad = []
    if status != expect:
        bad.append(f'status {status}')
    bad += [m for m in MARKERS if m in body]
    if bad:
        failures.append(f'{label} {path}: {", ".join(bad)}')
        print(f'  FAIL {path}: {", ".join(bad)}')
    else:
        print(f'  ok   {path} ({len(body)//1000}k)')


print('--- anonymous ---')
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
for p in PUBLIC:
    s, b = fetch(op, p)
    check('anon', p, s, b, expect=404 if p == '/nope' else 200)

for email, paths in BY_ROLE.items():
    print(f'--- {email} ---')
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    data = urllib.parse.urlencode({'email': email, 'password': 'password123'}).encode()
    try:
        with op.open(BASE + '/login', data=data, timeout=25) as r:
            st = r.status
    except urllib.error.HTTPError as e:
        st = e.code
    if st != 200:
        failures.append(f'login {email}: {st}')
        print(f'  FAIL login {st}')
        continue
    print('  ok   login')
    for p in paths:
        s, b = fetch(op, p)
        check(email, p, s, b)

print()
print('\n'.join(' - ' + f for f in failures) if failures else 'ALL PAGES OK')
