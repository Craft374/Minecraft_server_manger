@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "EMSR_PYTHON=.venv\Scripts\python.exe"
) else (
    where py >nul 2>nul
)
if not defined EMSR_PYTHON if %errorlevel% equ 0 (
    set "EMSR_PYTHON=py -3"
)
if not defined EMSR_PYTHON (
    set "EMSR_PYTHON=python"
)

echo [EMSR] 필요한 패키지를 확인합니다.
%EMSR_PYTHON% -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo [EMSR] Windows 실행 파일을 빌드합니다.
%EMSR_PYTHON% -m PyInstaller --noconfirm --clean win_main.spec
if errorlevel 1 goto :error

echo.
echo [EMSR] 빌드 완료: dist\EMSR.exe
pause
exit /b 0

:error
echo.
echo [EMSR] 빌드에 실패했습니다. 위 오류 내용을 확인해 주세요.
pause
exit /b 1
