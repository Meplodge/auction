import app

c = app.app.test_client()
for path in ['/fixed', '/browse', '/login', '/register', '/']:
    r = c.get(path)
    print(path, r.status_code, len(r.data))

h = c.get('/fixed').get_data(as_text=True)
print('slides:', h.count('class="show-panel'))
print('intro:', 'is-intro' in h)
print('rail:', 'data-rail' in h)
print('step buttons:', h.count('data-step'))
print('countdowns:', h.count('data-countdown'))
print('thumbs:', h.count('class="show-thumb"'))
