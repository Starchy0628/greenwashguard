<template>
  <div class="seal-wrapper" v-if="show">
    <div class="seal">
      <div class="seal-inner">
        <span class="seal-text">预警</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ show: { type: Boolean, default: false } })
</script>

<style scoped>
.seal-wrapper {
  position: absolute;
  top: 8px;
  left: 8px;
  width: 36px;
  height: 36px;
  z-index: 10;
}

.seal {
  position: relative;
  width: 100%;
  height: 100%;
  transform: rotate(-8deg);
}

.seal-inner {
  width: 100%;
  height: 100%;
  border: 1.5px solid var(--cinnabar);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--cinnabar-soft);
  position: relative;
  opacity: 0.7;
}

.seal-inner::before {
  content: '';
  position: absolute;
  inset: 3px;
  border: 1px solid var(--cinnabar);
  border-radius: 4px;
  opacity: 0.4;
}

.seal-text {
  font-family: 'Noto Serif SC', serif;
  font-weight: 700;
  font-size: 10px;
  color: var(--cinnabar-dim);
  letter-spacing: 1px;
  writing-mode: vertical-rl;
  line-height: 1.2;
}
</style>
