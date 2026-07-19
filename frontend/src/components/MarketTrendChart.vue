<template>
  <div class="trend-wrap" v-if="data.length">
    <h4>全市场年度趋势</h4>
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { companiesApi } from '../api'

const data = ref([])
const chartRef = ref(null)
let chart = null

function renderChart() {
  if (!chartRef.value || !data.value.length) return
  try {
    const rect = chartRef.value.getBoundingClientRect()
    if (rect.width === 0 || rect.height === 0) {
      console.log('MarketTrendChart: DOM not visible, retrying...')
      setTimeout(renderChart, 100)
      return
    }
    if (!chart) chart = echarts.init(chartRef.value)
    console.log('MarketTrendChart: rendering with data length:', data.value.length)

  const years = data.value.map(d => d.year)
  const avg = data.value.map(d => d.avg_gw_index)
  const median = data.value.map(d => d.median_gw_index)
  const rows = data.value

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1B2E27',
      borderColor: '#2F6F62',
      textStyle: { color: '#EEEEE4', fontSize: 12 },
      formatter: (params) => {
        const idx = params[0].dataIndex
        const row = rows[idx]
        const count = row.count ?? row.company_count ?? 0
        const lines = [`年份：${params[0].axisValue}`]
        params.forEach(p => {
          lines.push(`${p.marker} ${p.seriesName}：${p.value?.toFixed(4) ?? '--'}`)
        })
        lines.push(`企业数量：${count}`)
        return lines.join('<br/>')
      },
    },
    legend: {
      data: ['均值', '中位数'],
      textStyle: { color: '#6E9186', fontSize: 11 },
      top: 0,
      right: 0,
      itemWidth: 12,
      itemHeight: 8,
    },
    grid: { top: 28, right: 20, bottom: 24, left: 50 },
    xAxis: {
      type: 'category',
      data: years,
      axisLine: { lineStyle: { color: 'rgba(238,238,228,0.2)' } },
      axisLabel: { color: '#6E9186', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      name: 'GW指数',
      nameTextStyle: { color: '#6E9186', fontSize: 10 },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: 'rgba(238,238,228,0.08)' } },
      axisLabel: { color: '#6E9186', fontSize: 10 },
    },
    series: [
      {
        name: '均值',
        data: avg,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: '#A83B2E', width: 2 },
        itemStyle: { color: '#A83B2E' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(168,59,46,0.15)' },
            { offset: 1, color: 'rgba(168,59,46,0)' },
          ]),
        },
      },
      {
        name: '中位数',
        data: median,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: '#2F6F62', width: 2 },
        itemStyle: { color: '#2F6F62' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(47,111,98,0.15)' },
            { offset: 1, color: 'rgba(47,111,98,0)' },
          ]),
        },
      },
    ],
  }, true)
    } catch (e) {
      console.error('MarketTrendChart render error:', e)
    }
}

async function loadData() {
  try {
    const res = await companiesApi.getMarketTrend()
    data.value = Array.isArray(res) ? res : (res?.data || [])
    console.log('MarketTrendChart: loaded data length:', data.value.length)
    nextTick(() => renderChart())
  } catch (e) {
    console.error('MarketTrendChart load error:', e)
    data.value = []
  }
}

onMounted(() => {
  loadData()
})
onUnmounted(() => { if (chart) { chart.dispose(); chart = null } })
</script>

<style scoped>
.trend-wrap { margin-top: 22px; }
.trend-wrap h4 {
  font-size: 12.5px;
  letter-spacing: 1px;
  color: var(--ink-soft);
  text-transform: uppercase;
  margin-bottom: 8px;
  font-weight: 700;
}
.chart-container { width: 100%; height: 200px; }
</style>
