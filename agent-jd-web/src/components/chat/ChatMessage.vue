<template>
  <div class="message" :class="message.role">
    <div class="avatar">{{ message.role === 'user' ? '我' : 'AI' }}</div>
    <div class="bubble">
      <MarkdownView :content="message.content" />
    </div>
  </div>
</template>
<script setup lang="ts">
import MarkdownView from '@/components/common/MarkdownView.vue'
import type { ChatMessage } from '@/types/domain'
defineProps<{ message: ChatMessage }>()
</script>
<style scoped>
.message {
  display: flex;
  gap: 10px;
  margin: 14px 0;
}

.message.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: #e0e7ff;
  color: #3730a3;
  font-weight: 700;
}

.bubble {
  max-width: 76%;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: white;
}

.user .bubble {
  border: 0;
  background: #2563eb;
  color: white;
}

:deep(.user .markdown-body) {
  color: white;
}
</style>
