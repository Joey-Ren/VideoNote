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
        :disabled="!videoUrl || isPrepared || isPreparing"
        @click="handlePrepare"
      >
        {{ isPreparing ? '预处理中...' : isPrepared ? '✓ 已就绪' : '预处理视频' }}
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
import { ref, nextTick } from 'vue'
import { startTranscription, getTranscriptionResult } from '@/api'
import type { QAMessage } from '@/types'

const videoUrl = ref('')
const question = ref('')
const isPrepared = ref(false)
const isPreparing = ref(false)
const isAsking = ref(false)
const transcriptionContext = ref('')
const messages = ref<QAMessage[]>([])
const chatContainer = ref<HTMLElement>()

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

async function handlePrepare() {
  if (!videoUrl.value || isPreparing.value) return
  isPreparing.value = true

  try {
    const resp = await startTranscription(videoUrl.value)

    await new Promise<void>((resolve, reject) => {
      const es = new EventSource(`/api/transcribe/progress/${resp.task_id}`)
      es.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.status === 'completed') { es.close(); resolve() }
        if (data.status === 'error') { es.close(); reject(new Error(data.message)) }
      }
      es.onerror = () => { es.close(); reject(new Error('连接中断')) }
    })

    const result = await getTranscriptionResult(resp.task_id)
    transcriptionContext.value = result.text
    isPrepared.value = true
  } catch {
    messages.value.push({
      role: 'assistant',
      content: '预处理失败，请检查视频链接后重试。',
      timestamp: Date.now(),
    })
  } finally {
    isPreparing.value = false
  }
}

async function handleAsk() {
  if (!question.value || isAsking.value) return
  const q = question.value
  question.value = ''
  isAsking.value = true

  messages.value.push({ role: 'user', content: q, timestamp: Date.now() })
  scrollToBottom()

  messages.value.push({ role: 'assistant', content: '', timestamp: Date.now() })
  const assistantIdx = messages.value.length - 1

  try {
    const resp = await fetch('/api/qa/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        video_url: videoUrl.value,
        question: q,
        context: transcriptionContext.value,
      }),
    })

    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    if (!resp.body) throw new Error('无响应')

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const text = decoder.decode(value)
      const lines = text.split('\n')
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.content) {
              messages.value[assistantIdx] = {
                ...messages.value[assistantIdx],
                content: messages.value[assistantIdx].content + data.content,
              }
              scrollToBottom()
            }
          } catch {
            // skip
          }
        }
      }
    }
  } catch {
    messages.value[assistantIdx] = {
      ...messages.value[assistantIdx],
      content: '回答失败，请重试。',
    }
  } finally {
    isAsking.value = false
    scrollToBottom()
  }
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
