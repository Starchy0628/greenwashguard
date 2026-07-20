<template>
  <div class="result-card" :class="{ show: !!result }">
    <div class="result-top">
      <div>
        <div class="result-name">
          {{ result?.company_name }}
          <span class="result-code">{{ result?.stock_code }}</span>
        </div>
        <div class="result-industry">
          <span class="industry-main">
            所属行业：{{ result?.industry }}
            <span v-if="isSampleInsufficient" class="ref-tag" title="行业样本量不足30家，结果仅供参考">参考</span>
          </span>
          <span class="industry-note" title="行业分类依据《申万宏源行业分类标准（2021版）》，部分企业手动调整，请以实际归类为准">
            行业分类依据《申万宏源行业分类标准（2021版）》，部分企业手动调整，请以实际归类为准。
          </span>
        </div>
      </div>
      <SealTag :show="isWarn" />
    </div>

    <div class="gw-big" :class="{ warn: isWarn }">
      {{ gwDisplay }}
      <span class="u">GW 指数</span>
    </div>

    <div class="metric-row">
      <div class="metric-item">
        <div class="mv">{{ result?.summary?.total_substantive ?? result?.substantive_count ?? 0 }}</div>
        <div class="ml">实质性语句数</div>
      </div>
      <div class="metric-item">
        <div class="mv">{{ result?.summary?.total_descriptive ?? result?.descriptive_count ?? 0 }}</div>
        <div class="ml">描述性语句数</div>
      </div>
      <div class="metric-item">
        <div class="mv">{{ result?.summary?.total_dispute ?? result?.dispute_count ?? 0 }}</div>
        <div class="ml">分歧语句数</div>
      </div>
      <div class="metric-item">
        <div class="mv">{{ result?.industry_sample_count ?? 0 }}</div>
        <div class="ml">行业样本量
          <span v-if="isSampleInsufficient" class="ref-dot" title="样本量不足30家"></span>
        </div>
      </div>
      <div class="metric-item">
        <div class="mv non-env">{{ nonEnvCount }}</div>
        <div class="ml">非环保语句数</div>
      </div>
    </div>

    <SentenceList
      :year-groups="result?.yearGroups || []"
      :title="'环境语句'"
    />

    <TrendChart :data="trendData" />

    <div class="action-row">
      <button class="watch-btn" :class="{ watched: isWatched }" @click="$emit('toggleWatch')">
        {{ isWatched ? '✓ 已加入关注' : '+ 加入关注列表' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import SealTag from './SealTag.vue'
import SentenceList from './SentenceList.vue'
import TrendChart from './TrendChart.vue'

const props = defineProps({
  result: { type: Object, default: null },
  isWatched: { type: Boolean, default: false },
})
defineEmits(['toggleWatch'])

const isWarn = computed(() => props.result?.risk_level === '预警')
const gwDisplay = computed(() => props.result?.gw_index?.toFixed(4) ?? '--')
const isSampleInsufficient = computed(() => {
  const count = props.result?.industry_sample_count
  return count !== undefined && count !== null && count < 30
})

const nonEnvCount = computed(() => {
  if (props.result?.summary?.total_non_env != null) {
    return props.result.summary.total_non_env
  }
  if (props.result?.non_env_count != null) {
    return props.result.non_env_count
  }
  return 0
})

const envSentences = computed(() =>
  (props.result?.sentences || []).filter(s => s.final_category !== 'non_env')
)
const trendData = computed(() => props.result?.trend || [])
</script>

<style scoped>
.result-card {
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-lg);
  padding: 28px;
  display: none;
}
.result-card.show { display: block; animation: fade .4s cubic-bezier(0.16, 1, 0.3, 1); }
@keyframes fade { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }

.result-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}
.result-name {
  font-family: var(--font-sans);
  font-weight: 700;
  font-size: 22px;
  color: var(--text-primary);
  letter-spacing: 0.3px;
}
.result-code {
  font-size: 14px;
  color: var(--text-muted);
  font-weight: 500;
  margin-left: 6px;
  font-family: var(--font-mono);
}
.result-industry {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}
.industry-main {
  flex-shrink: 0;
}
.industry-note {
  font-size: 10px;
  color: var(--text-dim);
  line-height: 1.4;
  text-align: right;
  max-width: 420px;
}
@media (max-width: 720px) {
  .result-industry {
    flex-direction: column;
    gap: 4px;
  }
  .industry-note {
    text-align: left;
  }
}

.gw-big {
  font-family: var(--font-sans);
  font-weight: 800;
  font-size: 42px;
  font-variant-numeric: tabular-nums;
  margin-top: 20px;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}
.gw-big.warn { color: var(--cinnabar-dim); }

.gw-big .u {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-muted);
  margin-left: 10px;
}

.ref-tag {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 8px;
  font-size: 10px;
  font-weight: 600;
  color: var(--gold);
  background: var(--gold-soft);
  border: 1px solid rgba(201, 169, 97, 0.3);
  border-radius: var(--radius-sm);
  vertical-align: middle;
  cursor: help;
}

.metric-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin: 22px 0 24px;
  padding: 18px;
  background: var(--bg-elevated);
  border-radius: var(--radius);
  border: 1px solid var(--panel-border);
}
.metric-item { text-align: center; }
.metric-item .mv {
  font-family: var(--font-sans);
  font-weight: 700;
  font-size: 22px;
  color: var(--jade-dim);
  font-variant-numeric: tabular-nums;
}
.metric-item .mv.non-env {
  color: var(--text-muted);
}
.metric-item .ml {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
}
.ref-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--gold);
  cursor: help;
}

.action-row { margin-top: 24px; }
.watch-btn {
  background: var(--jade);
  color: #fff;
  border: none;
  padding: 11px 22px;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  font-family: var(--font-sans);
  transition: background 0.25s ease;
}
.watch-btn.watched { background: var(--jade-dim); opacity: 0.7; }
.watch-btn:hover { opacity: 0.9; }
</style>
