<template>
  <section class="block">
    <SectionTitle>
      风险企业 <span class="highlight">TOP 10</span>
      <template #aux>按GW指数降序排列</template>
    </SectionTitle>
    <div class="risk-grid">
      <Top10Card
        v-for="(c, i) in companies"
        :key="c.stock_code"
        :company="c"
        :rank="i + 1"
        :max-gw="maxGw"
        @click="$emit('select', c)"
      />
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import Top10Card from './Top10Card.vue'
import SectionTitle from './SectionTitle.vue'

const props = defineProps({ companies: { type: Array, default: () => [] } })
defineEmits(['select'])

const maxGw = computed(() => {
  if (!props.companies.length) return 1
  return Math.max(...props.companies.map(c => c.gw_index ?? 0), 0.01)
})
</script>

<style scoped>
.block { margin-bottom: 96px; }

.risk-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 14px;
}
</style>
