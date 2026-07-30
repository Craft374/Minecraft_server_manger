import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from server_core import (
    APP_VERSION,
    ConfigStore,
    build_launch_command,
    detect_minecraft_version,
    find_launch_target,
    java_feature_for_minecraft,
)


class JavaVersionTests(unittest.TestCase):
    def test_app_version_file_matches_runtime_version(self):
        version_file = Path(__file__).parents[1] / "app_version.txt"
        self.assertEqual(
            version_file.read_text(encoding="utf-8").strip(),
            APP_VERSION,
        )

    def test_java_version_mapping(self):
        cases = {
            "1.12.2": 8,
            "1.16.5": 8,
            "1.17.1": 16,
            "1.18.2": 17,
            "1.20.4": 17,
            "1.20.5": 21,
            "1.21.1": 21,
            "": 21,
        }
        for minecraft_version, expected in cases.items():
            with self.subTest(minecraft_version=minecraft_version):
                self.assertEqual(
                    java_feature_for_minecraft(minecraft_version),
                    expected,
                )


class ServerDetectionTests(unittest.TestCase):
    def test_detects_version_json_inside_server_jar(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            server_path = Path(temp_dir)
            with zipfile.ZipFile(server_path / "server.jar", "w") as archive:
                archive.writestr("version.json", json.dumps({"id": "1.21.1"}))

            self.assertEqual(detect_minecraft_version(server_path), "1.21.1")

    def test_prefers_platform_script_and_falls_back_to_jar(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            server_path = Path(temp_dir)
            (server_path / "server.jar").write_bytes(b"not-a-real-jar")
            run_file = server_path / "run.sh"
            run_file.write_text("#!/bin/bash\n", encoding="utf-8")

            self.assertEqual(
                find_launch_target(server_path, "Darwin"),
                ("script", run_file),
            )
            command = build_launch_command(
                server_path,
                Path("/managed/jdk/bin/java"),
                "Windows",
            )
            self.assertEqual(command[0], "/managed/jdk/bin/java")
            self.assertIn("server.jar", command[-2])

    def test_replaces_hardcoded_java_in_run_script(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            server_path = Path(temp_dir)
            run_file = server_path / "run.sh"
            run_file.write_text(
                "/old/jdk/Contents/Home/bin/java -Xmx2G -jar server.jar\n",
                encoding="utf-8",
            )

            command = build_launch_command(
                server_path,
                Path("/managed/jdk/Contents/Home/bin/java"),
                "Darwin",
            )

            self.assertEqual(command[:2], ["/bin/bash", "-c"])
            self.assertIn("/managed/jdk/Contents/Home/bin/java", command[2])
            self.assertNotIn("/old/jdk", command[2])

    def test_windows_batch_uses_managed_path_and_removes_pause(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            server_path = Path(temp_dir)
            run_file = server_path / "run.bat"
            run_file.write_text(
                "@echo off\njava -Xmx2G -jar server.jar\npause\n",
                encoding="utf-8",
            )

            command = build_launch_command(
                server_path,
                Path("C:/managed/jdk/bin/java.exe"),
                "Windows",
            )

            self.assertEqual(command[:4], ["cmd.exe", "/d", "/s", "/c"])
            self.assertIn("java -Xmx2G", command[4])
            self.assertNotIn("pause", command[4].lower())


class ConfigStoreTests(unittest.TestCase):
    def test_add_server_updates_duplicate_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_file = root / "config.json"
            server_path = root / "server"
            server_path.mkdir()
            store = ConfigStore(config_file)

            store.add_server("첫 이름", server_path, "1.20.4")
            store.add_server("바뀐 이름", server_path, "1.21.1")

            self.assertEqual(len(store.data["servers"]), 1)
            self.assertEqual(store.data["servers"][0]["name"], "바뀐 이름")
            self.assertEqual(
                store.data["servers"][0]["minecraft_version"],
                "1.21.1",
            )


if __name__ == "__main__":
    unittest.main()
