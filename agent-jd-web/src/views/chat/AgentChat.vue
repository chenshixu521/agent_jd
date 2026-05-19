<template>
  <div class="chat-page fade-in">
    <div class="chat-shell">
      <ChatWindow :messages="chat.messages" :loading="chat.loading" @send="chat.send" />
    </div>
  </div>
</template>
<script setup lang="ts">
import ChatWindow from '@/components/chat/ChatWindow.vue'
import { useChatStore } from '@/stores/chat'
const chat=useChatStore()
</script>
<style scoped>
.chat-page {
  min-height: calc(100vh - 124px);
  display: grid;
  place-items: center;
  padding: 8px 0;
}

.chat-shell {
  width: min(920px, 100%);
  height: calc(100vh - 132px);
}

.chat-shell :deep(.chat-window) {
  height: 100%;
  border: 1px solid rgba(148, 163, 184, .24);
  box-shadow: 0 22px 70px rgba(15, 23, 42, .12);
}
</style>
