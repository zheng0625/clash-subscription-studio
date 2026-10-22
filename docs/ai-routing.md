# AI 分流预设 v0.2.0

清单日期：2026-10-22；24 组服务，67 条规则。

在“分流规则”点击“一键创建 AI 分流”，选择已有节点或代理组作为出口，点击“应用到草稿”，检查后“保存并发布”。默认建立 `🤖 AI 服务` 手动选择组。

预设规则放在普通规则之前，统一覆盖清单域名及其更窄域名的原有 DOMAIN / DOMAIN-SUFFIX 匹配。原始 YAML、规则与其他手动编辑记录保留；停用预设后，普通规则会恢复。上游刷新时重新应用预设。重复应用复用代理组并去重。

预设规则在列表中标记为“AI 预设”，通过“管理 AI 分流”统一修改出口；若要独立编辑这些规则，请停用预设后按普通规则添加。停用时保留 AI 组；重新启用会复用它，包括已重命名的组。启用中的 AI 组需要先停用预设才能删除。

规则不添加 no-resolve，不下载远程 GeoSite / AI 分类。共享登录、支付、通用 CDN，以及 Google / 微软 / GitHub 的其他流量继续按原规则处理。清单会随软件版本维护，不随第三方分类自动扩张。

按平台归属排除国内 AI 服务：不添加 DeepSeek、豆包、通义千问、文心、Kimi、智谱、腾讯元宝、MiniMax 等域名。Hugging Face / OpenRouter 中托管或调用的模型不按模型来源细分，因为分流按服务域名匹配。

出口是否满足服务地区、账号和节点 IP 要求，需要实际使用验证。

