<template>
  <div class="dashboard-home fade-in">
    <div class="home-chat">
      <ChatWindow
        :messages="chat.messages"
        :loading="chat.loading"
        :conversations="chat.conversations"
        :conversation-id="chat.conversationId"
        @new-conversation="chat.newConversation"
        @select-conversation="chat.selectConversation"
        @upload="chat.uploadAndAnalyze"
        @send="chat.send"
      />
    </div>
  </div>
</template>
<script setup lang="ts">
import { onMounted } from 'vue'
import ChatWindow from '@/components/chat/ChatWindow.vue'
import { useChatStore } from '@/stores/chat'
import { useJdStore } from '@/stores/jd'
import { useResumeStore } from '@/stores/resume'
import { useTaskStore } from '@/stores/task'

const resume = useResumeStore()
const jd = useJdStore()
const task = useTaskStore()
const chat = useChatStore()

onMounted(() => {
  resume.load()
  jd.load()
  task.load()
  chat.loadHistory()
})
</script>
<style scoped>
.dashboard-home {
  position: absolute;
  inset: 0;
  display: flex;
  background: var(--color-bg);
}

.home-chat {
  width: 100%;
  height: 100%;
}

.home-chat :deep(.chat-window) {
  height: 100%;
  border: 0;
  border-radius: 0;
  box-shadow: none;
}

.home-chat :deep(.chat-window .el-card__body) {
  padding: 18px 24px;
}
</style>
