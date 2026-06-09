"""Check dashboard JSON data validity and test all script sources."""
import urllib.request, http.cookiejar, re, json, sys

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
r = op.open("https://imsohaiti.com/django-admin/login/")
c = re.search(r'csrfmiddlewaretoken" value="([^"]+)"', r.read().decode()).group(1)
req = urllib.request.Request("https://imsohaiti.com/django-admin/login/",
    data=f"username=mirv&password=admin123456&csrfmiddlewaretoken={c}&next=/dashboard/".encode(), method="POST")
req.add_header("Content-Type", "application/x-www-form-urlencoded")
req.add_header("Referer", "https://imsohaiti.com/django-admin/login/")
op.open(req)
h = op.open("https://imsohaiti.com/dashboard/").read().decode()

# Test 1: Check dashboard-summary-data JSON validity
print("=== Test 1: Dashboard JSON data ===")
m = re.search(r'id="dashboard-summary-data"[^>]*>([^<]+)', h)
if m:
    raw = m.group(1)
    try:
        data = json.loads(raw)
        print(f"  VALID JSON: {json.dumps(data, indent=2)[:500]}")
    except json.JSONDecodeError as e:
        print(f"  INVALID JSON: {e}")
        print(f"  Raw: {raw[:200]}")
else:
    print("  NOT FOUND")

# Test 2: Check all script HTTP status codes
print("\n=== Test 2: All script HTTP status ===")
scripts = re.findall(r'src="([^"]+\.js)"', h)
all_ok = True
for s in scripts:
    url = "https://imsohaiti.com" + s if s.startswith("/") else s
    try:
        resp = urllib.request.urlopen(urllib.request.Request(url), timeout=15)
        if resp.status != 200:
            print(f"  FAIL [{resp.status}] {s[-50:]}")
            all_ok = False
    except Exception as e:
        print(f"  ERROR {s[-50:]}: {e}")
        all_ok = False
if all_ok:
    print("  ALL SCRIPTS RETURN 200")

# Test 3: Check Babel response time  
print("\n=== Test 3: Babel file check ===")
try:
    resp = urllib.request.urlopen(urllib.request.Request("https://imsohaiti.com/static/adminpanel/assets/babel.min.js"), timeout=15)
    babel_data = resp.read()
    print(f"  Babel: {resp.status}, {len(babel_data)} bytes")
    # Check first bytes to verify it's JavaScript
    if babel_data[:10] == b'/*! @babel':
        print("  Babel header: CORRECT")
    else:
        print(f"  Babel header: {babel_data[:100]}")
except Exception as e:
    print(f"  Babel error: {e}")

# Test 4: Check dashboard API endpoints return something useful  
print("\n=== Test 4: Dashboard API health ===")
try:
    r = op.open("https://imsohaiti.com/dashboard/api/summary/")
    print(f"  /dashboard/api/summary/ -> {r.status}")
except Exception as e:
    print(f"  /dashboard/api/summary/ -> ERROR: {e}")

try:
    r = op.open("https://imsohaiti.com/dashboard/api/notifications/")
    print(f"  /dashboard/api/notifications/ -> {r.status}")
except Exception as e:
    print(f"  /dashboard/api/notifications/ -> ERROR: {e}")

# Test 5: Check if ReactDOM.createRoot receives the right element
print("\n=== Test 5: #root element check ===")
root_match = re.search(r'<div[^>]*id="root"[^>]*>(.*?)</div>', h, re.DOTALL)
if root_match:
    inner = root_match.group(1).strip()
    print(f"  #root inner content: '{inner[:100]}'")
    if inner:
        print("  NOTE: #root is NOT empty! React will overwrite it.")
else:
    print("  #root element not found!")

# Test 6: Check if babel scripts actually have JSX syntax
print("\n=== Test 6: Quick JSX syntax check in babel scripts ===")
babel_script_urls = re.findall(r'<script[^>]*type="text/babel"[^>]*src="([^"]*)"', h)
for i, s in enumerate(babel_script_urls[:5]):
    url = "https://imsohaiti.com" + s if s.startswith("/") else s
    data = urllib.request.urlopen(urllib.request.Request(url), timeout=15).read().decode("utf-8", errors="replace")
    has_jsx = False
    for pattern in [r'<\w+\s', r'<\w+>', r'/>', r'</\w+>']:
        if re.search(pattern, data):
            has_jsx = True
            break
    print(f"  [{i}] {'HAS JSX' if has_jsx else 'NO JSX'} ({len(data)} bytes)")

print("\nDone.")
