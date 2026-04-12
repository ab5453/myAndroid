# Git 云打包（GitHub Actions）

已配置文件：
- `.github/workflows/android-build.yml`
- `.gitignore`

## 1) 初始化 git（如果还没初始化）
在项目目录执行：

```bash
git init
git add .
git commit -m "init: enable github cloud apk build"
```

## 2) 关联你的 GitHub 仓库并推送
把下面的 `<你的仓库地址>` 换成实际地址：

```bash
git branch -M main
git remote add origin <你的仓库地址>
git push -u origin main
```

## 3) 云端打包触发方式
- 推送到 `main/master` 自动触发
- 或去 GitHub 页面：`Actions -> Android APK Build (Buildozer) -> Run workflow`

## 4) 下载 APK
- 进入对应 workflow run
- 在 `Artifacts` 下载 `udiprintermlkit-apk`

## 常见问题
1. **构建超时/失败**
   - 重新运行一次（首次会下载很多依赖）
2. **找不到 APK**
   - 检查 `buildozer.spec` 是否正常
   - 看日志里 `bin/` 是否生成 apk
3. **分支名不是 main/master**
   - 改 workflow 的分支触发条件
