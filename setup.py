# python setup.py py2app

from setuptools import setup

APP = ['main_ui.py']  # 메인 스크립트 파일로 main_ui.py 사용
DATA_FILES = [
    ('image', ['image/Group 12.png', 'image/plane.png'])  # 이미지 파일 포함
]

OPTIONS = {
    'argv_emulation': False,  # 문제가 될 수 있으므로 False로 변경
    'iconfile': 'icon.ico',  # 아이콘 파일 (선택 사항)
    'packages': ['tkinter', 'customtkinter', 'PIL', 'mcipc'],
    'includes': ['tkinter', 'customtkinter', 'PIL', 'sub_process', 'ctk_label_button', 'mcipc.rcon.je'],
    'frameworks': [],
    'excludes': ['matplotlib', 'scipy', 'numpy', 'pandas'],  # 불필요한 패키지 제외
    'plist': {
        'CFBundleName': 'MinecraftController',  # 애플리케이션 이름 변경
        'CFBundleIdentifier': 'com.example.minecraftcontroller',  # 식별자 변경
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,  # 고해상도 디스플레이 지원
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)