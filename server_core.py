import json
import os
import platform
import re
import shlex
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path



def _read_app_version():
    resource_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    try:
        return (resource_root / "app_version.txt").read_text(encoding="utf-8").strip()
    except OSError:
        return "1.2"


APP_VERSION = _read_app_version()
DEFAULT_SERVER_ROOT = Path.home() / "Documents" / "Minecraft_server"
DEFAULT_JDK_ROOT = DEFAULT_SERVER_ROOT / "jdk"
VERSION_PATTERN = re.compile(r"(?<!\d)(1\.\d+(?:\.\d+)?)(?!\d)")
JAVA_EXECUTABLE_PATTERN = re.compile(
    r"""(?P<java>
        "[^"\r\n]*[/\\]java(?:\.exe)?"
        |'[^'\r\n]*[/\\]java(?:\.exe)?'
        |[^\s"'<>|&]*[/\\]java(?:\.exe)?
    )(?=\s|$)""",
    re.IGNORECASE | re.VERBOSE,
)


def java_feature_for_minecraft(minecraft_version):
    match = VERSION_PATTERN.search(minecraft_version or "")
    if not match:
        return 21

    parts = [int(part) for part in match.group(1).split(".")]
    minor = parts[1]
    patch = parts[2] if len(parts) > 2 else 0

    if minor <= 16:
        return 8
    if minor == 17:
        return 16
    if minor == 20 and patch >= 5:
        return 21
    if minor >= 21:
        return 21
    return 17


def find_server_jar(server_path):
    server_path = Path(server_path)
    jars = [
        path
        for path in server_path.glob("*.jar")
        if "installer" not in path.name.lower() and "sources" not in path.name.lower()
    ]
    if not jars:
        return None

    priorities = ("server.jar", "fabric-server-launch.jar")
    by_name = {path.name.lower(): path for path in jars}
    for name in priorities:
        if name in by_name:
            return by_name[name]

    preferred_words = ("paper", "purpur", "spigot", "forge", "fabric")
    for word in preferred_words:
        matches = sorted(path for path in jars if word in path.name.lower())
        if matches:
            return matches[0]
    return sorted(jars)[0]


def find_launch_target(server_path, system_name=None):
    server_path = Path(server_path)
    system_name = system_name or platform.system()

    if system_name == "Windows":
        script = server_path / "run.bat"
        if script.is_file():
            return "script", script
    elif system_name == "Darwin":
        script = server_path / "run.sh"
        if script.is_file():
            return "script", script

    jar_path = find_server_jar(server_path)
    if jar_path:
        return "jar", jar_path
    return None


