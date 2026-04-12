@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "PIP_MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple"

echo ==============================================
echo [步骤1/3] 安装 Windows 侧 Python 依赖（用于本机调试）
echo ==============================================
set "PY_EXE="
for /f "delims=" %%I in ('where python3.exe 2^>nul') do (
  "%%~fI" -c "import sys; exit(0 if sys.version_info[0]==3 else 1)" >nul 2>nul
  if not errorlevel 1 if not defined PY_EXE set "PY_EXE=%%~fI"
)
if not defined PY_EXE (
  for /f "delims=" %%I in ('where python.exe 2^>nul') do (
    "%%~fI" -c "import sys; exit(0 if sys.version_info[0]==3 else 1)" >nul 2>nul
    if not errorlevel 1 if not defined PY_EXE set "PY_EXE=%%~fI"
  )
)
if not defined PY_EXE (
  for /f "delims=" %%I in ('py -3 -c "import sys;print(sys.executable)" 2^>nul') do (
    "%%~fI" -c "import sys; exit(0 if sys.version_info[0]==3 else 1)" >nul 2>nul
    if not errorlevel 1 if not defined PY_EXE set "PY_EXE=%%~fI"
  )
)
if not defined PY_EXE (
  echo 未找到可用的 Python 3（python3.exe/python.exe/py -3）。
  echo 请先安装 Python 3，并勾选 Add Python to PATH 后重试。
  goto :err
)
echo 使用 Python: !PY_EXE!
"!PY_EXE!" -m pip install --upgrade pip -i %PIP_MIRROR%
if errorlevel 1 goto :err
"!PY_EXE!" -m pip install -i %PIP_MIRROR% kivy pyjnius
if errorlevel 1 goto :err

echo.
echo ==============================================
echo [步骤2/3] 检查 WSL（用于 Android APK 打包）
echo ==============================================
where wsl >nul 2>nul
if errorlevel 1 (
  echo 未检测到 WSL，已完成 Windows 侧依赖安装。
  echo 如需打包 APK，请先安装 WSL Ubuntu 后再次运行本脚本。
  goto :ok
)

set "WSL_DISTRO="
for /f "delims=" %%D in ('wsl -l -q 2^>nul') do (
  if not "%%~D"=="" if not defined WSL_DISTRO set "WSL_DISTRO=%%~D"
)
if not defined WSL_DISTRO (
  echo(已检测到 WSL，但尚未安装 Linux 发行版。
  echo Please run: wsl --install -d Ubuntu
  echo(或先手动安装任意发行版后重试。
  goto :ok
)

echo 使用 WSL 发行版: !WSL_DISTRO!
echo.
echo ==============================================
echo [步骤3/3] 在 WSL Ubuntu 内安装 Buildozer/Android 构建依赖
echo ==============================================
set "WSL_CMD=set -e; sudo apt-get update; sudo apt-get install -y python3-pip python3-setuptools python3-wheel git zip unzip openjdk-17-jdk autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev; python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple; python3 -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple cython buildozer"
wsl -d "!WSL_DISTRO!" bash -lc "!WSL_CMD!"
if errorlevel 1 goto :err

:ok
echo.
echo 全部依赖安装流程已完成。
echo Next: run this in WSL
echo buildozer -v android debug
pause
exit /b 0

:err
echo.
echo 安装失败，请检查网络 / Python / WSL 环境。
pause
exit /b 1
