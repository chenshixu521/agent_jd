<template>
  <el-aside width="248px" class="sidebar">
    <div class="brand">
      <div class="logo">AI</div>
      <div>
        <b>Agent JD</b>
        <span>求职智能体平台</span>
      </div>
    </div>
    <el-menu router :default-active="$route.path" class="menu">
      <el-menu-item index="/">
        <House :size="18" />
        首页
      </el-menu-item>
      <el-menu-item index="/resume">
        <FileUp :size="18" />
        简历上传
      </el-menu-item>
      <el-menu-item index="/jd">
        <BriefcaseBusiness :size="18" />
        JD 上传
      </el-menu-item>
      <el-menu-item index="/analysis">
        <Sparkles :size="18" />
        AI 分析
      </el-menu-item>
      <el-menu-item index="/rewrite">
        <PenTool :size="18" />
        项目改写
      </el-menu-item>
      <el-menu-item index="/match">
        <Gauge :size="18" />
        匹配度
      </el-menu-item>
    </el-menu>
  </el-aside>
</template>

<script setup lang="ts">
import { BriefcaseBusiness, FileUp, Gauge, House, PenTool, Sparkles } from 'lucide-vue-next'
</script>

<style scoped>
.sidebar {
  padding: 18px 12px;
  background: #0f172a;
  color: white;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 10px 22px;
}

.logo {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  font-weight: 800;
}

.brand span {
  display: block;
  margin-top: 3px;
  color: #94a3b8;
  font-size: 12px;
}

.menu {
  border: 0;
  background: transparent;
}

:deep(.el-menu-item) {
  gap: 10px;
  margin: 4px 0;
  border-radius: 12px;
  color: #cbd5e1;
}

:deep(.el-menu-item.is-active),
:deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, .1);
  color: white;
}
</style>
