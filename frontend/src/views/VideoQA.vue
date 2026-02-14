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
          :class="{
            'voice-btn--active': isListening,
            'voice-btn--chat-mode': voiceChatMode,
          }"
          :disabled="!isPrepared"
          :title="voiceChatMode ? (isSpeaking ? '打断并说话' : '结束语音对话') : '开始语音对话'"
          @click="toggleVoiceChat"
        >
          <span class="voice-icon">{{ !voiceChatMode ? '🎤' : (isSpeaking ? '🎤' : '⏹') }}</span>
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
      <div v-if="voiceChatMode || voiceStatus" class="voice-status">
        <span v-if="voiceChatMode && !voiceStatus" class="voice-mode-label">语音对话中 · 点🎤打断 · 说"结束"退出</span>
        <span v-else>{{ voiceStatus }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onBeforeUnmount } from 'vue'
import {
  startTranscription,
  getTranscriptionResult,
  synthesizeSpeech,
  transcribeAudio,
} from '@/api'
import type { QAMessage } from '@/types'

const videoUrl = ref('')
const question = ref('')
const isPrepared = ref(false)
const isPreparing = ref(false)
const isAsking = ref(false)
const isListening = ref(false)
const isSpeaking = ref(false)
const voiceStatus = ref('')
const voiceChatMode = ref(false)
const transcriptionContext = ref('')
const messages = ref<QAMessage[]>([])
const chatContainer = ref<HTMLElement>()

let mediaRecorder: MediaRecorder | null = null
let audioChunks: Blob[] = []
let currentAudio: HTMLAudioElement | null = null
let audioContext: AudioContext | null = null
let silenceCheckId = 0
let speakResolve: (() => void) | null = null
let vadStream: MediaStream | null = null
let vadContext: AudioContext | null = null
let vadCheckId = 0
let interrupted = false
let ttsPlaying = false
let sseAbortController: AbortController | null = null

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

// ========== 录音 + SenseVoice STT ==========

const SILENCE_THRESHOLD = 15
const SILENCE_DURATION = 2000

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
    audioChunks = []

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data)
    }

    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop())
      cleanupAudioContext()

      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
      if (audioBlob.size < 1000) {
        if (voiceChatMode.value) {
          setTimeout(() => startListening(), 1000)
        }
        return
      }

      voiceStatus.value = '识别中...'
      isListening.value = false

      try {
        const text = await transcribeAudio(audioBlob)
        if (!text.trim()) {
          voiceStatus.value = '未检测到语音'
          setTimeout(() => { voiceStatus.value = '' }, 2000)
          if (voiceChatMode.value) {
            setTimeout(() => startListening(), 1500)
          }
          return
        }

        const exitKeywords = ['结束对话', '退出', '结束']
        if (exitKeywords.some((kw) => text.includes(kw))) {
          exitVoiceChat()
          return
        }

        question.value = text
        voiceStatus.value = ''
        handleAsk()
      } catch {
        voiceStatus.value = '识别失败，请重试'
        setTimeout(() => { voiceStatus.value = '' }, 2000)
        if (voiceChatMode.value) {
          setTimeout(() => startListening(), 2000)
        }
      }
    }

    mediaRecorder.start()
    setupSilenceDetection(stream)
  } catch {
    voiceStatus.value = '麦克风权限被拒绝'
    isListening.value = false
    voiceChatMode.value = false
    setTimeout(() => { voiceStatus.value = '' }, 3000)
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop()
  }
}

function setupSilenceDetection(stream: MediaStream) {
  audioContext = new AudioContext()
  const analyser = audioContext.createAnalyser()
  const source = audioContext.createMediaStreamSource(stream)
  source.connect(analyser)
  analyser.fftSize = 512

  const dataArray = new Uint8Array(analyser.frequencyBinCount)
  let lastSoundTime = Date.now()
  const checkId = ++silenceCheckId

  const checkSilence = () => {
    if (checkId !== silenceCheckId || !isListening.value) return
    analyser.getByteFrequencyData(dataArray)
    const volume = dataArray.reduce((a, b) => a + b, 0) / dataArray.length

    if (volume > SILENCE_THRESHOLD) {
      lastSoundTime = Date.now()
    } else if (Date.now() - lastSoundTime > SILENCE_DURATION) {
      stopRecording()
      return
    }

    requestAnimationFrame(checkSilence)
  }

  setTimeout(checkSilence, 500)
}

