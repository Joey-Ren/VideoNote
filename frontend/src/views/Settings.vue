<template>
  <div class="page">
    <h1 class="page-title">设置</h1>
    <p class="page-desc">配置 AI 模型和 API 密钥</p>

    <!-- OpenAI 配置 -->
    <div class="card settings-section">
      <h3 class="section-title">OpenAI 配置</h3>
      <div class="form-group">
        <label class="form-label">API Key</label>
        <input
          v-model="settings.openaiApiKey"
          class="input"
          type="password"
          placeholder="sk-..."
        />
      </div>
      <div class="form-group">
        <label class="form-label">API Base URL</label>
        <input
          v-model="settings.openaiBaseUrl"
          class="input"
          placeholder="https://api.openai.com/v1"
        />
      </div>
      <div class="form-group">
        <label class="form-label">模型</label>
        <div class="model-input-wrapper">
          <input
            v-model="settings.openaiModel"
            class="input"
            placeholder="输入模型名称，如 gpt-4o"
            list="model-suggestions"
          />
          <datalist id="model-suggestions">
            <option value="gpt-4o" />
            <option value="gpt-4o-mini" />
            <option value="gpt-4.1" />
            <option value="gpt-3.5-turbo" />
            <option value="claude-3-opus-20240229" />
            <option value="claude-3.5-sonnet-20241022" />
            <option value="deepseek-chat" />
            <option value="qwen-plus" />
          </datalist>
        </div>
        <p class="form-hint">可直接输入任意模型名称，也可从下拉建议中选择</p>
      </div>
    </div>

    <!-- Whisper 配置 -->
    <div class="card settings-section">
      <h3 class="section-title">Whisper 转录配置</h3>
      <div class="form-group">
        <label class="form-label">模型大小</label>
        <select v-model="settings.whisperModel" class="input">
          <option value="tiny">Tiny (最快，质量一般)</option>
          <option value="base">Base (推荐，平衡)</option>
          <option value="small">Small (较好质量)</option>
          <option value="medium">Medium (高质量)</option>
          <option value="large-v3">Large-v3 (最高质量，需要 GPU)</option>
        </select>
      </div>
    </div>

    <!-- YouTube 配置 -->
    <div class="card settings-section">
      <h3 class="section-title">YouTube API（可选）</h3>
      <div class="form-group">
        <label class="form-label">YouTube API Key</label>
        <input
          v-model="settings.youtubeApiKey"
          class="input"
          type="password"
          placeholder="配置后可加速 YouTube 视频预览"
        />
        <p class="form-hint">不配置也能用，只是预览速度稍慢</p>
      </div>
    </div>

    <button class="btn-primary" @click="handleSave">保存设置</button>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'

const settings = reactive({
  openaiApiKey: '',
  openaiBaseUrl: 'https://api.openai.com/v1',
  openaiModel: 'gpt-4o',
  whisperModel: 'base',
  youtubeApiKey: '',
})

function handleSave() {
  // TODO: 保存到后端 / localStorage
  localStorage.setItem('videonote-settings', JSON.stringify(settings))
  alert('设置已保存')
}

// 初始化加载
const saved = localStorage.getItem('videonote-settings')
if (saved) {
  try {
    Object.assign(settings, JSON.parse(saved))
  } catch {
    // ignore
  }
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.settings-section {
  margin-bottom: $spacing-lg;
}

.section-title {
  font-size: $font-size-md;
  font-weight: 600;
  margin-bottom: $spacing-lg;
}

.form-group {
  margin-bottom: $spacing-lg;

  &:last-child {
    margin-bottom: 0;
  }
}

.form-label {
  display: block;
  font-size: $font-size-sm;
  font-weight: 500;
  color: $text-secondary;
  margin-bottom: $spacing-sm;
}

.form-hint {
  margin-top: $spacing-xs;
  font-size: $font-size-xs;
  color: $text-muted;
}

select.input {
  cursor: pointer;
}
</style>
