# 原生发行包 / Native packages

[English below](#english)

原生包将 Python 解释器、后端依赖和前端构建资源一起打包；使用者不需要安装 Python、Node.js、pip 或 npm，也不需要首次联网安装依赖。仍需要系统自带的网页浏览器和受支持的操作系统。订阅导入和刷新需要按来源访问网络。

## 下载与启动

| 平台 | 文件后缀 | 启动 | 停止 |
| --- | --- | --- | --- |
| Windows x64 | `windows-x64.zip` | 解压整个目录，双击 `ClashStudio.exe` 或 `Start.cmd` | `Stop.cmd` 或终端 Ctrl+C |
| Linux x64 | `linux-x64.tar.gz` | 解压后运行 `./Start.sh` | `./Stop.sh` 或终端 Ctrl+C |
| Linux ARM64 | `linux-arm64.tar.gz` | 同上，适用于 ARM64 系统 | 同上 |
| macOS Intel | `macos-x64.tar.gz` | 解压后打开 `ClashStudio.app`，或双击 `Start.command` | `Stop.command` |
| macOS Apple Silicon | `macos-arm64.tar.gz` | 同上，适用于 M 系列 Mac | 同上 |

不要只复制主程序。`_internal`、`.app` 内部结构和其他随包文件需要完整保留。关闭浏览器不会停止后端，局域网订阅更新需要程序继续运行。默认管理地址仍是 `http://127.0.0.1:8765`。

macOS 包目前没有开发者证书签名和 Apple 公证，系统可能要求用户在隐私与安全设置中确认来源。该构建不宣称已经通过 Gatekeeper 或所有 macOS 版本的实际设备验收。Linux x64 构建基于 Ubuntu 22.04，ARM64 构建基于 Ubuntu 24.04；需要兼容相应的 glibc 系统，不适用于 Alpine/musl。Windows 包面向 Windows 10/11 x64。

## 用户数据

原生包默认将数据放在用户目录，更新程序时不覆盖：

- Windows：`%LOCALAPPDATA%\ClashStudio`
- macOS：`~/Library/Application Support/ClashStudio`
- Linux：`${XDG_DATA_HOME:-~/.local/share}/clash-studio`

源码模式继续使用项目目录 `data/`。旧版用户可关闭两个版本后，将旧 `data/` 的内容复制到上述目录；或使用 `--data-dir <旧数据目录>`。同一数据库不能同时由两个服务实例写入。订阅地址中的令牌会随数据库保留，但电脑 IP、端口或路径变化时需更新客户端链接。环境变量 `CLASH_STUDIO_DATA` 也可覆盖数据目录。

所有原生可执行程序均支持 `--port 8877`、`--no-browser`、`--data-dir <path>`、`--stop` 和 `--version`。macOS 的命令行入口为 `ClashStudio.app/Contents/MacOS/ClashStudio`。

## 构建与分发

前端构建完成后，在对应系统安装 `requirements-build.txt`，执行 `python scripts/build_native.py`。PyInstaller 不是跨系统编译器，需要在目标系统和目标架构构建。GitHub Actions `Native packages` 为五种平台分别生成候选附件，不会自动发布 Release。

原生包包含完整项目源码 ZIP、GPL 许可证、第三方声明、Python/依赖许可文件、依赖版本列表与 SHA-256 文件清单。构建成功不等同于实际设备可用性确认；请先验收候选包再发布。

## English

Native distributions bundle the Python interpreter, backend dependencies and prebuilt frontend. End users do not need Python, Node.js, pip/npm or a first-run dependency download. A supported OS and a web browser are still required. Importing or refreshing a remote subscription requires access to its source.

Extract the complete archive. On Windows, open `ClashStudio.exe` or `Start.cmd`; on Linux, run `./Start.sh`; on macOS, open `ClashStudio.app` or `Start.command`. Use the accompanying Stop launcher to shut down the backend. Closing the browser does not stop it. Keep bundled directories intact.

Choose the archive matching your OS and CPU. Linux x64 targets Ubuntu 22.04-compatible glibc systems; Linux ARM64 targets Ubuntu 24.04-compatible systems. Alpine/musl is not supported. macOS packages are not Developer ID signed or notarized; macOS may require user approval. This does not claim physical-device validation on every supported system. Windows packages target Windows 10/11 x64.

Persistent data lives under `%LOCALAPPDATA%\ClashStudio` (Windows), `~/Library/Application Support/ClashStudio` (macOS), or `${XDG_DATA_HOME:-~/.local/share}/clash-studio` (Linux). Source checkouts keep using `data/`. To migrate, stop both versions and copy the old data into the new location, or pass `--data-dir <old-data-directory>`. Do not run two instances against one database.

Use `--port`, `--no-browser`, `--data-dir`, `--stop` or `--version` as needed. Native packages contain corresponding project source, licenses, dependency notices and checksums. CI builds candidates only; publishing a release remains a separate acceptance step.
