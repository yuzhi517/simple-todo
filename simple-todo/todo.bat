@echo off
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8

echo 正在启动后端服务...
start /B python -m uvicorn server.main:app --host 127.0.0.1 --port 8000

echo 等待后端服务就绪...
timeout /t 3 /nobreak > nul

echo 启动菜单...
python -m client.cli menu

echo 正在关闭后端服务...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq uvicorn*" 2>nul
echo 再见！
pause
