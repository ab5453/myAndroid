# 蓝牙打印APP（ML Kit DataMatrix 版）

## 你要的功能
- UI界面
- 点击“扫描UDI（ML Kit）” -> 调用 Google ML Kit 扫码（优先 DataMatrix，兼容 QR）
- 识别结果写入文本框
- 点击“蓝牙打印” -> 连接已配对蓝牙打印机并打印文本

## 文件说明
- `main.py`：主程序
- `buildozer.spec`：Android 打包配置（已含 ML Kit 依赖）
- `一键安装全部依赖_国内镜像.bat`：国内镜像一键安装依赖命令

## 一键安装依赖（国内镜像）
双击执行：

```text
一键安装全部依赖_国内镜像.bat
```

## 运行与打包
### 本机 UI 预览（Windows）
```bash
python main.py
```
> 扫码与蓝牙打印功能仅 Android 真机有效。

### 打包 APK（WSL / Ubuntu）
在项目目录执行：
```bash
buildozer -v android debug
```

## 备注
- 该方案使用 `com.google.android.gms:play-services-code-scanner`（ML Kit 扫码）。
- UDI 在医疗场景常见 DataMatrix；本项目默认优先 DataMatrix。