function cleanupAudioContext() {
  silenceCheckId++
  if (audioContext) {
    audioContext.close().catch(() => {})
    audioContext = null
  }
}

// ========== TTS 预合成 + 播放队列 ==========

let audioQueue: Promise<Blob | null>[] = []

function enqueueTTS(sentence: string) {
  if (interrupted) return
  const blobPromise = synthesizeSpeech(sentence).catch(() => null)
  audioQueue.push(blobPromise)
  if (!ttsPlaying) {
    playNextInQueue()
  }
}

async function playNextInQueue() {
  if (interrupted || audioQueue.length === 0) {
    ttsPlaying = false
    if (!interrupted && voiceChatMode.value && !isAsking.value) {
      stopVAD()
      startListening()
    }
    return
  }

  ttsPlaying = true
  const blobPromise = audioQueue.shift()!
  const blob = await blobPromise

  if (interrupted || !blob) {
    playNextInQueue()
    return
  }

  await playBlob(blob)

  if (!interrupted) {
    playNextInQueue()
  }
}

function interruptAll() {
  interrupted = true
  audioQueue = []
  ttsPlaying = false
  if (sseAbortController) {
    sseAbortController.abort()
    sseAbortController = null
  }
  stopSpeak()
}

async function playBlob(blob: Blob): Promise<void> {
  const url = URL.createObjectURL(blob)
  currentAudio = new Audio(url)
  voiceStatus.value = '🔊 正在播放...'
  isSpeaking.value = true

  return new Promise<void>((resolve) => {
    speakResolve = resolve

    const cleanup = () => {
      isSpeaking.value = false
      URL.revokeObjectURL(url)
      if (!ttsPlaying) voiceStatus.value = ''
      currentAudio = null
      speakResolve = null
      resolve()
    }

    currentAudio!.onended = () => cleanup()
    currentAudio!.onerror = () => cleanup()

    currentAudio!.play().then(() => {
      if (voiceChatMode.value && !interrupted) {
        startVAD()
      }
    }).catch(() => cleanup())
  })
}

async function speak(text: string): Promise<void> {
  if (interrupted) return
  try {
    const blob = await synthesizeSpeech(text)
    if (interrupted) return
    await playBlob(blob)
  } catch {
    isSpeaking.value = false
    voiceStatus.value = ''
    speakResolve = null
  }
}

function stopSpeak() {
  stopVAD()
  if (currentAudio) {
    currentAudio.onended = null
    currentAudio.onerror = null
    currentAudio.pause()
    currentAudio.src = ''
    currentAudio = null
  }
  isSpeaking.value = false
  if (speakResolve) {
    speakResolve()
    speakResolve = null
  }
}

const VAD_THRESHOLD = 30
const VAD_CONFIRM_MS = 300
async function startVAD() {
  try {
    vadStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    vadContext = new AudioContext()
    const analyser = vadContext.createAnalyser()
    const source = vadContext.createMediaStreamSource(vadStream)
    source.connect(analyser)
    analyser.fftSize = 512

    const dataArray = new Uint8Array(analyser.frequencyBinCount)
    let voiceStartTime = 0
    const checkId = ++vadCheckId

    const detectVoice = () => {
      if (checkId !== vadCheckId || !isSpeaking.value) return
      analyser.getByteFrequencyData(dataArray)
      const volume = dataArray.reduce((a, b) => a + b, 0) / dataArray.length

      if (volume > VAD_THRESHOLD) {
        if (voiceStartTime === 0) voiceStartTime = Date.now()
        if (Date.now() - voiceStartTime > VAD_CONFIRM_MS) {
          interruptAll()
          startListening()
          return
        }
      } else {
        voiceStartTime = 0
      }

      requestAnimationFrame(detectVoice)
    }

    requestAnimationFrame(detectVoice)
  } catch {
    // 麦克风不可用，降级为手动打断
  }
}

