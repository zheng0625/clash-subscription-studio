# Clash Studio · 本地订阅工作台

可视化编辑 Clash / Mihomo 订阅：导入配置、调整节点和代理组、编辑分流规则，再生成供本机或局域网设备使用的订阅地址。

**版本：v0.4.0-rc.1 · 已通过用户手动测试并公开发布（预发布版）。**

[下载发行包](https://github.com/zheng0625/clash-subscription-studio/releases/tag/v0.4.0-rc.1) · [源码仓库](https://github.com/zheng0625/clash-subscription-studio)

## 功能

- 从订阅 URL、YAML 文件或内置示例导入。
- 节点改名和排除，代理组策略与成员调整，规则添加、排序和搜索。
- 草稿预览与保存发布分离，源订阅更新后重新应用编辑记录。
- 历史版本恢复，独立随机令牌订阅地址，支持停用和重新生成。
- 一键创建 AI 分流：24 组服务、67 条域名规则，包含 Muse AI。
- 可选局域网只读订阅共享，管理界面保持仅本机访问。
- 五套主题预设与六项自定义颜色，配色自动保存在当前浏览器。

## Windows 启动

1. 完整解压发行包到一个新目录。
2. 安装 Python 3.11 或更新版本，并确保能从命令行使用。
3. 双击 **启动软件.cmd**，等待依赖安装，然后打开 `http://127.0.0.1:8765`。
4. 首次使用可点“载入演示配置”。演示节点不能实际联网。

发行 ZIP 包含源码与构建后的前端，**不是独立 EXE，也不包含 Python 运行时**。首次启动需要联网安装 Python 依赖。从 GitHub 源码启动时还需要 Node.js 20.19+ / 22.12+ 和 npm 或 pnpm，用于构建界面。已存在的本地 Codex runtime 会被启动脚本识别，但不是必需条件。

服务运行期间保持启动窗口打开。关闭服务请双击 **停止服务.cmd**，或在启动窗口按 Ctrl+C。局域网设备更新订阅时，电脑和本软件必须保持运行。

```powershell
.\start.ps1                  # 启动并打开浏览器
.\start.ps1 -Port 8877       # 使用其他管理端口
.\start.ps1 -Rebuild        # 重建前端
.\start.ps1 -NoBrowser      # 仅启动服务
.\stop.ps1                  # 停止服务
```

## 数据与局域网

配置、编辑记录、历史、发布 YAML 和订阅令牌默认保存在当前软件目录的 `data/` 中；局域网设置位于 `data/network.json`。不会自动上传到 GitHub。浏览器只保存界面偏好和上次选中的订阅 ID。

管理服务仅绑定回环地址，默认 `127.0.0.1:8765`。局域网共享默认关闭；在订阅“设置”中开启后，右侧选择“局域网”并复制地址到同一网络的设备。共享使用独立端口，默认 8767，只提供带令牌的订阅下载，不开放编辑界面。详见 [局域网共享说明](docs/lan-sharing.md)。

本机地址和局域网地址使用相同令牌与已发布配置。重置令牌或停用订阅会同时影响两种地址。请在可信网络传递链接，不做公网端口映射。必要时手动运行 **配置局域网防火墙.cmd**，其仅放行专用网络下本地子网的当前共享端口。

## 开发、测试与打包

技术栈：Vue 3 / TypeScript / Vite，FastAPI / SQLite / ruamel.yaml。

源码构建：在 `frontend/` 运行 `pnpm install --frozen-lockfile`、`pnpm build`，然后通过 Python 虚拟环境安装 `requirements.txt`，运行 `python run.py`。

- [贡献与开发说明](CONTRIBUTING.md)
- [架构与接口](docs/architecture.md)
- [AI 分流说明](docs/ai-routing.md)
- [验证范围](docs/verification.md)
- [发行前手动测试清单](docs/release-checklist.md)
- [安全与隐私](SECURITY.md)
- [更新记录](CHANGELOG.md)

`python scripts/package.py` 按白名单打包源码、文档、许可证和构建后的前端，并生成文件清单与 ZIP SHA-256 校验值。不会收录 `data/`、数据库、备份、截图、虚拟环境、node_modules 或 Git 历史。

## 范围

不提供代理节点或账号，不处理代理流量，不是 Clash/Mihomo 内核。基础结构和引用检查不能替代客户端内核兼容性验证。未实现所有协议参数、全部规则语义、外部 provider 展开、节点测速、多订阅聚合或桌面安装器。自动刷新只在本服务运行时执行。

## 许可证

Copyright (C) 2026 zheng0625 and contributors.

本项目原始代码按 **GPL-3.0-only** 许可，完整条款见 [LICENSE](LICENSE)。对外分发修改版本时，请遵守 GPL 的源码提供等要求。本软件按原样提供，不提供担保。第三方依赖保留各自许可，随包声明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
