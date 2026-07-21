<template>
  <el-header class="header">
    <div class="header-title">
      <b>AI 求职 Agent 工作台</b>
      <span>简历优化 / JD 分析 / 匹配推荐 / 多轮对话</span>
    </div>
    <div class="center-info">
      <el-tag type="success" effect="plain">DeepSeek Connected</el-tag>
      <el-tag effect="plain">Agent Online</el-tag>
      <span>智能求职全流程工作区</span>
    </div>
    <div class="user-area">
      <el-dropdown>
        <el-button round class="user-button">
          <span class="avatar">{{ avatarText }}</span>
          <span class="username">{{ auth.user?.username || '用户' }}</span>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </el-header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const avatarText = computed(() => (auth.user?.username || 'U').slice(0, 1).toUpperCase())

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.header {
  height: 76px;
  display: grid;
  grid-template-columns: 280px 1fr 220px;
  align-items: center;
  gap: 18px;
  border-bottom: 1px solid var(--border);
  background: rgba(255, 255, 255, .92);
  backdrop-filter: blur(18px);
}

.header-title span {
  display: block;
  margin-top: 4px;
  color: var(--color-muted);
  font-size: 13px;
}

.center-info {
  justify-self: center;
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--color-muted);
  font-size: 13px;
}

.user-area {
  justify-self: end;
  display: flex;
  align-items: center;
}

.user-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding-left: 8px;
}

.avatar {
  width: 28px;
  height: 28px;
  flex: 0 0 28px;
  display: inline-grid;
  place-items: center;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary), var(--color-ai));
  color: white;
  font-size: 12px;
  font-weight: 800;
}

.username {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 980px) {
  .header {
    grid-template-columns: 1fr auto;
  }

  .center-info {
    display: none;
  }

  .header-title span {
    display: none;
  }
}

@media (max-width: 640px) {
  .header {
    height: 64px;
    gap: 10px;
    padding: 0 12px;
  }

  .header-title {
    min-width: 0;
  }

  .header-title b {
    display: block;
    overflow: hidden;
    font-size: 14px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .user-button {
    max-width: 154px;
  }

  :deep(.user-button > span) {
    min-width: 0;
    max-width: 100%;
    overflow: hidden;
  }
}
</style>
