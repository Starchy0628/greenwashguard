<template>
  <div
    ref="rootRef"
    class="stat-card group relative overflow-hidden bg-white rounded-card border border-line p-5 transition-all duration-300 hover:-translate-y-1 hover:shadow-card-hover"
    @mouseenter="hovered = true"
    @mouseleave="hovered = false"
  >
    <!-- 顶部装饰条 -->
    <div
      class="absolute top-0 left-0 right-0 h-[3px] transition-opacity duration-300"
      :class="accentBarClass"
      :style="{ opacity: hovered ? 1 : 0.55 }"
    />
    <!-- 指标名称 -->
    <div class="text-xs font-medium tracking-wider uppercase text-ink-muted mb-2">
      {{ label }}
    </div>
    <!-- 数值 + 单位 -->
    <div class="flex items-baseline gap-1">
      <span
        class="text-3xl font-bold tabular-nums leading-none"
        :class="valueClass"
      >
        {{ display }}
      </span>
      <span v-if="unit" class="text-sm font-medium text-ink-muted">
        {{ unit }}
      </span>
    </div>
    <!-- 副描述 -->
    <div v-if="description" class="mt-2 text-xs text-ink-dim">
      {{ description }}
    </div>
    <!-- 角标图标 -->
    <div
      class="absolute right-3 top-3 w-7 h-7 rounded-full flex items-center justify-center text-[10px] transition-transform duration-300 group-hover:scale-110"
      :class="iconWrapClass"
    >
      <svg v-if="tone === 'jade'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
        <polyline points="10 9 9 9 8 9"/>
      </svg>
      <svg v-else-if="tone === 'ink'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 21h18"/>
        <path d="M5 21V7l8-4v18"/>
        <path d="M19 21V11l-6-4"/>
        <line x1="9" y1="9" x2="9" y2="9.01"/>
        <line x1="9" y1="12" x2="9" y2="12.01"/>
        <line x1="9" y1="15" x2="9" y2="15.01"/>
      </svg>
      <svg v-else-if="tone === 'gold'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <circle cx="12" cy="12" r="6"/>
        <circle cx="12" cy="12" r="2"/>
      </svg>
      <svg v-else-if="tone === 'cinnabar'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="18" cy="18" r="10"/>
        <circle cx="6" cy="6" r="10"/>
        <path d="M15 9a3 3 0 0 1 0 6"/>
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useCountUp } from '../composables/useCountUp'

interface Props {
  label: string
  value: number
  unit?: string
  decimals?: number
  description?: string
  tone?: 'jade' | 'gold' | 'cinnabar' | 'ink'
}

const props = withDefaults(defineProps<Props>(), {
  decimals: 0,
  tone: 'jade',
})

const rootRef = ref<HTMLElement | null>(null)
const hovered = ref(false)

const valueRef = computed(() => props.value)

const { display, setupObserver } = useCountUp({
  end: valueRef,
  decimals: props.decimals,
  duration: 2000,
})

const toneMap = {
  jade: {
    bar: 'bg-jade',
    value: 'text-jade',
    icon: 'bg-jade-soft text-jade',
  },
  gold: {
    bar: 'bg-gold',
    value: 'text-gold',
    icon: 'bg-gold-soft text-gold',
  },
  cinnabar: {
    bar: 'bg-cinnabar',
    value: 'text-cinnabar',
    icon: 'bg-cinnabar-soft text-cinnabar',
  },
  ink: {
    bar: 'bg-ink',
    value: 'text-ink',
    icon: 'bg-line text-ink',
  },
}

const toneConf = computed(() => toneMap[props.tone])
const accentBarClass = computed(() => toneConf.value.bar)
const valueClass = computed(() => toneConf.value.value)
const iconWrapClass = computed(() => toneConf.value.icon)

onMounted(() => {
  setupObserver(rootRef.value)
})
</script>

<style scoped>
.stat-card {
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 4px 12px rgba(15, 23, 42, 0.04);
}
</style>
