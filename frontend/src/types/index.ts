/** 视频信息 */
export interface VideoInfo {
  title: string
  thumbnail: string | null
  duration: number // 秒
  platform: string
  url: string
}

/** 转录片段 */
export interface TranscriptionSegment {
  start: number
  end: number
  text: string
}

/** 转录结果 */
export interface TranscriptionResult {
  text: string
  segments: TranscriptionSegment[]
  language: string
  duration: number
}

/** 笔记结果 */
export interface NoteResult {
  markdown: string
  title: string
  outline: string[]
}

/** 问答消息 */
export interface QAMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

/** 下载选项 */
export interface DownloadOptions {
  format: string
  quality: string
}

/** 任务响应 */
export interface TaskResponse {
  task_id: string
  status: string
  message: string
}

/** SSE 进度事件 */
export interface ProgressEvent {
  progress: number
  message: string
  status: 'processing' | 'completed' | 'error'
}
