<template>
  <div class="toast" :class="{ show: visible, error: type === 'error' }">{{ message }}</div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  message: { type: String, default: '' },
  type: { type: String, default: 'info' },
  duration: { type: Number, default: 2500 },
})
const emit = defineEmits(['done'])
const visible = ref(false)

watch(() => props.message, (val) => {
  if (val) {
    visible.value = true
    setTimeout(() => {
      visible.value = false
      emit('done')
    }, props.duration)
  }
})
</script>

<style scoped>
.toast {
  position: fixed;
  bottom: 48px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--bg-surface);
  color: var(--text-primary);
  padding: 12px 28px;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 600;
  z-index: 100;
  opacity: 0;
  transition: opacity .3s ease, transform .3s ease;
  pointer-events: none;
  border: 1px solid var(--panel-border);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}
.toast.show { opacity: 1; transform: translateX(-50%) translateY(-4px); }
.toast.error {
  background: var(--cinnabar-soft);
  color: var(--cinnabar-dim);
  border-color: var(--cinnabar);
}
</style>
