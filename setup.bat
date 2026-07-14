@echo off
chcp 65001 >nul
echo ========================================
echo   Simple Todo 安装向导
echo ========================================
echo.

where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 未找到 Python，请先安装: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python 已就绪

echo.
echo 📦 安装依赖...
pip install -r server\requirements.txt -q
echo ✅ 依赖安装完成

echo.
echo ========================================
echo   安装完成！
echo.
echo   启动方式：
echo     python run.py
echo.
echo   或直接双击 run.py 文件
echo ========================================
pause