function stopVAD() {
  vadCheckId++
  if (vadStream) {
    vadStream.getTracks().forEach((t) => t.stop())
    vadStream = null
  }
  if (vadContext) {
    vadContext.close().catch(() => {})
    vadContext = null
  }
}

function toggleSpeak(text: string) {
  if (isSpeaking.value || ttsPlaying) {
    interruptAll()
  } else {
    interrupted = false
    speak(text)
  }
}

// ========== 连续对话模式 ==========

function startListening() {
  if (!voiceChatMode.value) return
  isListening.value = true
  voiceStatus.value = '🎤 正在聆听...'
  startRecording()
}

function toggleVoiceChat() {
  if (voiceChatMode.value) {
    if (isSpeaking.value || isAsking.value) {
      interruptAll()
      startListening()
    } else {
      exitVoiceChat()
    }
  } else {
    enterVoiceChat()
  }
}

function enterVoiceChat() {
  voiceChatMode.value = true
  startListening()
}

function exitVoiceChat() {
  voiceChatMode.value = false
  isListening.value = false
  voiceStatus.value = ''
  interruptAll()
  stopRecording()
  cleanupAudioContext()
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

const SENTENCE_DELIMITERS = /([。！？\n.!?])/

async function handleAsk() {
  if (!question.value || isAsking.value) return
  const q = question.value
  question.value = ''
  isAsking.value = true
  interruptAll()
  interrupted = false

  if (voiceChatMode.value) {
    voiceStatus.value = '🤖 AI 思考中...'
  }

  messages.value.push({ role: 'user', content: q, timestamp: Date.now() })
  scrollToBottom()

  messages.value.push({ role: 'assistant', content: '', timestamp: Date.now() })
  const assistantMsg = messages.value[messages.value.length - 1] as QAMessage

  let sentenceBuffer = ''

  try {
    sseAbortController = new AbortController()
    const resp = await fetch('/api/qa/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        video_url: videoUrl.value,
        question: q,
        context: transcriptionContext.value,
      }),
      signal: sseAbortController.signal,
    })

    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    if (!resp.body) throw new Error('无响应')

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      if (interrupted) break
      const { done, value } = await reader.read()
      if (done) break

      const text = decoder.decode(value)
      const lines = text.split('\n')
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.content) {
              assistantMsg.content += data.content
              scrollToBottom()

              if (voiceChatMode.value && !interrupted) {
                sentenceBuffer += data.content
                const parts = sentenceBuffer.split(SENTENCE_DELIMITERS)
                while (parts.length >= 3) {
                  const sentence = parts.shift()! + parts.shift()!
                  if (sentence.trim()) {
                    enqueueTTS(sentence.trim())
                  }
                }
                sentenceBuffer = parts.join('')
              }
            }
          } catch {
            // skip malformed SSE
          }
        }
      }
    }

    sseAbortController = null

    if (!interrupted && voiceChatMode.value && sentenceBuffer.trim()) {
      enqueueTTS(sentenceBuffer.trim())
    }

    if (!interrupted && !voiceChatMode.value && assistantMsg.content) {
      speak(assistantMsg.content)
    }
  } catch (e) {
    if (!interrupted) {
      assistantMsg.content = assistantMsg.content || '回答失败，请重试。'
      if (voiceChatMode.value) {
        setTimeout(() => startListening(), 2000)
      }
    }
  } finally {
    isAsking.value = false
    sseAbortController = null
    scrollToBottom()
  }
}

onBeforeUnmount(() => {
  exitVoiceChat()
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
  transition: all $transition-base;

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

  &--chat-mode {
    width: 56px;
    min-width: 56px;
    height: 56px;
    background: $accent-primary;
    border-color: $accent-primary;

    .voice-icon {
      font-size: 22px;
      color: white;
    }

    &:hover:not(:disabled) {
      background: $accent-hover;
      border-color: $accent-hover;
    }
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

  .voice-btn--chat-mode & {
    border-color: $accent-primary;
  }
}

.voice-status {
  padding-top: $spacing-sm;
  font-size: $font-size-xs;
  color: $text-muted;
  text-align: center;
}

.voice-mode-label {
  color: $accent-primary;
  font-weight: 500;
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
