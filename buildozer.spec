[app]
title = UDIPrinterMLKit
package.name = udiprintermlkit
package.domain = com.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0

requirements = python3,kivy,pyjnius
orientation = portrait

# Android 编译参数
android.api = 33
android.minapi = 24
android.archs = arm64-v8a,armeabi-v7a
android.enable_androidx = True

# 权限
android.permissions = CAMERA,BLUETOOTH,BLUETOOTH_ADMIN,ACCESS_FINE_LOCATION,BLUETOOTH_CONNECT,BLUETOOTH_SCAN

# ML Kit / Google Code Scanner 依赖（支持 DataMatrix）
android.gradle_dependencies = com.google.android.gms:play-services-code-scanner:16.1.0

# 如需指定仓库可打开（通常不必）
# android.add_gradle_repositories = https://maven.google.com

log_level = 2

[buildozer]
warn_on_root = 1
