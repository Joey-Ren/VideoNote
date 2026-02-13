import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'video-note',
      component: () => import('@/views/VideoNote.vue'),
      meta: { title: '视频笔记' },
    },
    {
      path: '/qa',
      name: 'video-qa',
      component: () => import('@/views/VideoQA.vue'),
      meta: { title: '视频问答' },
    },
    {
      path: '/download',
      name: 'video-download',
      component: () => import('@/views/VideoDownload.vue'),
      meta: { title: '视频下载' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/Settings.vue'),
      meta: { title: '设置' },
    },
  ],
})

export default router
