@echo off
setlocal
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

echo ======================================
echo   Simple Todo — 待办事项
echo ======================================
echo.

REM 启动后端 API 服务
echo [1/2] 启动后端 API 服务...
start /B python -m uvicorn server.main:app --host 127.0.0.1 --port 8000

REM 等待后端就绪
echo 等待后端服务就绪...
timeout /t 2 /nobreak > nul

REM 启动静态文件服务
echo [2/2] 启动 Web 前端...
start /B python -m http.server 3000 -d web

echo.
echo   后端 API : http://127.0.0.1:8000
echo   Web 前端 : http://127.0.0.1:3000
echo.
echo 按任意键关闭所有服务...
pause > nul

echo 正在关闭服务...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *http.server*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul
echo 服务已关闭。
endlocal
