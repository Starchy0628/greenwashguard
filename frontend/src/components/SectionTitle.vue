<template>
  <div class="section-title">
    <div class="title-main">
      <span class="title-prefix"></span>
      <h2 class="title-text">
        <slot></slot>
      </h2>
    </div>
    <div v-if="$slots.aux" class="title-aux">
      <slot name="aux"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.section-title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-top: 48px;
  margin-bottom: 20px;
}

.title-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-prefix {
  width: 4px;
  height: 16px;
  background: var(--jade);
  border-radius: 2px;
}

.title-text {
  font-family: 'HarmonyOS Sans SC', 'Noto Sans SC', var(--font-sans);
  font-weight: 800;
  font-size: 22px;
  letter-spacing: 0.02em;
  margin: 0;
  color: var(--text-primary);
}

.title-text .highlight {
  color: var(--gold);
}

.title-aux {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 500;
}
</style>
