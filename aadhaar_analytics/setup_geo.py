import os
import urllib.request
import json

url = "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
target_path = r"d:\UIDAI\aadhaar_analytics\data\geo\india_states.geojson"

print(f"Ensuring directory exists: {os.path.dirname(target_path)}")
os.makedirs(os.path.dirname(target_path), exist_ok=True)

print(f"Downloading from {url}...")
try:
    with urllib.request.urlopen(url) as response:
        data = response.read()
        with open(target_path, 'wb') as f:
            f.write(data)
    print(f"Successfully downloaded GeoJSON to {target_path}")
except Exception as e:
    print(f"Error downloading GeoJSON: {e}")
