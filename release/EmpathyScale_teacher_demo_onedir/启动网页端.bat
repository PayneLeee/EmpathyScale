@echo off
setlocal
chcp 65001 >nul

echo ============================================
echo   EmpathyScale 一键启动
echo ============================================
echo.

if exist "%~dp0EmpathyScale.exe" (
  echo [INFO] 在当前目录找到 EmpathyScale.exe，正在启动...
  start "" "%~dp0EmpathyScale.exe"
  goto :end
)

if exist "%~dp0..\dist\EmpathyScale.exe" (
  echo [INFO] 在 ..\dist\ 找到 EmpathyScale.exe，正在启动...
  start "" "%~dp0..\dist\EmpathyScale.exe"
  goto :end
)

echo [ERROR] 未找到 EmpathyScale.exe
echo.
echo 请确保以下任一位置存在可执行文件：
echo 1) release\EmpathyScale.exe
echo 2) dist\EmpathyScale.exe
echo.
echo 然后重新双击本脚本。
pause

:end
echo.
echo [INFO] 若浏览器未自动打开，请手动访问：
echo        http://127.0.0.1:7860
echo.
echo [INFO] 若网络报错，请先开启可访问 OpenAI 的网络（例如 VPN）。
endlocal
