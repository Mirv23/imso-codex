import urllib.request, re

# Check React version
url = "https://imsohaiti.com/static/adminpanel/assets/f08e89d7-6e64-4694-b408-451ba17659e6.js"
resp = urllib.request.urlopen(urllib.request.Request(url), timeout=15)
data = resp.read().decode("utf-8", errors="replace")

# Find version string
match = re.search(r'version:\s*"([^"]+)"', data)
if match:
    print(f"React version: {match.group(1)}")
else:
    # Check for React 18 specific features
    if "createRoot" in data:
        print("Has createRoot -> React 18+")
    else:
        print("No createRoot -> React <18")
    # Try to find version
    for m in re.finditer(r'react[^"]*version[^"]*"([^"]+)"', data, re.I):
        print(f"Found version: {m.group(1)}")

# Check ReactDOM version
url2 = "https://imsohaiti.com/static/adminpanel/assets/9b34737a-591c-492b-8cd0-8c7a6ddc879b.js"
resp2 = urllib.request.urlopen(urllib.request.Request(url2), timeout=15)
data2 = resp2.read().decode("utf-8", errors="replace")
if "createRoot" in data2:
    print("ReactDOM has createRoot -> React 18+")
else:
    print("ReactDOM does NOT have createRoot -> React 17 or earlier")
for m in re.finditer(r'version:\s*"([^"]+)"', data2):
    print(f"ReactDOM version: {m.group(1)}")
    break
