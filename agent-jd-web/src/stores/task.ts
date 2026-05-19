import { defineStore } from 'pinia'
import { getTaskResultApi, listTasksApi, submitTaskApi, type TaskSubmitPayload } from '@/api/task'
import type { AiTask } from '@/types/domain'

export const useTaskStore = defineStore('task', {
  state: () => ({
    items: [] as AiTask[],
    latest: null as AiTask | null,
    loading: false
  }),
  actions: {
    async load() {
      this.items = await listTasksApi()
    },
    async submit(payload: TaskSubmitPayload) {
      this.loading = true
      try {
        const task = await submitTaskApi(payload)
        this.latest = task
        this.items.unshift(task)
        return task
      } finally {
        this.loading = false
      }
    },
    async refreshResult(taskUuid?: string) {
      const id = taskUuid || this.latest?.taskUuid
      if (!id) return null
      const task = await getTaskResultApi(id)
      this.latest = task
      const index = this.items.findIndex((item) => item.taskUuid === task.taskUuid)
      if (index >= 0) this.items[index] = task
      return task
    },
    async waitForResult(taskUuid?: string, maxAttempts = 120) {
      this.loading = true
      try {
        for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
          const task = await this.refreshResult(taskUuid)
          if (
            !task ||
            task.status === 2 ||
            task.status === 3 ||
            task.status === 4
          ) {
            return task
          }
          await new Promise((resolve) => window.setTimeout(resolve, 1500))
        }
        return this.latest
      } finally {
        this.loading = false
      }
    }
  }
})
