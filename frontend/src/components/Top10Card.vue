<template>
  <div class="risk-card" @click="$emit('click')">
    <SealTag :show="isWarn" />
    <div class="rank">NO.{{ rank }}</div>
    <div class="cname">{{ company.company_name }}</div>
    <div class="gw-value" :class="{ warn: isWarn }">{{ gwDisplay }}</div>
    <div class="gw-bar">
      <div class="gw-bar-fill" :class="{ warn: isWarn }" :style="{ width: barWidth }"></div>
    </div>
    <div class="gw-label">GW INDEX</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import SealTag from './SealTag.vue'

const props = defineProps({
  company: { type: Object, required: true },
  rank: { type: Number, required: true },
  maxGw: { type: Number, default: 1 },
})
defineEmits(['click'])

const isWarn = computed(() => props.company.risk_level === '预警')
const gwDisplay = computed(() => props.company.gw_index?.toFixed(4) ?? '--')
const barWidth = computed(() => {
  const gw = props.company.gw_index ?? 0
  const pct = Math.min(gw / props.maxGw, 1) * 100
  return `${Math.max(pct, 5)}%`
})
</script>

<style scoped>
.risk-card {
  position: relative;
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius);
  padding: 18px 16px 16px;
  cursor: pointer;
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), background 0.25s ease, border-color 0.25s ease;
  display: flex;
  flex-direction: column;
  min-height: 150px;
}

.risk-card:hover {
  transform: translateY(-3px);
  background: var(--panel-bg-hover);
  border-color: var(--panel-border-hover);
}

.rank {
  font-size: 10px;
  color: var(--text-dim);
  font-weight: 600;
  letter-spacing: 1.5px;
  margin-bottom: 8px;
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
}

.cname {
  font-family: var(--font-sans);
  font-weight: 600;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.35;
  margin-bottom: 12px;
  min-height: 38px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.gw-value {
  font-family: var(--font-sans);
  font-weight: 800;
  font-size: 28px;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
  line-height: 1;
  letter-spacing: -0.02em;
  margin-bottom: 10px;
}

.gw-value.warn {
  color: var(--cinnabar-dim);
}

.gw-bar {
  height: 3px;
  background: var(--line);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 8px;
}

.gw-bar-fill {
  height: 100%;
  background: var(--jade-dim);
  border-radius: 2px;
  transition: width 0.4s ease;
  opacity: 0.6;
}

.gw-bar-fill.warn {
  background: var(--cinnabar-dim);
  opacity: 0.7;
}

.gw-label {
  font-size: 9px;
  color: var(--text-dim);
  letter-spacing: 2px;
  font-weight: 500;
  margin-top: auto;
  font-family: var(--font-mono);
}
</style>
