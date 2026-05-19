import { defineStore } from 'pinia'
import { loginApi, meApi, registerApi, type LoginPayload, type RegisterPayload } from '@/api/auth'
import type { UserInfo } from '@/types/domain'
import { clearToken, getStoredUser, getToken, setStoredUser, setToken } from '@/utils/token'

export const useAuthStore = defineStore('auth', {
  state: () => ({ token: getToken(), user: getStoredUser<UserInfo>(), loading: false }),
  getters: { isLogin: (state) => Boolean(state.token) },
  actions: {
    async login(payload: LoginPayload) {
      this.loading = true
      try {
        const result = await loginApi(payload)
        this.token = result.accessToken
        this.user = result.user
        setToken(result.accessToken)
        setStoredUser(result.user)
      } finally { this.loading = false }
    },
    async register(payload: RegisterPayload) {
      const result = await registerApi(payload)
      this.token = result.accessToken
      this.user = result.user
      setToken(result.accessToken)
      setStoredUser(result.user)
    },
    async fetchMe() {
      if (!this.token) return
      this.user = await meApi()
      setStoredUser(this.user)
    },
    logout() {
      this.token = ''
      this.user = null
      clearToken()
    }
  }
})
