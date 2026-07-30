from setuptools import setup

APP = ["main_ui.py"]
DATA_FILES = [("", ["app_version.txt"])]

OPTIONS = {
    "argv_emulation": False,
    "iconfile": "icon.ico",
    "packages": ["tkinter", "customtkinter", "PIL", "requests"],
    "includes": ["tkinter", "customtkinter", "PIL", "server_core"],
    "frameworks": [],
    "excludes": ["matplotlib", "scipy", "numpy", "pandas"],
    "plist": {
        "CFBundleName": "Easy Minecraft Server Runner",
        "CFBundleIdentifier": "com.Craft374.EMSR",
        "CFBundleVersion": "1.2.0",
        "CFBundleShortVersionString": "1.2.0",
        "NSHighResolutionCapable": True,
    },
}

setup(
    name="EMSR",
    version="1.2.0",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
