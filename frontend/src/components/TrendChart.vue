<template>
  <div class="trend-wrap" v-if="hasValidData">
    <h4>历史趋势</h4>
    <div class="chart-note">
      <span>行业基准线（中位数）：展示同行业企业当年环境语调中位数，作为企业GW指数的对比参考</span>
    </div>
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({ data: { type: Array, default: () => [] } })
const chartRef = ref(null)
let chart = null
let resizeObserver = null
let renderRetryTimer = null

const hasValidData = computed(() => {
  if (!props.data || !props.data.length) return false
  return props.data.some(d => d.gw_index !== null && d.gw_index !== undefined)
})

function clearRetryTimer() {
  if (renderRetryTimer) {
    clearTimeout(renderRetryTimer)
    renderRetryTimer = null
  }
}

function renderChart() {
  clearRetryTimer()
  if (!chartRef.value || !hasValidData.value) return
  try {
    const rect = chartRef.value.getBoundingClientRect()
    if (rect.width === 0 || rect.height === 0) {
      console.log('TrendChart: DOM not visible, retrying...')
      renderRetryTimer = setTimeout(renderChart, 100)
      return
    }
    if (!chart) {
      chart = echarts.init(chartRef.value)
      if (typeof ResizeObserver !== 'undefined') {
        resizeObserver = new ResizeObserver(() => {
          if (chart) chart.resize()
        })
        resizeObserver.observe(chartRef.value)
      }
    }
    console.log('TrendChart: rendering with data length:', props.data.length)

    const sortedData = [...props.data].sort((a, b) => a.year - b.year)
    const years = sortedData.map(d => d.year)
    const gwValues = sortedData.map(d => d.gw_index ?? null)
    const industryMedian = sortedData.map(d => d.industry_median_gw ?? null)

    // 标记 GW 指数缺失的年份（以空心圆点标识断点）
    const breakPoints = sortedData
      .filter(d => (d.gw_index === null || d.gw_index === undefined) && d.industry_median_gw !== null && d.industry_median_gw !== undefined)
      .map(d => ({
        name: '数据缺失',
        xAxis: d.year,
        yAxis: d.industry_median_gw,
        value: '无数据',
      }))

    chart.setOption({
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#142D25',
        borderColor: 'rgba(238, 238, 228, 0.1)',
        borderWidth: 1,
        textStyle: { color: '#E8E6E0', fontSize: 12, fontFamily: 'Inter, sans-serif' },
        padding: [10, 14],
        formatter: (params) => {
          const idx = params[0].dataIndex
          const row = sortedData[idx]
          const lines = [`年份：${params[0].axisValue}`]
          params.forEach(p => {
            if (p.seriesName === '数据断点') return
            if (p.value !== null && p.value !== undefined) {
              lines.push(`${p.marker} ${p.seriesName}：${p.value.toFixed(4)}`)
            } else if (p.seriesName === '企业GW指数') {
              lines.push(`${p.marker} ${p.seriesName}：无数据`)
            }
          })
          if (row.risk_level) {
            lines.push(`风险等级：${row.risk_level}`)
          }
          return lines.join('<br/>')
        },
      },
      legend: {
        data: ['企业GW指数', '行业中位数'],
        textStyle: { color: '#6B7D74', fontSize: 11, fontFamily: 'Inter, sans-serif' },
        top: 0,
        right: 0,
        itemWidth: 12,
        itemHeight: 8,
      },
      grid: { top: 32, right: 20, bottom: 28, left: 54 },
      xAxis: {
        type: 'category',
        data: years,
        axisLine: { lineStyle: { color: 'rgba(238, 238, 228, 0.08)' } },
        axisLabel: { color: '#6B7D74', fontSize: 11, fontFamily: 'Inter, sans-serif' },
      },
      yAxis: {
        type: 'value',
        name: 'GW指数/语调',
        nameTextStyle: { color: '#6B7D74', fontSize: 10, fontFamily: 'Inter, sans-serif' },
        axisLine: { show: false },
        splitLine: { lineStyle: { color: 'rgba(238, 238, 228, 0.04)' } },
        axisLabel: { color: '#6B7D74', fontSize: 10, fontFamily: 'JetBrains Mono, monospace' },
      },
      series: [
        {
          name: '企业GW指数',
          data: gwValues,
          type: 'line',
          smooth: false,
          connectNulls: false,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { color: '#A85050', width: 2 },
          itemStyle: { color: '#A85050' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(168,80,80,0.12)' },
              { offset: 1, color: 'rgba(168,80,80,0)' },
            ]),
          },
          markPoint: {
            symbol: 'emptyCircle',
            symbolSize: 8,
            itemStyle: { color: 'transparent', borderColor: '#A85050', borderWidth: 1.5 },
            label: { show: false },
            data: breakPoints,
            tooltip: {
              formatter: () => '该年份企业 GW 指数数据缺失',
            },
          },
        },
        {
          name: '行业中位数',
          data: industryMedian,
          type: 'line',
          smooth: false,
          connectNulls: false,
          symbol: 'diamond',
          symbolSize: 5,
          lineStyle: { color: '#5A9388', width: 2, type: 'dashed' },
          itemStyle: { color: '#5A9388' },
        },
      ],
    }, true)
  } catch (e) {
    console.error('TrendChart render error:', e)
  }
}

onMounted(() => {
  nextTick(() => renderChart())
})
watch(() => props.data, () => {
  nextTick(() => renderChart())
}, { deep: true })
watch(hasValidData, (val) => {
  if (val) {
    nextTick(() => renderChart())
  }
})
onUnmounted(() => {
  clearRetryTimer()
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<style scoped>
.trend-wrap { margin-top: 26px; }
.trend-wrap h4 {
  font-size: 12px;
  letter-spacing: 1.5px;
  color: var(--text-muted);
  text-transform: uppercase;
  margin-bottom: 8px;
  font-weight: 600;
  font-family: var(--font-sans);
}
.chart-note {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 10px;
  padding: 6px 10px;
  background: var(--jade-soft);
  border-radius: var(--radius-sm);
  border-left: 2px solid var(--jade);
}
.chart-container { width: 100%; height: 260px; }
</style>
