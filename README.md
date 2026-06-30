# 抖音聊天记录导出工具

从抖音网页版完整导出私信聊天记录，并提供本地 Web 浏览界面。

**目录**：[功能](#功能) · [环境要求](#环境要求) · [部署](#部署方式) · [使用](#使用) · [控制面板](#4-控制面板) · [失败通知](#配置失败通知server酱) · [注意事项](#注意事项)

## 功能

- **完整导出**：通过直接调用抖音 IM API（protobuf），突破虚拟列表滚动上限，可导出完整历史记录
- **精确排序**：使用服务端 `created_at_us` 单调递增序号排序，确保消息顺序正确
- **多种消息类型**：文本、表情包、图片、语音、分享视频/商品/直播、系统消息等
- **引用/回复消息**：提取引用消息数据，前端显示引用区块并支持点击跳转到原消息
- **语音消息**：自动下载语音文件到本地，前端支持播放
- **图片本地化**：可开关「自动下载原图」+「回填历史图片」，AES-GCM 解密 + HEIC 自动转 JPEG，前端支持点击放大
- **增量更新**：支持增量模式，只获取新消息
- **前端浏览器**：内置 Vue 3 + FastAPI 聊天记录浏览界面，支持无限滚动、全文搜索、搜索跳转
- **ChatLab 导出**：支持导出为 [ChatLab](https://github.com/hellodigua/ChatLab) 标准格式（JSON/JSONL），可用于 AI 聊天记录分析
- **控制面板**：Web 管理面板，可视化控制采集、导出、定时任务，支持远程扫码登录
- **失败通知**：采集失败时通过 [Server酱](https://sct.ftqq.com) 推送到微信，附带失败时间和日志末尾
- **Docker 部署**：支持 Docker 一键部署，含前端、后端、采集器

## 环境要求

| 依赖 | 版本要求 | 说明 |
|------|----------|------|
| Python | >= 3.10 | 后端服务与采集器 |
| Node.js | >= 20.19 或 >= 22.12 | 前端构建（Vite 7 要求） |
| Docker | >= 20.10（可选） | Docker 部署时需要，会自动处理上述依赖 |

> **Docker 用户**：无需手动安装 Python 和 Node.js，容器内已包含所有依赖，直接看方式二。

## 部署方式

### 方式一：Docker 部署（推荐，完美支持 macOS/Windows/Linux/ARM）

无需安装 Python / Node.js，Docker 会自动处理所有依赖。

```bash
git clone https://github.com/TeamBreakerr/douyin-chat-export.git
cd douyin-chat-export
docker compose up -d --build
```

容器启动后，可通过 `http://localhost:8000` 访问。数据持久化在当前目录的 `./data` 中。

#### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MODE` | `all` | `web` 只启动 Web 服务 / `scraper` 只执行采集 / `all` 全部启动 |
| `HEADLESS` | `true` | 浏览器是否无头模式（Docker 中必须为 true） |
| `SCRAPER_INCREMENTAL` | `true` | 采集是否增量模式 |
| `SCRAPER_FILTER` | (空) | 过滤指定会话名称 |
| `SCRAPER_SCHEDULE` | (空) | cron 表达式，如 `0 */6 * * *`（空=不定时） |

### 方式二：本地原生运行

```bash
# 创建 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows PowerShell

# 安装依赖
pip install -r requirements.txt
playwright install chromium

# 构建前端
cd frontend && npm install && npm run build && cd ..

# 启动服务
python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

## 使用

### 1. 登录

首次使用需要登录抖音，我们提供了三种跨平台极其稳定的登录方案：

#### 方案 A：本地扫码 + 云端注入凭证（⭐️强烈推荐，完美规避跨平台加密与验证码难题）

无论你是在公网 ARM 服务器、还是在本地 OrbStack 部署 Docker，**推荐直接在你的主设备（Mac/Windows）上运行提取脚本，一键注入到容器！**这能彻底解决跨平台同步时的 macOS 密钥串解密失败问题，以及无头浏览器由于缺乏 GPU 导致的极度卡顿。

1. 在你自己的电脑上，运行：
   ```bash
   python3 local_login.py
   ```
   *会弹出真实的图形化浏览器，你可以非常顺滑地完成扫码或滑块验证。成功后，跨平台兼容的明文 `cookies.json` 会保存在 `data/` 目录中。*

2. （如果你是本地 OrbStack 部署）：文件已自动映射，直接运行：
   ```bash
   docker exec douyin-chat-export python3 import_cookies.py
   ```
   （如果是远程服务器部署）：只需先用 `scp` 把 `data/cookies.json` 传到服务器的 `data` 目录下，再执行上面那句命令即可。

#### 方案 B：面板远程扫码（已针对无 GPU 环境深度优化）

打开控制面板 `http://localhost:8000/panel`，点击“扫码登录”。
系统会通过无头浏览器截取抖音二维码并展现在网页上。
*(注：由于我们优化了图片压缩比并加入了鼠标节流逻辑，现在即便是没有独立显卡的纯 CPU Linux/ARM 服务器，拖动滑块验证码也是“指哪打哪”零延迟！)*

#### 方案 C：手动导入 Cookie
在任意浏览器登录抖音 -> F12 -> Application -> Cookies -> `https://www.douyin.com` -> 复制所有，然后在控制面板里点击“导入 Cookie”粘贴。

---

### 2. 导出聊天记录

登录完成后，直接在浏览器访问 Web 控制面板（`http://localhost:8000/panel`），点击“获取聊天列表”，勾选想要的会话并点击开始导出。
全部导出后的数据（包含完整的独立网页版对话和静态资源）都会保存在 `data/exports` 目录下。

（你也可以通过命令行触发）
```bash
python3 extract.py --filter "会话名称" --incremental
```

### 3. 导出为 ChatLab 格式

支持导出为 [ChatLab](https://github.com/hellodigua/ChatLab) 标准格式，可直接导入 ChatLab 进行 AI 分析。

```bash
# 导出为 JSONL（默认）
python3 export.py --filter "会话名称"

# 指定输出路径
python3 export.py --filter "会话名称" --output data/export.jsonl
```

### 4. 控制面板

访问 `/panel` 可使用 Web 控制面板：

- **状态概览**：会话数、消息数、用户数
- **登录管理**：远程扫码登录、检查登录状态、清除会话
- **采集控制**：增量/全量切换、会话过滤（支持自定义输入）、实时日志
- **定时任务**：标准 cron 表达式、预设快捷按钮
- **导出管理**：选择格式和会话、一键导出下载
- **媒体下载**：新消息自动下载图片到本地、一键回填历史图片（避免 CDN 过期失效）

#### 配置失败通知（Server酱）

适合开启了定时任务的用户：cookie 失效、抖音接口变动等导致采集失败时主动推送微信。前往 [sct.ftqq.com](https://sct.ftqq.com) 复制 SendKey 并在控制面板设置即可。

## 注意事项

- 本工具仅用于导出**自己的**聊天记录备份，请勿用于非法用途
- 抖音可能随时更改 API 接口，导致工具失效
- 媒体 CDN URL 有签名有效期（约 1 年），过期后图片/表情包将无法显示（可通过面板开启本地化保护）

## License

MIT
