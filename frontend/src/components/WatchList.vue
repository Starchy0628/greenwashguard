<template>
  <section class="block">
    <SectionTitle>
      我的关注列表
      <template #aux>{{ items.length }} 家企业</template>
    </SectionTitle>

    <div v-if="!items.length" class="watch-empty">
      暂无关注 · 查询企业后可添加关注
    </div>

    <div v-else class="watch-list">
      <div
        v-for="item in items"
        :key="item.stock_code"
        class="watch-row"
        @click="$emit('select', item)"
      >
        <div class="left">
          <span class="star">★</span>
          <span class="cname">{{ item.company_name }}</span>
        </div>
        <div class="right">
          <span class="gw" :class="{ warn: item.latest_risk_level === '预警' }">
            {{ item.latest_gw_index?.toFixed(4) ?? '--' }}
          </span>
          <button class="remove-btn" @click.stop="$emit('remove', item.stock_code)" title="取消关注">×</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import SectionTitle from './SectionTitle.vue'

defineProps({ items: { type: Array, default: () => [] } })
defineEmits(['select', 'remove'])
</script>

<style scoped>
.block { margin-bottom: 96px; }

.watch-empty {
  border: 1px dashed var(--panel-border);
  border-radius: var(--radius);
  padding: 28px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
}

.watch-list { display: flex; flex-direction: column; gap: 8px; }
.watch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius);
  padding: 14px 18px;
  cursor: pointer;
  transition: background 0.25s ease, border-color 0.25s ease;
}
.watch-row:hover {
  background: var(--panel-bg-hover);
  border-color: var(--panel-border-hover);
}

.left { display: flex; align-items: center; gap: 12px; }
.star { color: var(--gold); font-size: 14px; }
.cname { font-weight: 600; font-size: 14px; color: var(--text-primary); }

.right { display: flex; align-items: center; gap: 14px; }
.gw {
  font-variant-numeric: tabular-nums;
  font-size: 14px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-weight: 500;
}
.gw.warn { color: var(--cinnabar-dim); }

.remove-btn {
  background: none;
  border: 1px solid var(--panel-border);
  color: var(--text-muted);
  width: 26px;
  height: 26px;
  border-radius: 50%;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: all 0.25s ease;
}
.remove-btn:hover {
  border-color: var(--cinnabar);
  color: var(--cinnabar-dim);
  background: var(--cinnabar-soft);
}
</style>
