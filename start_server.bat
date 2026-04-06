@echo off
echo ========================================
echo    RAG 服务器启动 (Windows)
echo ========================================
echo.
cd /d "%~dp0"
if not exist "python\run_rag_server.py" (
    echo 错误: 找不到 python\run_rag_server.py
    pause
    exit /b 1
)
call python\start_rag_server.bat
pause
