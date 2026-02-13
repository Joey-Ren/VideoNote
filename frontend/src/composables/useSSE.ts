import { ref, onUnmounted } from 'vue'
import type { ProgressEvent } from '@/types'

/**
 * SSE (Server-Sent Events) composable
 * 用于实时接收后端推送的进度信息
 */
export function useSSE() {
  const progress = ref(0)
  const message = ref('')
  const status = ref<'idle' | 'processing' | 'completed' | 'error'>('idle')
  const isConnected = ref(false)

  let eventSource: EventSource | null = null

  /**
   * 连接 SSE 端点
   * @param url SSE 端点地址
   * @param onData 收到数据时的回调
   */
  function connect(url: string, onData?: (event: ProgressEvent) => void) {
    disconnect()

    eventSource = new EventSource(url)
    isConnected.value = true
    status.value = 'processing'

    eventSource.onmessage = (event) => {
      try {
        const data: ProgressEvent = JSON.parse(event.data)
        progress.value = data.progress
        message.value = data.message
        status.value = data.status

        onData?.(data)

        if (data.status === 'completed' || data.status === 'error') {
          disconnect()
        }
      } catch {
        // 非 JSON 数据，当作纯文本消息处理
        message.value = event.data
      }
    }

    eventSource.onerror = () => {
      status.value = 'error'
      message.value = '连接中断'
      disconnect()
    }
  }

  /** 断开 SSE 连接 */
  function disconnect() {
    if (eventSource) {
      eventSource.close()
      eventSource = null
      isConnected.value = false
    }
  }

  /** 重置状态 */
  function reset() {
    disconnect()
    progress.value = 0
    message.value = ''
    status.value = 'idle'
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    progress,
    message,
    status,
    isConnected,
    connect,
    disconnect,
    reset,
  }
}
