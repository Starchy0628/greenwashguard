<template>
  <header class="top">
    <BrandLogo :size="'medium'" :show-subtitle="true" subtitle="企业漂绿风险监测" />
  </header>
</template>

<script setup>
import BrandLogo from './BrandLogo.vue'
</script>

<style scoped>
header.top {
  position: sticky;
  top: 0;
  z-index: 20;
  background: linear-gradient(180deg, var(--bg-base) 80%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  padding: 24px 0 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 36px;
}
</style>
