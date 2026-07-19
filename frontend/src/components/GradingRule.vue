<template>
  <section class="block">
    <SectionTitle>
      风险分级依据
    </SectionTitle>
    <div class="rule-bar">
      <div class="seg normal">
        <span class="seg-label">正常</span>
      </div>
      <div class="seg warn">
        <span class="seg-label">预警</span>
      </div>
    </div>
    <div class="rule-legend">
      <span><b>正常</b> · 前 80% 分位</span>
      <span><b>预警</b> · 后 20% 分位</span>
    </div>
    <div class="rule-text">
      <ul class="rule-list">
        <li class="rule-item">全市场企业GW指数按分布统一排序</li>
        <li class="rule-item">后20%企业标记为「预警」 触发红色印记提示</li>
        <li class="rule-item">其余企业均显示为「正常」 不做额外标注</li>
        <li class="rule-item">阈值随全市场数据分布定期滚动校准</li>
      </ul>
    </div>
  </section>
</template>

<script setup>
import SectionTitle from './SectionTitle.vue'
</script>

<style scoped>
.block { margin-bottom: 96px; }

.rule-bar {
  display: flex;
  height: 36px;
  border-radius: var(--radius);
  overflow: hidden;
  margin: 16px 0 12px;
  border: 1px solid var(--panel-border);
}
.rule-bar .seg {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.rule-bar .seg.normal {
  background: var(--jade-soft);
  flex: 8;
}
.rule-bar .seg.warn {
  background: var(--cinnabar-soft);
  flex: 2;
  border-left: 1px solid var(--panel-border);
}
.seg-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 1px;
}
.seg.normal .seg-label { color: var(--jade-dim); }
.seg.warn .seg-label { color: var(--cinnabar-dim); }

.rule-legend {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-muted);
}
.rule-legend b {
  color: var(--text-secondary);
  font-weight: 600;
}
.rule-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.8;
  margin-top: 14px;
  padding: 16px 18px;
  background: rgba(58, 122, 110, 0.08);
  border-radius: var(--radius);
  border: 1px solid rgba(58, 122, 110, 0.18);
}

.rule-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rule-item {
  position: relative;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.rule-item::before {
  content: '';
  position: absolute;
  left: 4px;
  top: 9px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--jade);
}
</style>
