#!/usr/bin/env python3

import requests
import json

# Test the outline parameter processing by examining how the API receives and processes the outline-width parameter

# API endpoint
url = "http://localhost:8080/add-subtitles"

# Test data with outline-width: 0
test_data = {
    "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
    "subtitle_mode": "karaoke", 
    "font-family": "Pixelify Sans",
    "font-size": 50,
    "line-color": "#FFFF00",
    "position": 40,
    "text-transform": "uppercase",
    "outline-width": 0  # This is the key parameter to test
}

print("Testing outline-width parameter:")
print(f"Sending outline-width: {test_data['outline-width']} (type: {type(test_data['outline-width'])})")

try:
    response = requests.post(url, json=test_data, timeout=10)
    if response.status_code == 200:
        result = response.json()
        print(f"Job started: {result.get('job_id')}")
        print("Monitor Docker logs for outline debug messages...")
    else:
        print(f"Request failed: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error: {e}")

# Test what happens with different outline-width values
print("\nParameter type testing:")
test_values = [0, "0", 0.0, "0.0"]
for val in test_values:
    print(f"Value: {val} (type: {type(val)}) == 0: {val == 0}")