def detect_minecraft_version(server_path):
    server_path = Path(server_path)
    jar_path = find_server_jar(server_path)

    if jar_path:
        try:
            with zipfile.ZipFile(jar_path) as archive:
                version_files = [
                    name
                    for name in archive.namelist()
                    if name == "version.json" or name.endswith("/version.json")
                ]
                for name in version_files:
                    try:
                        data = json.loads(archive.read(name).decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        continue
                    for key in ("id", "name"):
                        match = VERSION_PATTERN.search(str(data.get(key, "")))
                        if match:
                            return match.group(1)
        except (OSError, zipfile.BadZipFile):
            pass

        match = VERSION_PATTERN.search(jar_path.name)
        if match:
            return match.group(1)

    for part in reversed(server_path.parts):
        match = VERSION_PATTERN.fullmatch(part)
        if match:
            return match.group(1)
    return ""


def build_launch_command(server_path, java_path, system_name=None):
    server_path = Path(server_path)
    system_name = system_name or platform.system()
    target = find_launch_target(server_path, system_name)
    if not target:
        raise FileNotFoundError("run.bat, run.sh 또는 실행 가능한 서버 JAR을 찾지 못했습니다.")

    target_type, target_path = target
    if target_type == "script":
        try:
            script_text = target_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            script_text = ""

        replacement = (
            f'"{java_path}"'
            if system_name == "Windows"
            else shlex.quote(str(java_path))
        )
        patched_text, replacement_count = JAVA_EXECUTABLE_PATTERN.subn(
            lambda _match: replacement,
            script_text,
        )
        if system_name == "Windows" and patched_text:
            patched_text = "\n".join(
                line
                for line in patched_text.splitlines()
                if line.strip().lower() not in ("pause", "@pause")
            )
            return ["cmd.exe", "/d", "/s", "/c", patched_text]

        if replacement_count:
            return ["/bin/bash", "-c", patched_text, "emsr"]

        if system_name == "Windows":
            return ["cmd.exe", "/d", "/s", "/c", str(target_path)]
        return ["/bin/bash", str(target_path)]

    return [
        str(java_path),
        "-Xms1G",
        "-Xmx2G",
        "-jar",
        str(target_path),
        "nogui",
    ]


class ConfigStore:
    def __init__(self, config_file=None):
        self.config_file = Path(config_file or Path.home() / ".emsr" / "config.json")
        self.data = self.load()

    @staticmethod
    def defaults():
        return {
            "jdk_path": str(DEFAULT_JDK_ROOT),
            "theme": "Dark",
            "ui_scale": "100%",
            "servers": [],
        }

    def load(self):
        defaults = self.defaults()
        if not self.config_file.is_file():
            return defaults

        try:
            saved = json.loads(self.config_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return defaults

        if not isinstance(saved, dict):
            return defaults

        data = defaults.copy()
        data.update(saved)
        if not isinstance(data.get("servers"), list):
            data["servers"] = []
        return data

    def save(self):
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self.config_file.with_suffix(".tmp")
        temp_file.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp_file.replace(self.config_file)

    def add_server(self, name, path, minecraft_version):
        normalized_path = str(Path(path).expanduser().resolve())
        entry = {
            "name": name.strip() or Path(normalized_path).name,
            "path": normalized_path,
            "minecraft_version": minecraft_version.strip(),
        }

        for index, server in enumerate(self.data["servers"]):
            if server.get("path") == normalized_path:
                self.data["servers"][index] = entry
                self.save()
                return entry

        self.data["servers"].append(entry)
        self.save()
        return entry

    def discover_legacy_servers(self):
        if self.data["servers"] or not DEFAULT_SERVER_ROOT.is_dir():
            return []

        discovered = []
        for server_type in DEFAULT_SERVER_ROOT.iterdir():
            if not server_type.is_dir() or server_type.name == "jdk":
                continue
            for version_folder in server_type.iterdir():
                if not version_folder.is_dir():
                    continue
                for server_folder in version_folder.iterdir():
                    if not server_folder.is_dir() or not find_launch_target(server_folder):
                        continue
                    discovered.append(
                        {
                            "name": server_folder.name,
                            "path": str(server_folder.resolve()),
                            "minecraft_version": (
                                version_folder.name
                                if VERSION_PATTERN.fullmatch(version_folder.name)
                                else detect_minecraft_version(server_folder)
                            ),
                        }
                    )

        if discovered:
            self.data["servers"] = discovered
            self.save()
        return discovered


class JdkManager:
    def __init__(self, install_root):
        self.install_root = Path(install_root).expanduser()

    def find_java(self, feature_version):
        executable_name = "java.exe" if platform.system() == "Windows" else "java"
        direct_candidates = [
            self.install_root / "bin" / executable_name,
            self.install_root / "Contents" / "Home" / "bin" / executable_name,
        ]
        for path in direct_candidates:
            if path.is_file():
                return path

        roots = [
            self.install_root / f"jdk-{feature_version}",
            self.install_root / f"jdk{feature_version}",
        ]
        for root in roots:
            if not root.is_dir():
                continue
            matches = sorted(root.rglob(executable_name))
            for path in matches:
                if path.parent.name == "bin":
                    return path
        return None

    @staticmethod
    def java_home(java_path):
        return Path(java_path).parent.parent

    @staticmethod
    def _download_url(feature_version):
        system_name = platform.system()
        if system_name == "Windows":
            operating_system = "windows"
        elif system_name == "Darwin":
            operating_system = "mac"
        else:
            raise RuntimeError("JDK 자동 설치는 Windows와 macOS만 지원합니다.")

        machine = platform.machine().lower()
        if machine in ("arm64", "aarch64"):
            architecture = "aarch64"
        elif machine in ("x86_64", "amd64"):
            architecture = "x64"
        else:
            raise RuntimeError(f"지원하지 않는 CPU 아키텍처입니다: {machine}")

        return (
            "https://api.adoptium.net/v3/binary/latest/"
            f"{feature_version}/ga/{operating_system}/{architecture}/jdk/"
            "hotspot/normal/eclipse?project=jdk"
        )

    @staticmethod
    def _azul_fallback_url(feature_version, requests_module):
        response = requests_module.get(
            "https://api.azul.com/metadata/v1/zulu/packages/",
            params={
                "java_version": feature_version,
                "os": "macos",
                "arch": "arm",
                "java_package_type": "jdk",
                "archive_type": "tar.gz",
                "javafx_bundled": "false",
                "release_status": "ga",
                "availability_types": "ca",
                "latest": "true",
                "page_size": 10,
            },
            timeout=(15, 60),
        )
        response.raise_for_status()
        packages = response.json()
        if not packages:
            raise RuntimeError(
                f"Apple Silicon용 Java {feature_version} JDK를 찾지 못했습니다."
            )
        return packages[0]["download_url"]

    @staticmethod
    def _validate_archive_path(target_root, member_name):
        target_root = target_root.resolve()
        destination = (target_root / member_name).resolve()
        if destination != target_root and target_root not in destination.parents:
            raise RuntimeError("JDK 압축 파일에 안전하지 않은 경로가 포함되어 있습니다.")

    def install(self, feature_version, progress_callback=None):
        import requests

        existing = self.find_java(feature_version)
        if existing:
            return existing

        self.install_root.mkdir(parents=True, exist_ok=True)
        target_folder = self.install_root / f"jdk-{feature_version}"
        target_folder.mkdir(parents=True, exist_ok=True)
        suffix = ".zip" if platform.system() == "Windows" else ".tar.gz"
        temp_handle = tempfile.NamedTemporaryFile(
            prefix=f"emsr-jdk-{feature_version}-",
            suffix=suffix,
            dir=str(self.install_root),
            delete=False,
        )
        archive_path = Path(temp_handle.name)
        temp_handle.close()

        try:
            if progress_callback:
                progress_callback(f"Java {feature_version} 다운로드 준비 중")

            download_response = requests.get(
                self._download_url(feature_version),
                stream=True,
                timeout=(15, 300),
            )
            if (
                download_response.status_code == 404
                and platform.system() == "Darwin"
                and platform.machine().lower() in ("arm64", "aarch64")
                and feature_version in (8, 16)
            ):
                download_response.close()
                fallback_url = self._azul_fallback_url(
                    feature_version,
                    requests,
                )
                download_response = requests.get(
                    fallback_url,
                    stream=True,
                    timeout=(15, 300),
                )

            with download_response as response:
                response.raise_for_status()
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0
                last_reported_percent = -5
                with archive_path.open("wb") as output:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if not chunk:
                            continue
                        output.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size:
                            percent = min(int(downloaded * 100 / total_size), 100)
                            if percent >= last_reported_percent + 5 or percent == 100:
                                progress_callback(
                                    f"Java {feature_version} 다운로드 중 · {percent}%"
                                )
                                last_reported_percent = percent

            if progress_callback:
                progress_callback(f"Java {feature_version} 설치 중")

            if suffix == ".zip":
                with zipfile.ZipFile(archive_path) as archive:
                    for member in archive.namelist():
                        self._validate_archive_path(target_folder, member)
                    archive.extractall(target_folder)
            else:
                with tarfile.open(archive_path, "r:gz") as archive:
                    for member in archive.getmembers():
                        self._validate_archive_path(target_folder, member.name)
                    archive.extractall(target_folder)

            java_path = self.find_java(feature_version)
            if not java_path:
                raise RuntimeError("JDK 설치 후 java 실행 파일을 찾지 못했습니다.")

            if platform.system() != "Windows":
                java_path.chmod(java_path.stat().st_mode | 0o111)
            return java_path
        finally:
            try:
                archive_path.unlink()
            except FileNotFoundError:
                pass
