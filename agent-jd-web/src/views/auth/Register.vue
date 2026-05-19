<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <h2>创建账号</h2>
      <el-form :model="form" label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-button type="primary" size="large" @click="submit">注册并进入</el-button>
        <p>
          已有账号？
          <router-link to="/login">返回登录</router-link>
        </p>
      </el-form>
    </el-card>
  </div>
</template>
<script setup lang="ts">
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const form = reactive({ username: '', email: '', password: '' })

async function submit() {
  await auth.register(form)
  router.push('/')
}
</script>
<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
}

.auth-card {
  width: 420px;
  border-radius: 24px;
}

.el-button {
  width: 100%;
}
</style>
