<template>
  <el-card class="chat-window">
    <template #header>
      <div class="chat-header">
        <div>
          <b>AI 求职 Agent</b>
          <span>多轮对话 · 上下文记忆</span>
        </div>
        <div class="chat-actions">
          <el-select
            v-if="conversations?.length"
            :model-value="conversationId"
            size="small"
            placeholder="历史对话"
            style="width: 220px"
            @change="$emit('selectConversation', $event)"
          >
            <el-option
              v-for="item in conversations"
              :key="item.id"
              :label="item.title"
              :value="item.id"
            />
          </el-select>
          <el-button size="small" @click="$emit('newConversation')">新建对话</el-button>
        </div>
      </div>
    </template>
    <div class="messages">
      <ChatMessage v-for="(item,index) in messages" :key="index" :message="item" />
      <el-empty v-if="!messages.length" description="开始和 Agent 聊聊你的简历、JD 或项目经历" />
    </div>
    <ChatInput
      :loading="loading"
      @upload="$emit('upload', $event)"
      @send="$emit('send', $event)"
    />
  </el-card>
</template>
<script setup lang="ts">
import ChatInput from '@/components/chat/ChatInput.vue'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import type { Conversation } from '@/api/conversation'
import type { ChatMessage as Message } from '@/types/domain'
defineProps<{
  messages: Message[]
  loading?: boolean
  conversations?: Conversation[]
  conversationId?: string
}>()
defineEmits<{
  send: [content: string]
  upload: [file: File]
  newConversation: []
  selectConversation: [id: string]
}>()
</script>
<style scoped>
.chat-window {
  height: calc(100vh - 132px);
  display: flex;
  flex-direction: column;
}

.chat-window :deep(.el-card__body) {
  min-height: 0;
  display: flex;
  flex: 1;
  flex-direction: column;
}

.chat-window span {
  margin-left: 8px;
  color: var(--color-muted);
  font-size: 13px;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.messages {
  flex: 1;
  overflow: auto;
  padding-right: 6px;
}
</style>
