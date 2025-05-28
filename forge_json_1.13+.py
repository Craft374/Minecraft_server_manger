import json
import requests
import time
import threading
import os

# 버전 리스트 (내림차순)
mc_versions = [
    "1.21.5", "1.21.4", "1.21.3", "1.21.1", "1.21", "1.20.6",
    "1.20.4", "1.20.3",  # ver 중복
    "1.20.2", "1.20.1", "1.20",
    "1.19.4", "1.19.3", "1.19.2", "1.19.1", "1.19",
    "1.18.2", "1.18.1", "1.18",
    "1.17.1",
    "1.16.5", "1.16.4", "1.16.3", "1.16.2", "1.16.1",
    "1.15.2", "1.15.1", "1.15",
    "1.14.4", "1.14.3", "1.14.2",
    "1.13.2"
]

shared_ver = [("1.20.3", "1.20.4")]

# ver 계산
ver_map = {}
ver = 55
i = 0
while i < len(mc_versions):
    v = mc_versions[i]
    if any(v in pair for pair in shared_ver):
        key = next(pair for pair in shared_ver if v in pair)
        if all(k in ver_map for k in key):
            i += 1
            continue
        for k in key:
            ver_map[k] = ver
        i += len(key)
        ver -= 1
    else:
        ver_map[v] = ver
        ver -= 1
        i += 1

# 스레드 결과 저장용
lock = threading.Lock()
results = {}

def check_url(version_str):
    url = f"https://maven.minecraftforge.net/net/minecraftforge/forge/{version_str}/forge-{version_str}-installer.jar"
    try:
        res = requests.head(url, timeout=3)
        if res.status_code == 200:
            print("✅", version_str)
            return True
        elif res.status_code in [403, 405]:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                print("✅", version_str)
                return True
    except requests.RequestException:
        pass
    return False

def check_range(mc_ver):
    ver = ver_map[mc_ver]
    local_list = []

    if mc_ver == "1.20.3":
        for patch in [1, 2]:
            version_str = f"{mc_ver}-{ver}.0.{patch}"
            if check_url(version_str):
                local_list.append(version_str)
    elif mc_ver == "1.20.4":
        a = 0
        b = 3
        fail = 0
        while fail < 5:
            version_str = f"{mc_ver}-{ver}.{a}.{b}"
            if check_url(version_str):
                local_list.append(version_str)
                fail = 0
            else:
                fail += 1
            b += 1
    else:
        a = 0
        b = 0
        fail = 0
        while fail < 5:
            version_str = f"{mc_ver}-{ver}.{a}.{b}"
            if check_url(version_str):
                local_list.append(version_str)
                fail = 0
            else:
                fail += 1
            b += 1

    with lock:
        results[mc_ver] = local_list

# 스레드 실행
threads = []
start = time.time()
for mc_ver in mc_versions:
    t = threading.Thread(target=check_range, args=(mc_ver,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

elapsed = time.time() - start
print(f"\n⏱ 총 소요 시간: {elapsed:.2f}초")

# JSON 저장
base_url = "https://maven.minecraftforge.net/net/minecraftforge/forge"
file_path = "forge_version.json"

if os.path.exists(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        full_data = json.load(f)
else:
    full_data = {}

for mc_ver in mc_versions:
    ver_list = results.get(mc_ver, [])
    if not ver_list:
        continue
    latest = max(ver_list)
    recommended = ""  # 필요시 수동 지정
    full_data[mc_ver] = {
        "latest": f"{base_url}/{latest}/forge-{latest}-installer.jar",
        "recommended": f"{base_url}/{recommended}/forge-{recommended}-installer.jar" if recommended else "",
        "versions": {
            v: f"{base_url}/{v}/forge-{v}-installer.jar" for v in ver_list
        }
    }

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(full_data, f, indent=2, ensure_ascii=False)
