<template>
  <div class="page">
    <h1 class="page-title">视频下载</h1>
    <p class="page-desc">下载 YouTube / B站 视频到本地</p>

    <!-- 输入区域 -->
    <div class="card input-section">
      <div class="input-row">
        <input
          v-model="videoUrl"
          class="input"
          placeholder="粘贴视频链接..."
          @keydown.enter="handlePreview"
        />
        <button class="btn-primary" :disabled="!videoUrl" @click="handlePreview">
          预览
        </button>
      </div>
    </div>

    <!-- 下载选项 -->
    <div v-if="videoTitle" class="card options-section">
      <h3 class="section-title">{{ videoTitle }}</h3>
      <div class="options-grid">
        <div class="option-group">
          <label class="option-label">格式</label>
          <select v-model="format" class="input">
            <option value="mp4">MP4 (视频)</option>
            <option value="mp3">MP3 (仅音频)</option>
            <option value="webm">WebM</option>
          </select>
        </div>
        <div class="option-group">
          <label class="option-label">画质</label>
          <select v-model="quality" class="input">
            <option value="best">最佳画质</option>
            <option value="1080p">1080p</option>
            <option value="720p">720p</option>
            <option value="480p">480p</option>
          </select>
        </div>
      </div>
      <button
        class="btn-primary"
        style="margin-top: 16px"
        :disabled="downloading"
        @click="handleDownload"
      >
        {{ downloading ? '下载中...' : downloadDone ? '✓ 下载完成' : '开始下载' }}
      </button>
    </div>

    <!-- 下载进度 -->
    <div v-if="downloading" class="card progress-section">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progress + '%' }" />
      </div>
      <p class="progress-text">{{ progressMsg }}</p>
    </div>

    <div v-if="errorMsg" class="card" style="border-color: #ef4444; color: #ef4444;">
      <p>{{ errorMsg }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { previewVideo, startDownload } from '@/api'

const videoUrl = ref('')
const videoTitle = ref('')
const format = ref('mp4')
const quality = ref('best')
const downloading = ref(false)
const downloadDone = ref(false)
const progress = ref(0)
const progressMsg = ref('')
const errorMsg = ref('')

async function handlePreview() {
  if (!videoUrl.value) return
  errorMsg.value = ''
  videoTitle.value = ''
  downloadDone.value = false
  try {
    const info = await previewVideo(videoUrl.value)
    videoTitle.value = info.title
  } catch {
    errorMsg.value = '预览失败，请检查链接'
  }
}

async function handleDownload() {
  if (!videoUrl.value || downloading.value) return
  downloading.value = true
  downloadDone.value = false
  progress.value = 0
  progressMsg.value = '准备下载...'
  errorMsg.value = ''

  try {
    const resp = await startDownload(videoUrl.value, format.value, quality.value)

    await new Promise<void>((resolve, reject) => {
      const es = new EventSource(`/api/download/progress/${resp.task_id}`)
      es.onmessage = (event) => {
        const data = JSON.parse(event.data)
        progress.value = data.progress
        progressMsg.value = data.message
        if (data.status === 'completed') {
          es.close()
          resolve()
        }
        if (data.status === 'error') {
          es.close()
          reject(new Error(data.message))
        }
      }
      es.onerror = () => { es.close(); reject(new Error('连接中断')) }
    })

    downloadDone.value = true
    progressMsg.value = '下载完成！文件已保存到服务器 temp 目录'
  } catch (e: unknown) {
    errorMsg.value = e instanceof Error ? e.message : '下载失败'
  } finally {
    downloading.value = false
  }
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

.options-section {
  margin-bottom: $spacing-lg;
}

.section-title {
  font-size: $font-size-md;
  font-weight: 600;
  margin-bottom: $spacing-lg;
}

.options-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $spacing-lg;
}

.option-group {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
}

.option-label {
  font-size: $font-size-sm;
  color: $text-secondary;
  font-weight: 500;
}

select.input {
  cursor: pointer;
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
  transition: width 0.3s ease;
}

.progress-text {
  color: $text-secondary;
  font-size: $font-size-sm;
}

@media (max-width: 640px) {
  .input-row {
    flex-direction: column;
  }

  .options-grid {
    grid-template-columns: 1fr;
  }
}
</style>
