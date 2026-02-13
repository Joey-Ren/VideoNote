import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  /** 当前是否有任务在处理 */
  const isProcessing = ref(false)

  /** 全局提示消息 */
  const message = ref('')
  const messageType = ref<'info' | 'success' | 'error'>('info')

  function showMessage(msg: string, type: 'info' | 'success' | 'error' = 'info') {
    message.value = msg
    messageType.value = type
    setTimeout(() => {
      message.value = ''
    }, 3000)
  }

  return {
    isProcessing,
    message,
    messageType,
    showMessage,
  }
})
