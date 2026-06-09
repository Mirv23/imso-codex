"""Check HTTP response headers and potential CSP issues."""
import urllib.request, http.cookiejar, re, sys

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
r = op.open("https://imsohaiti.com/django-admin/login/")
c = re.search(r'csrfmiddlewaretoken" value="([^"]+)"', r.read().decode()).group(1)
req = urllib.request.Request("https://imsohaiti.com/django-admin/login/",
    data=f"username=mirv&password=admin123456&csrfmiddlewaretoken={c}&next=/dashboard/".encode(), method="POST")
req.add_header("Content-Type", "application/x-www-form-urlencoded")
req.add_header("Referer", "https://imsohaiti.com/django-admin/login/")
op.open(req)

r2 = op.open("https://imsohaiti.com/dashboard/")
h = r2.read().decode()

print("=== RESPONSE HEADERS ===")
for k,v in r2.headers.items():
    if k.lower() in ('content-security-policy', 'x-content-type-options', 'x-frame-options', 'x-xss-protection', 'strict-transport-security', 'content-type', 'cache-control'):
        print(f"  {k}: {v}")

# Also check if the page has a meta CSP
print("\n=== META CSP ===")
for m in re.finditer(r'<meta[^>]*http-equiv[^>]*>', h, re.IGNORECASE):
    print(f"  {m.group(0)[:200]}")

# Check for script execution issues: is 'unsafe-eval' in CSP?
csp = r2.headers.get('Content-Security-Policy', '')
print(f"\nCSP: {csp[:500] if csp else '(none)'}")
if 'unsafe-eval' not in csp and csp:
    print("WARNING: CSP may block Babel (needs 'unsafe-eval')")
elif 'unsafe-eval' in csp:
    print("OK: 'unsafe-eval' present in CSP")

# Also check for X-Content-Type-Options nosniff
cto = r2.headers.get('X-Content-Type-Options', '')
print(f"X-Content-Type-Options: {cto}")
if cto == 'nosniff':
    print("NOTE: nosniff may cause issues with script MIME types")

# Check Content-Type
ct = r2.headers.get('Content-Type', '')
print(f"Content-Type: {ct}")
