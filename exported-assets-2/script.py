import json
import os

# First, let's examine the input files to understand the data structure
files_to_check = [
    "heroes_cleaned.json",
    "hero_role_mapping.json", 
    "mlbb-winrate-leaderboard-complete.json",
    "patch_1_7_8.json",
    "patch_1_7_9.json"
]

# Check what files exist
for filename in files_to_check:
    if os.path.exists(filename):
        print(f"✓ Found: {filename}")
        with open(filename, 'r') as f:
            data = json.load(f)
            print(f"  Type: {type(data)}")
            if isinstance(data, list):
                print(f"  Length: {len(data)}")
                if len(data) > 0:
                    print(f"  Sample keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not dict'}")
            elif isinstance(data, dict):
                print(f"  Keys: {list(data.keys())}")
            print()
    else:
        print(f"✗ Missing: {filename}")