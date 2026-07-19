<template>
  <div class="sent-group">
    <h4>{{ title }}（共{{ totalEnvSentences }}条）</h4>
    <div v-if="!yearGroups.length" class="empty">暂无数据</div>
    <template v-else>
      <div
        v-for="group in yearGroups"
        :key="group.year"
        class="year-group"
      >
        <div class="year-header" @click="toggleYear(group.year)">
          <span class="year-label">{{ group.year }}年</span>
          <span class="year-stats">
            环境语句{{ group.env_sentences }}条 · 实质性{{ group.substantive_count }}条 · 描述性{{ group.descriptive_count }}条 · 分歧{{ group.dispute_count }}条
          </span>
          <span class="year-toggle">{{ expandedYears.includes(group.year) ? '收起' : '展开' }}</span>
        </div>
        <div v-show="expandedYears.includes(group.year)" class="year-content">
          <div
            v-for="(s, i) in getVisibleSentences(group)"
            :key="i"
            class="sent-item"
            :class="{ dispute: s.needs_review, open: s._open }"
            @click="toggleExpand(s)"
          >
            <span class="tag">{{ s.needs_review ? '待复核' : labelMap[s.final_category] || s.final_category }}</span>
            {{ s.sentence_text }}
            <div class="sent-detail" v-if="s._open">
              <div>Deepseek: {{ s.deepseek_result }}</div>
              <div>Qwen: {{ s.qwen_result }}</div>
              <div>GLM: {{ s.glm_result }}</div>
              <div v-if="s.sentiment_score !== null && s.sentiment_score !== undefined">情感评分: {{ s.sentiment_score?.toFixed(2) }}</div>
            </div>
          </div>
          <div v-if="group.sentences.length > 5" class="toggle-btn" @click.stop="toggleGroupExpand(group)">
            {{ group._expanded ? '收起' : `展开全部（${group.sentences.length} 条）` }}
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  yearGroups: { type: Array, default: () => [] },
  title: { type: String, default: '环境语句' },
})

const labelMap = { substantive: '实质性', descriptive: '描述性', non_env: '非环保', non_environmental: '非环保' }
const expandedYears = ref([])

const totalEnvSentences = computed(() => {
  return props.yearGroups.reduce((sum, group) => sum + (group.env_sentences || 0), 0)
})

function toggleYear(year) {
  const idx = expandedYears.value.indexOf(year)
  if (idx > -1) {
    expandedYears.value.splice(idx, 1)
  } else {
    expandedYears.value.push(year)
  }
}

function toggleGroupExpand(group) {
  group._expanded = !group._expanded
}

function getVisibleSentences(group) {
  if (group._expanded) return group.sentences
  return group.sentences.slice(0, 5)
}

function toggleExpand(s) {
  s._open = !s._open
}
</script>

<style scoped>
.sent-group { margin-top: 26px; }
.sent-group h4 {
  font-size: 12px;
  letter-spacing: 1.5px;
  color: var(--text-muted);
  text-transform: uppercase;
  margin-bottom: 12px;
  font-weight: 600;
  font-family: var(--font-sans);
}
.empty { font-size: 13px; color: var(--text-muted); padding: 8px 0; }

.year-group {
  margin-bottom: 10px;
  border: 1px solid var(--panel-border);
  border-radius: var(--radius);
  overflow: hidden;
  background: var(--panel-bg);
  transition: border-color 0.25s ease;
}
.year-group:hover {
  border-color: var(--panel-border-hover);
}

.year-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-elevated);
  cursor: pointer;
  gap: 12px;
  flex-wrap: wrap;
  transition: background 0.25s ease;
}
.year-header:hover {
  background: var(--bg-surface);
}

.year-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-sans);
}

.year-stats {
  font-size: 12px;
  color: var(--text-muted);
  flex: 1;
}

.year-toggle {
  font-size: 12px;
  color: var(--jade-dim);
  font-weight: 600;
}

.year-content {
  padding: 0 16px;
}

.sent-item {
  border-top: 1px solid var(--line);
  padding: 12px 0;
  font-size: 13.5px;
  line-height: 1.7;
  cursor: pointer;
  color: var(--text-secondary);
  transition: color 0.2s ease;
}
.sent-item:hover { color: var(--text-primary); }
.sent-item:first-child {
  border-top: none;
}

.sent-item .tag {
  display: inline-block;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  margin-right: 8px;
  background: var(--jade-soft);
  color: var(--jade-dim);
  font-weight: 600;
  vertical-align: middle;
}
.sent-item.dispute .tag { background: var(--cinnabar-soft); color: var(--cinnabar-dim); }

.sent-detail {
  display: none;
  margin-top: 10px;
  padding: 10px 12px;
  background: var(--bg-base);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  line-height: 1.8;
}
.sent-item.open .sent-detail { display: block; }

.toggle-btn {
  margin: 8px 0 14px;
  font-size: 12.5px;
  color: var(--jade-dim);
  cursor: pointer;
  font-weight: 600;
}
.toggle-btn:hover { color: var(--jade); }
</style>
