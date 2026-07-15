import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'TaskList',
      component: () => import('../views/TaskList.vue')
    },
    {
      path: '/tasks/new',
      name: 'TaskNew',
      component: () => import('../views/TaskNew.vue')
    },
    {
      path: '/tasks/:id',
      name: 'TaskDetail',
      component: () => import('../views/TaskDetail.vue')
    },
    {
      path: '/media',
      name: 'MediaLibrary',
      component: () => import('../views/MediaLibrary.vue')
    }
  ]
})

export default router
