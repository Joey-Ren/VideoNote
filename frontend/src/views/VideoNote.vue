<template>
  <div class="page">
    <h1 class="page-title">视频笔记</h1>
    <p class="page-desc">粘贴视频链接，AI 自动生成结构化笔记</p>

    <!-- 输入区域 -->
    <div class="card input-section">
      <div class="input-row">
        <input
          v-model="videoUrl"
          class="input"
          placeholder="粘贴 YouTube / B站 视频链接..."
          @keydown.enter="handlePreview"
        />
        <button class="btn-primary" :disabled="!videoUrl" @click="handlePreview">
          预览
        </button>
      </div>
    </div>

    <!-- 视频预览 -->
    <div v-if="videoInfo" class="card preview-section">
      <div class="preview-content">
        <img
          v-if="videoInfo.thumbnail"
          :src="videoInfo.thumbnail"
          :alt="videoInfo.title"
          class="preview-thumb"
        />
        <div class="preview-info">
          <h3 class="preview-title">{{ videoInfo.title }}</h3>
          <div class="preview-meta">
            <span>{{ videoInfo.platform }}</span>
            <span>{{ formatDuration(videoInfo.duration) }}</span>
          </div>
        </div>
      </div>
      <button class="btn-primary" @click="handleGenerate">
        生成笔记
      </button>
    </div>

    <!-- 进度条 -->
    <div v-if="sse.status.value === 'processing'" class="card progress-section">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: sse.progress.value + '%' }" />
      </div>
      <p class="progress-text">{{ sse.message.value || '处理中...' }}</p>
    </div>

    <!-- 笔记结果 -->
    <div v-if="noteMarkdown" class="card result-section">
      <div class="result-header">
        <h3>生成结果</h3>
        <button class="btn-secondary" @click="handleDownload">
          下载 Markdown
        </button>
      </div>
      <div class="markdown-body" v-html="renderedNote" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { marked } from 'marked'
import { previewVideo } from '@/api'
import { useSSE } from '@/composables/useSSE'
import type { VideoInfo } from '@/types'

const videoUrl = ref('')
const videoInfo = ref<VideoInfo | null>(null)
const noteMarkdown = ref('')
const sse = useSSE()

const renderedNote = computed(() => {
  if (!noteMarkdown.value) return ''
  return marked(noteMarkdown.value)
})

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

async function handlePreview() {
  if (!videoUrl.value) return
  try {
    videoInfo.value = await previewVideo(videoUrl.value)
  } catch {
    // TODO: 错误提示
  }
}

function handleGenerate() {
  // TODO: 调用转录 + 笔记生成 API
  noteMarkdown.value = '# 笔记生成中...\n\n连接后端后将自动生成笔记内容。'
}

function handleDownload() {
  const blob = new Blob([noteMarkdown.value], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${videoInfo.value?.title || 'note'}.md`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.input-section {
  margin-bottom: $spacing-lg;
}

.input-row {
  display: flex;
  gap: $spacing-md;
}

.preview-section {
  margin-bottom: $spacing-lg;
}

.preview-content {
  display: flex;
  gap: $spacing-lg;
  margin-bottom: $spacing-lg;
}

.preview-thumb {
  width: 200px;
  height: 112px;
  object-fit: cover;
  border-radius: $radius-md;
  flex-shrink: 0;
}

.preview-info {
  flex: 1;
  min-width: 0;
}

.preview-title {
  font-size: $font-size-md;
  font-weight: 600;
  margin-bottom: $spacing-sm;
  color: $text-primary;
}

.preview-meta {
  display: flex;
  gap: $spacing-md;
  color: $text-secondary;
  font-size: $font-size-sm;
}

.progress-section {
  margin-bottom: $spacing-lg;
}

.progress-bar {
  height: 6px;
  background: $bg-input;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: $spacing-sm;
}

.progress-fill {
  height: 100%;
  background: $accent-primary;
  border-radius: 3px;
  transition: width $transition-base;
}

.progress-text {
  color: $text-secondary;
  font-size: $font-size-sm;
}

.result-section {
  margin-bottom: $spacing-lg;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-lg;

  h3 {
    font-size: $font-size-md;
    font-weight: 600;
  }
}

.markdown-body {
  color: $text-primary;
  line-height: 1.8;

  :deep(h1),
  :deep(h2),
  :deep(h3) {
    margin-top: $spacing-lg;
    margin-bottom: $spacing-md;
    color: $text-primary;
  }

  :deep(p) {
    margin-bottom: $spacing-md;
  }

  :deep(ul),
  :deep(ol) {
    padding-left: $spacing-lg;
    margin-bottom: $spacing-md;
  }

  :deep(code) {
    background: $bg-input;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: $font-size-sm;
  }

  :deep(pre) {
    background: $bg-input;
    padding: $spacing-md;
    border-radius: $radius-md;
    overflow-x: auto;
    margin-bottom: $spacing-md;
  }
}

@media (max-width: 640px) {
  .input-row {
    flex-direction: column;
  }

  .preview-content {
    flex-direction: column;
  }

  .preview-thumb {
    width: 100%;
    height: auto;
    aspect-ratio: 16 / 9;
  }
}
</style>
