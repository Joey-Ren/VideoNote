import axios from 'axios'
import type {
  VideoInfo,
  TranscriptionResult,
  NoteResult,
  TaskResponse,
} from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

/** 视频预览 — 获取视频信息 */
export async function previewVideo(url: string): Promise<VideoInfo> {
  const { data } = await api.post('/video/preview', { url })
  return data
}

/** 开始转录 */
export async function startTranscription(
  url?: string,
  localPath?: string,
): Promise<TaskResponse> {
  const { data } = await api.post('/transcribe/start', {
    url,
    local_path: localPath,
  })
  return data
}

/** 获取转录结果 */
export async function getTranscriptionResult(
  taskId: string,
): Promise<TranscriptionResult> {
  const { data } = await api.get(`/transcribe/result/${taskId}`)
  return data
}

/** 生成笔记 */
export async function generateNote(
  transcriptionText: string,
  language: string = 'zh',
): Promise<TaskResponse> {
  const { data } = await api.post('/note/generate', {
    transcription_text: transcriptionText,
    language,
  })
  return data
}

/** 获取笔记结果 */
export async function getNoteResult(taskId: string): Promise<NoteResult> {
  const { data } = await api.get(`/note/result/${taskId}`)
  return data
}

/** 视频问答 */
export async function askQuestion(
  videoUrl: string,
  question: string,
  context?: string,
): Promise<TaskResponse> {
  const { data } = await api.post('/qa/ask', {
    video_url: videoUrl,
    question,
    context,
  })
  return data
}

/** 开始下载 */
export async function startDownload(
  url: string,
  format: string = 'mp4',
  quality: string = 'best',
): Promise<TaskResponse> {
  const { data } = await api.post('/download/start', {
    url,
    format,
    quality,
  })
  return data
}

/** TTS 语音合成 — 返回 mp3 Blob */
export async function synthesizeSpeech(
  text: string,
  speed?: number,
): Promise<Blob> {
  const { data } = await api.post('/tts/speak', { text, speed }, {
    responseType: 'blob',
    timeout: 60000,
  })
  return data
}

/** STT 语音识别 — 发送音频，返回文本 */
export async function transcribeAudio(audioBlob: Blob): Promise<string> {
  const formData = new FormData()
  formData.append('file', audioBlob, 'audio.webm')
  const { data } = await api.post('/stt/transcribe', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 30000,
  })
  return data.text
}

export default api
