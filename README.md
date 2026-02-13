# VideoNote

**视频转笔记 — 让每个视频成为你的知识资产**

粘贴视频链接，AI 自动转录并生成结构化笔记。支持视频问答、视频下载。

## 功能

- **视频笔记** — 粘贴链接 → 自动转录 → AI 生成 Markdown 笔记
- **视频问答** — 基于视频内容的 AI 智能问答
- **视频下载** — 下载 YouTube / B站视频到本地

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3 + TypeScript + Vite |
| 后端 | Python FastAPI |
| 转录 | Faster-Whisper (本地) |
| AI | OpenAI API |
| 视频 | yt-dlp |

## 快速开始

### 前置要求

- Node.js 18+
- Python 3.10+
- FFmpeg

### 1. 克隆项目

```bash
git clone https://github.com/Joey-Ren/VideoNote.git
cd VideoNote
```

### 2. 启动后端

```bash
cd backend

# 创建虚拟环境并安装依赖
pip install uv
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 OpenAI API Key

# 启动
uv run uvicorn app.main:app --reload --port 8000
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 4. 打开浏览器

访问 http://localhost:5173

## 项目结构

```
VideoNote/
├── frontend/                # Vue3 前端
│   ├── src/
│   │   ├── api/            # API 层
│   │   ├── components/     # 组件
│   │   ├── composables/    # Vue Composables
│   │   ├── router/         # 路由
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── types/          # TypeScript 类型
│   │   └── views/          # 页面
│   └── package.json
├── backend/                 # Python 后端
│   ├── app/
│   │   ├── main.py         # FastAPI 入口 (< 60行)
│   │   ├── config.py       # 配置管理
│   │   ├── routers/        # API 路由 (5个模块)
│   │   ├── services/       # 业务逻辑 (5个服务)
│   │   ├── models/         # 数据模型
│   │   └── core/           # AI/Whisper 客户端
│   └── pyproject.toml
└── README.md
```

## License

MIT
