# VideoNote 产品设计文档

> 最后更新：2026-02-13
> 状态：MVP 开发中

---

## 一、产品定位

**一句话**：粘贴视频链接，AI 自动转录并生成结构化笔记。

**核心场景**：
- 学习者看完一个技术视频，想快速得到笔记
- 内容创作者需要把视频内容转成文字稿
- 知识工作者需要从视频中提取关键信息

**目标用户**：学习者、内容创作者、知识工作者

**产品形态**：开源 Web 应用，`git clone` 下来就能跑

---

## 二、竞品分析（ViNote）

我们参考了开源项目 [ViNote](https://github.com/user/ViNote)（视频转笔记赛道），做了深度代码分析。

### 值得借鉴

| 特性 | 说明 | 我们的借鉴 |
|------|------|-----------|
| SSE 实时进度推送 | 长任务不焦虑，用户能看到处理进度 | ✅ 已实现 |
| 分块摘要 + 上下文保留 | 长文本先分块总结再合并，块间保留尾部上下文防断裂 | ✅ 已实现 |
| 多级降级策略 | YouTube API → yt-dlp → 错误兜底 | 部分借鉴 |
| AI 思维链可视化 | 让用户看到 AI 在"想什么"，增加信任感 | 待实现 |

### 他们的硬伤（我们要避免的）

| 问题 | 严重度 | 我们的方案 |
|------|--------|-----------|
| main.py 1400+ 行 God Object | 🔴 高 | main.py 仅 50 行，路由/服务完全拆分 |
| JSON 文件存储，无数据库 | 🔴 高 | 预留数据库接口，后续接入 SQLite/PostgreSQL |
| 全局状态满天飞，竞态风险 | 🔴 高 | 服务类封装，状态隔离 |
| 前端原生 JS，15+ 文件无框架 | 🟡 中 | Vue3 + TypeScript，组件化开发 |
| 零测试、无 CI/CD | 🔴 高 | 后续补充测试和 GitHub Actions |
| 绑死 OpenAI，无模型抽象 | 🟡 中 | 配置化模型选择，支持 base_url 自定义 |
| Docker 部署门槛高 | 🟡 中 | npm + pip 直接跑，不依赖 Docker |

### 竞品成熟度评估

| 维度 | ViNote | VideoNote（我们） |
|------|--------|------------------|
| 代码质量 | ⭐⭐⭐ | ⭐⭐⭐⭐（模块化清晰） |
| 工程化 | ⭐⭐ | ⭐⭐⭐（待补测试/CI） |
| 产品完成度 | ⭐⭐⭐ | ⭐⭐（骨架+真实服务） |
| 可扩展性 | ⭐⭐ | ⭐⭐⭐⭐（预留接口） |
| UI/UX | ⭐⭐⭐⭐ | ⭐⭐⭐（待打磨） |

---

## 三、功能规划

### MVP（当前阶段）

| 功能 | 状态 | 说明 |
|------|------|------|
| 视频预览 | ✅ 已实现 | 粘贴链接 → 显示标题/封面/时长 |
| 音频转录 | ✅ 已实现 | 本地 Faster-Whisper，SSE 进度推送 |
| AI 笔记生成 | ✅ 已实现 | 分块摘要 + 流式输出 Markdown |
| 视频问答 | ✅ 已实现 | 基于转录内容的 AI 问答，流式输出 |
| 视频下载 | ✅ 已实现 | 支持 mp4/mp3，多画质选择 |
| 设置页面 | ✅ 已实现 | API Key 配置、模型选择 |

### Phase 2（计划中）

| 功能 | 优先级 | 说明 |
|------|--------|------|
| 数据库持久化 | 🔴 高 | SQLite 存储历史笔记和转录记录 |
| 笔记历史管理 | 🔴 高 | 查看、搜索、删除历史笔记 |
| 多模型适配 | 🟡 中 | 支持 Claude、Gemini、国产大模型 |
| 笔记编辑器 | 🟡 中 | 在线编辑生成的 Markdown 笔记 |
| 批量处理 | 🟢 低 | 一次性处理多个视频链接 |
| AI 思维链可视化 | 🟢 低 | 展示 AI 处理过程，增加信任感 |

### Phase 3（远期）

| 功能 | 说明 |
|------|------|
| 本地文件上传 | 支持上传本地视频/音频文件 |
| 字幕生成与导出 | SRT/VTT 字幕文件导出 |
| 笔记模板自定义 | 用户自定义笔记输出格式 |
| 多语言支持 | 英文/日文等多语言转录和笔记 |
| 协作分享 | 笔记分享链接、团队协作 |

---

## 四、技术架构

### 整体架构

```
┌─────────────────────────────────────────────┐
│  Frontend: Vue3 + TypeScript + Vite          │
│  暗色主题 · Pinia 状态管理 · SSE 实时通信      │
├─────────────────────────────────────────────┤
│  Backend: Python FastAPI                     │
│  5 Router · 5 Service · Pydantic 配置管理     │
│  main.py 仅 50 行（vs 友商 1400 行）           │
├─────────────────────────────────────────────┤
│  AI 层                                       │
│  OpenAI API（可配 base_url 兼容其他模型）       │
│  Faster-Whisper 本地转录                      │
├─────────────────────────────────────────────┤
│  工具层                                       │
│  yt-dlp 视频下载 · FFmpeg 音频处理             │
└─────────────────────────────────────────────┘
```

### 技术栈

| 层 | 技术 | 选型理由 |
|---|------|---------|
| 前端框架 | Vue 3 + TypeScript | 组件化、类型安全、生态成熟 |
| 构建工具 | Vite | 快速 HMR，开发体验好 |
| 状态管理 | Pinia | Vue3 官方推荐，轻量 |
| 样式 | SCSS + CSS Variables | 暗色主题，变量统一管理 |
| 后端框架 | FastAPI | 异步原生、自动文档、类型校验 |
| 配置管理 | pydantic-settings | .env 文件一键配置，类型安全 |
| 语音转录 | Faster-Whisper | 本地运行，无需付费 API |
| AI 模型 | OpenAI API | 通过 base_url 兼容各种模型 |
| 视频处理 | yt-dlp + FFmpeg | 支持 YouTube/B站等主流平台 |
| 包管理 | npm (前端) + uv (后端) | uv 比 pip 快 10-100 倍 |

### 项目结构

```
VideoNote/
├── frontend/                    # Vue3 前端
│   ├── src/
│   │   ├── api/index.ts        # API 请求封装
│   │   ├── assets/styles/      # 全局样式 + SCSS 变量
│   │   ├── components/layout/  # 布局组件（Header、Layout）
│   │   ├── composables/        # Vue Composables（useSSE）
│   │   ├── router/index.ts     # 路由配置
│   │   ├── stores/app.ts       # Pinia 全局状态
│   │   ├── types/index.ts      # TypeScript 类型定义
│   │   └── views/              # 4 个页面
│   │       ├── VideoNote.vue   # 视频笔记（核心页面）
│   │       ├── VideoQA.vue     # 视频问答
│   │       ├── VideoDownload.vue # 视频下载
│   │       └── Settings.vue    # 设置
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                     # Python 后端
│   ├── app/
│   │   ├── main.py             # FastAPI 入口（50 行）
│   │   ├── config.py           # pydantic-settings 配置
│   │   ├── core/               # 核心客户端
│   │   │   ├── ai_client.py    # OpenAI 客户端（懒加载单例）
│   │   │   └── whisper_client.py # Whisper 模型（懒加载单例）
│   │   ├── models/schemas.py   # Pydantic 数据模型
│   │   ├── routers/            # 5 个路由模块
│   │   │   ├── video.py        # 视频预览
│   │   │   ├── transcribe.py   # 转录
│   │   │   ├── note.py         # 笔记生成
│   │   │   ├── qa.py           # 问答
│   │   │   └── download.py     # 下载
│   │   ├── services/           # 5 个业务服务
│   │   │   ├── video_service.py
│   │   │   ├── transcribe_service.py
│   │   │   ├── note_service.py
│   │   │   ├── qa_service.py
│   │   │   └── download_service.py
│   │   └── utils/text.py       # 文本分块工具
│   ├── pyproject.toml
│   └── .env.example
│
├── docs/                        # 文档
│   └── PRODUCT_DESIGN.md       # 本文件
└── README.md
```

---

## 五、核心流程

### 视频笔记生成流程

```
用户粘贴链接 → 预览视频信息
     │
     ▼
点击"生成笔记"
     │
     ├─ Step 1: 音频转录（SSE 进度推送）
     │   ├─ yt-dlp 下载音频
     │   ├─ Faster-Whisper 本地转录
     │   └─ 返回带时间戳的转录文本
     │
     ├─ Step 2: AI 笔记生成（流式输出）
     │   ├─ 长文本分块摘要（chunk_size=8000, overlap=200）
     │   ├─ 合并摘要 → GPT 生成结构化 Markdown
     │   └─ 流式推送到前端实时渲染
     │
     └─ 完成 → 用户可下载 Markdown 文件
```

### 关键技术决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 转录方案 | 本地 Faster-Whisper | 免费、隐私安全、无文件大小限制 |
| 长文本处理 | 分块摘要 + 合并 | 避免 token 超限，保留上下文连贯性 |
| 实时通信 | SSE（Server-Sent Events） | 单向推送足够，比 WebSocket 简单 |
| 异步处理 | asyncio + ThreadPoolExecutor | CPU 密集任务（Whisper/yt-dlp）丢线程池 |
| 客户端初始化 | 懒加载单例 | 首次使用时才加载 Whisper 模型，节省启动时间 |
| 配置管理 | pydantic-settings + .env | 类型安全，一个 .env 文件搞定所有配置 |

---

## 六、API 设计

### 视频相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/video/preview` | 获取视频信息（标题/封面/时长） |

### 转录相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/transcribe/start` | 开始转录任务，返回 task_id |
| GET | `/api/transcribe/progress/{task_id}` | SSE 推送转录进度 |
| GET | `/api/transcribe/result/{task_id}` | 获取转录结果 |

### 笔记相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/note/generate` | 开始生成笔记，返回 task_id |
| GET | `/api/note/stream/{task_id}` | SSE 流式推送笔记内容 |
| GET | `/api/note/result/{task_id}` | 获取完整笔记结果 |

### 问答相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/qa/ask` | 基于视频内容问答（流式输出） |

### 下载相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/download/start` | 开始下载任务 |
| GET | `/api/download/progress/{task_id}` | SSE 推送下载进度 |
| GET | `/api/download/file/{task_id}` | 获取下载文件 |

### 系统

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |

---

## 七、数据模型

### 请求模型

```python
VideoPreviewRequest { url: str }
TranscribeRequest   { url?: str, local_path?: str }
NoteGenerateRequest { transcription_text: str, language: str = "zh" }
QARequest           { video_url: str, question: str, context?: str }
DownloadRequest     { url: str, format: str = "mp4", quality: str = "best" }
```

### 响应模型

```python
VideoInfo {
    title: str, thumbnail?: str, duration: int,
    platform: str, url: str
}

TranscriptionResult {
    text: str, segments: [{ start, end, text }],
    language: str, duration: float
}

NoteResult {
    markdown: str, title: str, outline: [str]
}

TaskResponse { task_id: str, status: str, message: str }
```

### SSE 事件格式

```json
// 进度事件
{ "status": "processing", "progress": 45, "message": "转录中... 45%" }

// 流式内容
{ "status": "streaming", "content": "## 核心要点\n" }

// 完成
{ "status": "completed" }

// 错误
{ "status": "error", "message": "转录失败: ..." }
```

---

## 八、配置项

通过 `.env` 文件配置，所有配置项：

```env
# OpenAI（必填）
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1    # 可改为其他兼容 API
OPENAI_MODEL=gpt-4o                           # 可选 gpt-3.5-turbo 等

# Whisper（可选，默认 base）
WHISPER_MODEL_SIZE=base                        # tiny/base/small/medium/large

# YouTube API（可选，加速视频预览）
YOUTUBE_API_KEY=

# 应用
APP_HOST=0.0.0.0
APP_PORT=8000
TEMP_DIR=./temp
```

---

## 九、部署方式

### 开发环境（当前）

```bash
# 1. 克隆
git clone https://github.com/Joey-Ren/VideoNote.git
cd VideoNote

# 2. 后端
cd backend
pip install uv && uv sync
cp .env.example .env  # 填入 OPENAI_API_KEY
uv run uvicorn app.main:app --reload --port 8000

# 3. 前端
cd frontend
npm install
npm run dev

# 4. 访问 http://localhost:5173
```

### 前置依赖

- Node.js 18+
- Python 3.10+
- FFmpeg（音频处理必需）

---

## 十、与友商的差异化总结

| 维度 | ViNote（友商） | VideoNote（我们） |
|------|---------------|------------------|
| 前端 | 原生 HTML/JS，15+ 文件 | Vue3 + TypeScript，组件化 |
| 后端入口 | main.py 1400+ 行 | main.py 50 行，5 路由 5 服务 |
| 存储 | JSON 文件 | 预留数据库接口 |
| 配置 | 散落各处 | pydantic-settings 统一管理 |
| 类型安全 | 无 | 前后端全类型覆盖 |
| 部署 | Docker（门槛高） | npm + pip 直接跑 |
| 测试 | 零 | 待补充（架构已预留） |
| 模型 | 绑死 OpenAI | base_url 可配，兼容多模型 |

---

## 十一、待解决的问题

1. **任务状态内存存储** — 重启丢失，需要持久化方案
2. **临时文件清理** — 下载/转录的临时文件需要定期清理
3. **并发限制** — Whisper 转录是 CPU 密集型，需要限制并发数
4. **错误恢复** — 长任务中断后的恢复机制
5. **前端 UI 打磨** — 当前是基础骨架，视觉效果待提升
6. **测试覆盖** — 前后端均无测试，需要补充

---

## 十二、GitHub 仓库

- **地址**：https://github.com/Joey-Ren/VideoNote
- **当前版本**：v0.1.0（MVP 骨架 + 真实服务实现）
- **Commit 历史**：
  1. `Initial commit` — 仓库初始化
  2. `init: VideoNote 项目骨架搭建` — 前后端骨架
  3. `feat: 全部服务真实实现 + 前端联调` — 服务真实实现
