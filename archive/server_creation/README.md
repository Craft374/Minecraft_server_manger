# 서버 제작 보관 코드

v1.2에서는 새 서버 제작 기능을 제공하지 않기 때문에 현재 실행 파일과 분리해 둔 참고 코드입니다.
`main_ui.py`와 빌드 파일에서는 이 폴더를 불러오지 않습니다.

## 파일

- `legacy_cli.py`: v1.1의 서버 다운로드·설치·실행 흐름
- `ui_preview.py`: 다음 버전에서 검토할 서버 제작 UI 시안
- `data/`: Paper·Fabric 버전 목록과 Forge 버전 백업
- `tools/forge_version_probe.py`: Forge 버전 백업 생성 실험 코드

## 참고

- JDK 주소와 서버 설치 방식은 오래된 값이 포함되어 있으므로 그대로 재사용하면 안 됩니다.
- `ui_preview.py`는 설치 화면 시안이며 실제 서버 제작을 완료하지 않습니다.
- 다운로드 결과는 `archive/server_creation/downloads`에 저장되며 Git에서 제외됩니다.
