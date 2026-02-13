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
          <div class="chat-bubble">
            {{ msg.content }}
            <button
              v-if="msg.role === 'assistant' && msg.content"
              class="voice-play-btn"
              :title="isSpeaking ? '停止播放' : '语音播放'"
              @click="toggleSpeak(msg.content)"
            >
              {{ isSpeaking ? '⏹' : '🔊' }}
            </button>
          </div>
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
          class="voice-btn"
          :class="{ 'voice-btn--active': isListening }"
          :disabled="!isPrepared"
          :title="isListening ? '停止录音' : '语音输入'"
          @click="toggleVoice"
        >
          <span class="voice-icon">{{ isListening ? '⏹' : '🎤' }}</span>
          <span v-if="isListening" class="voice-pulse" />
        </button>
        <button
          class="btn-primary"
          :disabled="!question || !isPrepared"
          @click="handleAsk"
        >
          发送
        </button>
      </div>
      <div v-if="voiceStatus" class="voice-status">{{ voiceStatus }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onBeforeUnmount } from 'vue'
import { startTranscription, getTranscriptionResult } from '@/api'
import type { QAMessage } from '@/types'

const videoUrl = ref('')
const question = ref('')
const isPrepared = ref(false)
const isPreparing = ref(false)
const isAsking = ref(false)
const isListening = ref(false)
const isSpeaking = ref(false)
const voiceStatus = ref('')
const autoSpeak = ref(true)
const transcriptionContext = ref('')
const messages = ref<QAMessage[]>([])
const chatContainer = ref<HTMLElement>()

let recognition: SpeechRecognition | null = null
let speechUtterance: SpeechSynthesisUtterance | null = null

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

// ========== 语音输入 (STT) ==========

function initRecognition(): SpeechRecognition | null {
  const SpeechRecognition = window.SpeechRecognition || (window as any).webkitSpeechRecognition
  if (!SpeechRecognition) {
    voiceStatus.value = '当前浏览器不支持语音识别，请使用 Chrome'
    return null
  }

  const r = new SpeechRecognition()
  r.lang = 'zh-CN'
  r.continuous = false
  r.interimResults = true

  r.onresult = (event: SpeechRecognitionEvent) => {
    let transcript = ''
    for (let i = event.resultIndex; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript
    }
    question.value = transcript
    if (event.results[event.results.length - 1].isFinal) {
      voiceStatus.value = ''
      isListening.value = false
      if (question.value.trim()) {
        handleAsk()
      }
    }
  }

  r.onerror = (event: SpeechRecognitionErrorEvent) => {
    isListening.value = false
    if (event.error === 'no-speech') {
      voiceStatus.value = '未检测到语音，请重试'
    } else if (event.error === 'not-allowed') {
      voiceStatus.value = '麦克风权限被拒绝，请在浏览器设置中允许'
    } else {
      voiceStatus.value = `识别失败: ${event.error}`
    }
    setTimeout(() => { voiceStatus.value = '' }, 3000)
  }

  r.onend = () => {
    isListening.value = false
  }

  return r
}

function toggleVoice() {
  if (isListening.value) {
    recognition?.stop()
    isListening.value = false
    voiceStatus.value = ''
    return
  }

  if (!recognition) {
    recognition = initRecognition()
  }
  if (!recognition) return

  voiceStatus.value = '正在聆听...'
  isListening.value = true
  recognition.start()
}

// ========== 语音播报 (TTS) ==========

function speak(text: string) {
  stopSpeak()
  speechUtterance = new SpeechSynthesisUtterance(text)
  speechUtterance.lang = 'zh-CN'
  speechUtterance.rate = 1.1
  speechUtterance.onstart = () => { isSpeaking.value = true }
  speechUtterance.onend = () => { isSpeaking.value = false }
  speechUtterance.onerror = () => { isSpeaking.value = false }
  speechSynthesis.speak(speechUtterance)
}

function stopSpeak() {
  speechSynthesis.cancel()
  isSpeaking.value = false
}

function toggleSpeak(text: string) {
  if (isSpeaking.value) {
    stopSpeak()
  } else {
    speak(text)
  }
}

// ========== 预处理 ==========

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

// ========== 问答 ==========

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

    if (autoSpeak.value && messages.value[assistantIdx].content) {
      speak(messages.value[assistantIdx].content)
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

onBeforeUnmount(() => {
  recognition?.stop()
  stopSpeak()
})
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
  position: relative;

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

.voice-play-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  padding: 2px 4px;
  margin-left: 6px;
  opacity: 0.5;
  transition: opacity $transition-fast;
  vertical-align: middle;

  &:hover {
    opacity: 1;
  }
}

.chat-input {
  display: flex;
  gap: $spacing-md;
  padding-top: $spacing-md;
  border-top: 1px solid $border-color;
}

.voice-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  min-width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid $border-light;
  background: $bg-input;
  cursor: pointer;
  position: relative;
  transition: all $transition-fast;

  &:hover:not(:disabled) {
    border-color: $accent-primary;
    background: $bg-hover;
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  &--active {
    border-color: $error;
    background: rgba($error, 0.1);
    animation: voice-glow 1.5s ease-in-out infinite;
  }
}

.voice-icon {
  font-size: 18px;
  line-height: 1;
}

.voice-pulse {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 2px solid $error;
  animation: voice-ripple 1.5s ease-out infinite;
  pointer-events: none;
}

.voice-status {
  padding-top: $spacing-sm;
  font-size: $font-size-xs;
  color: $text-muted;
  text-align: center;
}

@keyframes voice-glow {
  0%, 100% { box-shadow: 0 0 0 0 rgba($error, 0.3); }
  50% { box-shadow: 0 0 12px 4px rgba($error, 0.2); }
}

@keyframes voice-ripple {
  0% { transform: scale(1); opacity: 0.6; }
  100% { transform: scale(1.4); opacity: 0; }
}
</style>
