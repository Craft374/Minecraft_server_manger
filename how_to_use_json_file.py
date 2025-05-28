import json

with open('forge_version.json', 'r') as f:
    data = json.load(f)

versions = data.get("1.20.1", {}).get("versions", {})

if versions:
    latest_key = sorted(versions.keys())[0]
    print(versions[latest_key])
else:
    print("versions 데이터가 없습니다.")