@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

where node >nul 2>nul
if errorlevel 1 (
  echo [错误] 未找到 Node.js，请先安装 Node.js。
  pause
  exit /b 1
)

where npm.cmd >nul 2>nul
if errorlevel 1 (
  echo [错误] 未找到 npm。
  pause
  exit /b 1
)

if not exist node_modules (
  echo [准备] 首次运行，正在安装本地前端依赖...
  call npm.cmd install
  if errorlevel 1 goto :failed
)

echo [准备] 正在导出 Stage4.5-R 展示数据...
python tools\export_viewer_scene.py
if errorlevel 1 goto :failed

echo [启动] 浏览器地址：http://127.0.0.1:4173
call npm.cmd run dev
if errorlevel 1 goto :failed
exit /b 0

:failed
echo.
echo [错误] 三维轨迹 Viewer 启动失败，请检查上方信息。
pause
exit /b 1
