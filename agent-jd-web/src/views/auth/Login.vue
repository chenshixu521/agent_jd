<template>
  <div class="auth-page">
    <section class="auth-hero">
      <div class="brand-mark">AI</div>
      <h1>AI 求职 Agent</h1>
      <p>连接简历解析、JD 分析、项目改写和 DeepSeek 多轮对话，让求职准备更高效。</p>
      <div class="hero-tags">
        <el-tag effect="dark">简历自动解析</el-tag>
        <el-tag effect="dark" type="success">DeepSeek 已接入</el-tag>
        <el-tag effect="dark" type="warning">岗位匹配分析</el-tag>
      </div>
    </section>

    <el-card class="auth-card" shadow="always">
      <div class="card-title">
        <span>欢迎回来</span>
        <b>登录工作台</b>
      </div>
      <el-form :model="form" label-position="top" @submit.prevent>
        <el-form-item label="用户名">
          <el-input v-model="form.username" size="large" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            size="large"
            type="password"
            show-password
            placeholder="请输入密码"
          />
        </el-form-item>
        <el-button type="primary" size="large" :loading="auth.loading" @click="submit">进入平台</el-button>
        <p>
          没有账号？
          <router-link to="/register">立即注册</router-link>
        </p>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const form = reactive({ username: '', password: '' })

async function submit() {
  if (!form.username.trim() || !form.password.trim()) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  await auth.login(form)
  router.push('/')
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(420px, 1fr) 440px;
  gap: 56px;
  align-items: center;
  padding: 7vw;
  overflow: hidden;
  background:
    radial-gradient(circle at 20% 20%, rgba(59, 130, 246, .38), transparent 28%),
    radial-gradient(circle at 80% 10%, rgba(124, 58, 237, .35), transparent 30%),
    linear-gradient(135deg, #08111f, #111827 52%, #1e1b4b);
}

.auth-hero {
  color: white;
}

.brand-mark {
  width: 64px;
  height: 64px;
  display: grid;
  place-items: center;
  border-radius: 22px;
  background: linear-gradient(135deg, #38bdf8, #8b5cf6);
  box-shadow: 0 18px 50px rgba(59, 130, 246, .35);
  font-size: 24px;
  font-weight: 900;
}

.auth-hero h1 {
  margin: 28px 0 18px;
  font-size: 58px;
  line-height: 1.05;
  letter-spacing: -1.8px;
}

.auth-hero p {
  max-width: 640px;
  color: #cbd5e1;
  font-size: 20px;
  line-height: 1.8;
}

.hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 28px;
}

.auth-card {
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, .35);
  border-radius: 28px;
  background: rgba(255, 255, 255, .92);
  box-shadow: 0 26px 80px rgba(15, 23, 42, .32);
  backdrop-filter: blur(22px);
}

.card-title {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 24px;
}

.card-title span {
  color: var(--color-muted);
}

.card-title b {
  font-size: 28px;
}

.el-button {
  width: 100%;
  margin-top: 6px;
}

p {
  margin: 18px 0 0;
  color: var(--color-muted);
  text-align: center;
}

@media (max-width: 900px) {
  .auth-page {
    grid-template-columns: 1fr;
    padding: 28px;
  }

  .auth-hero h1 {
    font-size: 42px;
  }

  .auth-card {
    width: 100%;
    max-width: 480px;
    margin: auto;
  }
}
</style>
