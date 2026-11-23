@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo [X] 没找到 python 命令。
  echo     先装 Python 3.11 以上，安装时勾选 Add Python to PATH，
  echo     装完重开这个窗口再试。
  echo.
  pause
  exit /b 1
)
python tools\wizard.py
if errorlevel 1 pause
