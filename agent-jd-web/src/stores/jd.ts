import { defineStore } from 'pinia'
import { createJdApi, listJdsApi, type JdCreatePayload } from '@/api/jd'
import type { Jd } from '@/types/domain'

export const useJdStore = defineStore('jd', {
  state: () => ({
    items: [] as Jd[],
    current: null as Jd | null,
    loading: false
  }),
  actions: {
    async load() {
      this.loading = true
      try {
        this.items = await listJdsApi()
        this.current ||= this.items[0] || null
      } finally {
        this.loading = false
      }
    },
    async create(payload: JdCreatePayload) {
      const item = await createJdApi(payload)
      this.items.unshift(item)
      this.current = item
      return item
    }
  }
})
