# Ice 简体中文版

[![同步上游并发布汉化版](https://github.com/TOKIO233/Ice-zh/actions/workflows/chinese-release.yml/badge.svg)](https://github.com/TOKIO233/Ice-zh/actions/workflows/chinese-release.yml)

基于 [Jordan Baird 的 Ice](https://github.com/jordanbaird/Ice) 的简体中文社区 Fork。当前基线为 **0.11.13-dev.2**，包含 macOS 26 Tahoe 兼容修复。保留原作者署名及 GPL-3.0 许可证。

**[下载汉化版](https://github.com/TOKIO233/Ice-zh/releases) · [查看自动构建](https://github.com/TOKIO233/Ice-zh/actions/workflows/chinese-release.yml) · [反馈问题](https://github.com/TOKIO233/Ice-zh/issues)**

## 使用

在 Releases 下载 `Ice-zh-universal.zip`，解压后将 `Ice.app` 放入应用程序目录。支持 Apple Silicon 和 Intel，最低系统要求为 macOS 14。系统首选语言为简体中文时自动显示中文；其他语言回退到英文。

- 汉化范围：通用设置、菜单栏布局、外观、快捷键、高级设置、权限提示、右键菜单及主要错误提示。
- 独立应用标识为 `com.tokio233.Ice.zh`，设置和权限与官方版分开。使用时请退出其他菜单栏管理工具，并为本版授予辅助功能、屏幕录制权限。
- 社区安装包使用 **ad-hoc 签名**，当前没有 Apple Developer ID 签名与公证。macOS 可能阻止首次打开；本项目不会自动修改系统安全设置。
- 应用内“查看汉化版更新”打开本仓库发布页，以下载替换方式更新。

## 上游自动更新

默认开发分支为 `zh-CN`，原始 `main` 保留上游历史。`localization/upstream.json` 记录已同步的发布标签、提交和发布时间。

GitHub Actions 每小时第 23 分钟（UTC）检查 `jordanbaird/Ice` 的新 **Release**，包含正式版和预发布版。GitHub 的计划任务可能延迟；上游仅提交代码且尚未发布 Release 时，维持当前基线。

1. 发现新发布后进行普通 Git 合并，保留汉化改动，不强推。
2. 构建 Apple Silicon + Intel 通用版，检查编译器提取的文案、动态菜单名称、翻译占位符和包内资源，并在 macOS 26 上实测签名后的主程序与图标服务连接。
3. 检查全部通过后自动创建中文 Release，并上传 ZIP 与 SHA-256 校验文件。发布标签格式为 `<上游标签>-zh.<构建编号>`。
4. 合并冲突时停止同步；编译失败或新增文案待翻译时停止发布。已有可用 Release 保留，Actions 内可下载 `build-reports` 查看日志与 `translation-report.json`。

**新增文案需要补译后才能发布。** 自动化负责同步、校验、构建和发布，当前不调用外部机器翻译服务。补译推送后会自动重新构建，也可以在 Actions 页面点击 **Run workflow** 手动运行。

GitHub 对公共仓库的定时任务有闲置停用规则：连续 60 天没有仓库活动时可能自动停用。届时在 Actions 中重新启用工作流即可。使用默认 `GITHUB_TOKEN`，无需额外个人令牌或付费服务密钥。

## 维护与构建

使用 Xcode 26 或更新的兼容版本。

```bash
# 修改词典后生成原生语言资源
python3 scripts/localization.py generate
python3 scripts/localization.py check
python3 -m unittest discover -s tests -v

# 构建 Intel / Apple Silicon 通用版
xcodebuild -project Ice.xcodeproj -scheme Ice -configuration Release \
  -derivedDataPath build/DerivedData CODE_SIGNING_ALLOWED=NO \
  ONLY_ACTIVE_ARCH=NO 'ARCHS=arm64 x86_64' SWIFT_EMIT_LOC_STRINGS=YES build

# 检查新增文案并打包
python3 scripts/localization.py audit --derived-data build/DerivedData
bash scripts/package.sh build/DerivedData/Build/Products/Release/Ice.app dist
# macOS 26 上验证实际 XPC 连接
python3 scripts/check_xpc.py build/DerivedData/Build/Products/Release/Ice.app
```

翻译词典位于 [`localization/zh-Hans.json`](../localization/zh-Hans.json)，生成的资源位于 `Ice/Resources/zh-Hans.lproj/Localizable.strings`。界面文案保持英文源键；配置枚举的原始值保持稳定。新增以普通字符串动态拼接的界面文案，应改用 `String(localized:)` 或 `LocalizedStringKey`，并按需要补充动态文案检查规则。

构建报告覆盖编译器可提取的文案和明确列出的动态名称；应用名称、第三方图标名称、系统错误及系统界面由各自来源提供。上游说明见根目录的 [README.md](../README.md)。
