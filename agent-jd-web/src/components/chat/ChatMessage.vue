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
  overflow-wrap: anywhere;
}

.user .bubble {
  border: 0;
  background: #2563eb;
  color: white;
}

:deep(.user .markdown-body) {
  color: white;
}

@media (max-width: 640px) {
  .message {
    gap: 8px;
  }

  .avatar {
    width: 30px;
    height: 30px;
    flex: 0 0 30px;
    border-radius: 10px;
    font-size: 12px;
  }

  .bubble {
    max-width: calc(100% - 38px);
    padding: 10px 12px;
  }
}
</style>
