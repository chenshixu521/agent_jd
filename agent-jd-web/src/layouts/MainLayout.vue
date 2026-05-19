<template>
  <el-container class="app-shell">
    <AppSidebar />
    <el-container direction="vertical" class="content-shell">
      <AppHeader />
      <el-main class="app-main" :class="{ 'dashboard-main': route.name === 'dashboard' }">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import AppHeader from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
}

.content-shell {
  min-width: 0;
}

.app-main {
  min-height: calc(100vh - 76px);
  padding: 24px;
  background: var(--color-bg);
}

.dashboard-main {
  position: relative;
  overflow: hidden;
  padding: 0;
}
</style>
