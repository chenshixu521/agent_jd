import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/utils/token'

const MainLayout = () => import('@/layouts/MainLayout.vue')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/views/auth/Login.vue'), meta: { public: true } },
    { path: '/register', component: () => import('@/views/auth/Register.vue'), meta: { public: true } },
    {
      path: '/',
      component: MainLayout,
      children: [
        { path: '', name: 'dashboard', component: () => import('@/views/dashboard/Dashboard.vue') },
        { path: 'resume', name: 'resume', component: () => import('@/views/resume/ResumeUpload.vue') },
        { path: 'jd', name: 'jd', component: () => import('@/views/jd/JdUpload.vue') },
        { path: 'analysis', name: 'analysis', component: () => import('@/views/analysis/AiAnalysis.vue') },
        { path: 'rewrite', name: 'rewrite', component: () => import('@/views/rewrite/ProjectRewrite.vue') },
        { path: 'match', name: 'match', component: () => import('@/views/match/MatchReport.vue') }
      ]
    }
  ]
})

router.beforeEach((to) => {
  if (!to.meta.public && !getToken()) return '/login'
  if (to.meta.public && getToken() && to.path === '/login') return '/'
})

export default router
