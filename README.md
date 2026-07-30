# EMSR

기존 Minecraft 서버를 불러와 실행하고 관리하는 로컬 도구

서버를 실행할 때마다 Java 경로와 실행 파일을 직접 찾는 과정이 불편해서 제작했습니다.
현재 1.2v

## 완료

- 기존 서버 폴더 경로 불러오기
- Minecraft 버전에 맞는 Java 버전 판단
- 설정한 경로에 JDK 자동 설치
- JDK 설치 완료 후 서버 자동 실행
- 서버 로그 확인과 콘솔 명령 전송
- 플레이어·월드 빠른 명령
- Windows, macOS용 원클릭 빌드 파일

## 개발중

- 새 서버 제작 기능
- 서버 설정 파일 편집

## 실행 방법

```bash
python main_ui.py
```

필요한 패키지는 먼저 설치해야 합니다.

```bash
python -m pip install -r requirements.txt
```

## 빌드 방법

- Windows: `build_windows.bat` 더블클릭
- macOS: `build_macos.command` 더블클릭

빌드 결과는 `dist` 폴더에 생성됩니다.
Windows 실행 파일은 Windows에서, macOS 앱은 macOS에서 각각 빌드해야 합니다.

## 사용 기술

- Python
- CustomTkinter
- PyInstaller

## 참고

- 설정은 사용자 홈 폴더의 `.emsr/config.json`에 저장됩니다.
- JDK 자동 설치와 첫 서버 실행에는 인터넷 연결이 필요합니다.
- 서버 제작 버튼은 다음 업데이트 안내만 표시합니다.
