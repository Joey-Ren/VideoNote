<template>
  <div class="page">
    <h1 class="page-title">视频问答</h1>
    <p class="page-desc">基于视频内容的 AI 智能问答</p>

    <!-- 视频输入 -->
    <div class="card input-section">
      <input
        v-model="videoUrl"
        class="input"
        placeholder="粘贴视频链接，AI 将基于视频内容回答你的问题..."
      />
      <button
        class="btn-primary"
        style="margin-top: 12px"
        :disabled="!videoUrl || isPrepared"
        @click="handlePrepare"
      >
        {{ isPrepared ? '✓ 已就绪' : '预处理视频' }}
      </button>
    </div>

    <!-- 对话区域 -->
    <div class="card chat-section">
      <div class="chat-messages" ref="chatContainer">
        <div v-if="messages.length === 0" class="chat-empty">
          预处理视频后，在下方输入你的问题
        </div>
        <div
          v-for="(msg, i) in messages"
          :key="i"
          class="chat-message"
          :class="'chat-message--' + msg.role"
        >
          <div class="chat-bubble">{{ msg.content }}</div>
        </div>
      </div>
      <div class="chat-input">
        <input
          v-model="question"
          class="input"
          placeholder="输入你的问题..."
          :disabled="!isPrepared"
          @keydown.enter="handleAsk"
        />
        <button
          class="btn-primary"
          :disabled="!question || !isPrepared"
          @click="handleAsk"
        >
          发送
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { QAMessage } from '@/types'

const videoUrl = ref('')
const question = ref('')
const isPrepared = ref(false)
const messages = ref<QAMessage[]>([])

function handlePrepare() {
  // TODO: 调用预处理 API
  isPrepared.value = true
}

function handleAsk() {
  if (!question.value) return
  messages.value.push({
    role: 'user',
    content: question.value,
    timestamp: Date.now(),
  })
  // TODO: 调用问答 API，流式接收回答
  messages.value.push({
    role: 'assistant',
    content: '连接后端后将自动回答你的问题。',
    timestamp: Date.now(),
  })
  question.value = ''
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.input-section {
  margin-bottom: $spacing-lg;
}

.chat-section {
  display: flex;
  flex-direction: column;
  height: 500px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: $spacing-md 0;
}

.chat-empty {
  text-align: center;
  color: $text-muted;
  padding: $spacing-2xl;
}

.chat-message {
  display: flex;
  margin-bottom: $spacing-md;

  &--user {
    justify-content: flex-end;
  }

  &--assistant {
    justify-content: flex-start;
  }
}

.chat-bubble {
  max-width: 70%;
  padding: $spacing-sm $spacing-md;
  border-radius: $radius-lg;
  line-height: 1.6;

  .chat-message--user & {
    background: $accent-primary;
    color: white;
    border-bottom-right-radius: $spacing-xs;
  }

  .chat-message--assistant & {
    background: $bg-input;
    color: $text-primary;
    border-bottom-left-radius: $spacing-xs;
  }
}

.chat-input {
  display: flex;
  gap: $spacing-md;
  padding-top: $spacing-md;
  border-top: 1px solid $border-color;
}
</style>
