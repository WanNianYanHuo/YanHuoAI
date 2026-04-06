@echo off
chcp 65001 >nul
cd /d "%~dp0..\.."

echo.
echo ============================================================
echo   启动 Python RAG 后端服务（/docs 可查看接口页面）
echo ============================================================
echo.

if exist "env\Scripts\activate.bat" (
    call env\Scripts\activate.bat
)

python scripts\run\run_backend.py
pause