| 服务 | 匹配方式 | 域名 |
| --- | --- | --- |
| OpenAI / ChatGPT / Codex / Sora | `DOMAIN-SUFFIX` | `openai.com` |
| OpenAI / ChatGPT / Codex / Sora | `DOMAIN-SUFFIX` | `chatgpt.com` |
| OpenAI / ChatGPT / Codex / Sora | `DOMAIN-SUFFIX` | `chat.com` |
| OpenAI / ChatGPT / Codex / Sora | `DOMAIN-SUFFIX` | `sora.com` |
| OpenAI / ChatGPT / Codex / Sora | `DOMAIN-SUFFIX` | `oaistatic.com` |
| OpenAI / ChatGPT / Codex / Sora | `DOMAIN-SUFFIX` | `oaiusercontent.com` |
| Claude / Anthropic | `DOMAIN-SUFFIX` | `anthropic.com` |
| Claude / Anthropic | `DOMAIN-SUFFIX` | `claude.ai` |
| Claude / Anthropic | `DOMAIN-SUFFIX` | `claude.com` |
| Claude / Anthropic | `DOMAIN-SUFFIX` | `claudeusercontent.com` |
| Gemini / Google AI Studio | `DOMAIN-SUFFIX` | `gemini.google.com` |
| Gemini / Google AI Studio | `DOMAIN-SUFFIX` | `aistudio.google.com` |
| Gemini / Google AI Studio | `DOMAIN-SUFFIX` | `ai.google.dev` |
| Gemini / Google AI Studio | `DOMAIN` | `generativelanguage.googleapis.com` |
| Gemini / Google AI Studio | `DOMAIN` | `alkalimakersuite-pa.clients6.google.com` |
| Gemini / Google AI Studio | `DOMAIN` | `proactivebackend-pa.googleapis.com` |
| NotebookLM | `DOMAIN-SUFFIX` | `notebooklm.google.com` |
| NotebookLM | `DOMAIN-SUFFIX` | `notebooklm.google` |
| NotebookLM | `DOMAIN` | `notebooklm.googleapis.com` |
| NotebookLM | `DOMAIN` | `notebooklm-pa.googleapis.com` |
| Gemini Code Assist | `DOMAIN` | `cloudaicompanion.googleapis.com` |
| Gemini Code Assist | `DOMAIN` | `cloudcode-pa.googleapis.com` |
| Gemini Code Assist | `DOMAIN` | `daily-cloudcode-pa.googleapis.com` |
| Grok / xAI | `DOMAIN-SUFFIX` | `grok.com` |
| Grok / xAI | `DOMAIN-SUFFIX` | `x.ai` |
| Grok / xAI | `DOMAIN-SUFFIX` | `grok.x.com` |
| Microsoft Copilot | `DOMAIN-SUFFIX` | `copilot.com` |
| Microsoft Copilot | `DOMAIN-SUFFIX` | `copilot.microsoft.com` |
| Microsoft Copilot | `DOMAIN-SUFFIX` | `copilot.cloud.microsoft` |
| Perplexity | `DOMAIN-SUFFIX` | `perplexity.ai` |
| Perplexity | `DOMAIN-SUFFIX` | `perplexity.com` |
| Perplexity | `DOMAIN-SUFFIX` | `pplx.ai` |
| Perplexity | `DOMAIN` | `ppl-ai-file-upload.s3.amazonaws.com` |
| Perplexity | `DOMAIN` | `pplx-res.cloudinary.com` |
| Poe | `DOMAIN-SUFFIX` | `poe.com` |
| Poe | `DOMAIN-SUFFIX` | `poecdn.net` |
| Meta AI | `DOMAIN-SUFFIX` | `meta.ai` |
| Muse AI | `DOMAIN-SUFFIX` | `muse.ai` |
| Mistral / Le Chat | `DOMAIN-SUFFIX` | `mistral.ai` |
| Cohere | `DOMAIN-SUFFIX` | `cohere.com` |
| Cohere | `DOMAIN-SUFFIX` | `cohere.ai` |
| Groq | `DOMAIN-SUFFIX` | `groq.com` |
| Cerebras | `DOMAIN-SUFFIX` | `cerebras.ai` |
| OpenRouter | `DOMAIN-SUFFIX` | `openrouter.ai` |
| Cursor | `DOMAIN-SUFFIX` | `cursor.com` |
| Cursor | `DOMAIN-SUFFIX` | `cursor.sh` |
| Cursor | `DOMAIN-SUFFIX` | `cursorapi.com` |
| Cursor | `DOMAIN-SUFFIX` | `cursor-cdn.com` |
| Cursor | `DOMAIN-SUFFIX` | `cursorvm.com` |
| Windsurf / Codeium | `DOMAIN-SUFFIX` | `windsurf.com` |
| Windsurf / Codeium | `DOMAIN-SUFFIX` | `windsurf.build` |
| Windsurf / Codeium | `DOMAIN-SUFFIX` | `codeium.com` |
| Windsurf / Codeium | `DOMAIN-SUFFIX` | `codeiumdata.com` |
| GitHub Copilot | `DOMAIN-SUFFIX` | `githubcopilot.com` |
| GitHub Copilot | `DOMAIN` | `copilot-proxy.githubusercontent.com` |
| GitHub Copilot | `DOMAIN` | `copilot-workspace.githubnext.com` |
| GitHub Copilot | `DOMAIN` | `copilotprodattachments.blob.core.windows.net` |
| Hugging Face | `DOMAIN-SUFFIX` | `huggingface.co` |
| Hugging Face | `DOMAIN-SUFFIX` | `hf.co` |
| Hugging Face | `DOMAIN-SUFFIX` | `hf.space` |
| Midjourney | `DOMAIN-SUFFIX` | `midjourney.com` |
| ElevenLabs | `DOMAIN-SUFFIX` | `elevenlabs.io` |
| ElevenLabs | `DOMAIN-SUFFIX` | `elevenlabs.com` |
| Suno | `DOMAIN-SUFFIX` | `suno.com` |
| Suno | `DOMAIN-SUFFIX` | `suno.ai` |
| Runway | `DOMAIN-SUFFIX` | `runway.com` |
| Runway | `DOMAIN-SUFFIX` | `runwayml.com` |

来源核对：

- [domain-list-community](https://github.com/v2fly/domain-list-community/tree/master/data)
- [Google AI 专用接口](https://github.com/v2fly/domain-list-community/blob/master/data/google-deepmind)
- [GitHub Copilot 接口](https://github.com/v2fly/domain-list-community/blob/master/data/github-copilot)
- [Muse AI](https://muse.ai/)
- [Suno](https://suno.com/)
- [Runway](https://runway.com/)
