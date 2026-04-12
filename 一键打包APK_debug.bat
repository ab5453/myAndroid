@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 开始在 WSL 中打包 Debug APK...
wsl bash -lc "cd '/mnt/c/Users/13871/Desktop/蓝牙打印APP' && buildozer -v android debug"
echo.
echo 打包结束后请查看 bin 目录。
pause
