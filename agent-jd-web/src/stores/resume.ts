import { defineStore } from 'pinia'
import { createResumeApi, deleteResumeApi, listResumesApi, type ResumeCreatePayload } from '@/api/resume'
import type { Resume } from '@/types/domain'

export const useResumeStore = defineStore('resume', {
  state: () => ({
    items: [] as Resume[],
    current: null as Resume | null,
    loading: false
  }),
  actions: {
    async load() {
      this.loading = true
      try {
        this.items = await listResumesApi()
        this.current ||= this.items[0] || null
      } finally {
        this.loading = false
      }
    },
    async create(payload: ResumeCreatePayload) {
      const item = await createResumeApi(payload)
      this.items.unshift(item)
      this.current = item
      return item
    },
    async remove(id: string) {
      await deleteResumeApi(id)
      this.items = this.items.filter((item) => item.id !== id)
      if (this.current?.id === id) this.current = this.items[0] || null
    }
  }
})
