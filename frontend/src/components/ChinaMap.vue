<template>
  <div class="china-map-card">
    <div ref="chartRef" class="map-chart"></div>
    <div class="map-stat-card">
      <div class="stat-label">
        <span class="pulse-dot"></span>
        实时监测中
      </div>
      <div class="stat-value">
        <span class="stat-number">{{ formattedCount }}</span>
        <span class="stat-unit">家企业</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import chinaGeoJson from '../assets/geojson/china.json'

const props = defineProps({
  companyCount: {
    type: Number,
    default: 5522,
  },
})

const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null
let resizeObserver: ResizeObserver | null = null

const formattedCount = computed(() =>
  props.companyCount.toLocaleString('en-US')
)

function generateEnterprisePoints() {
  const points: [number, number, number][] = []

  const clusters = [
    { center: [121.47, 31.23], radius: 2.5, count: 80, name: '长三角' },
    { center: [113.26, 23.13], radius: 2.0, count: 60, name: '珠三角' },
    { center: [116.41, 39.91], radius: 2.0, count: 50, name: '京津冀' },
    { center: [104.07, 30.67], radius: 1.5, count: 20, name: '成渝' },
    { center: [114.31, 30.60], radius: 1.2, count: 15, name: '武汉' },
    { center: [108.94, 34.34], radius: 1.0, count: 12, name: '西安' },
    { center: [120.15, 30.28], radius: 1.0, count: 18, name: '杭州' },
    { center: [118.78, 32.04], radius: 0.9, count: 14, name: '南京' },
    { center: [113.42, 23.12], radius: 0.8, count: 12, name: '广州' },
    { center: [114.06, 22.54], radius: 0.9, count: 15, name: '深圳' },
    { center: [117.20, 31.86], radius: 0.8, count: 10, name: '合肥' },
    { center: [113.00, 28.22], radius: 0.8, count: 10, name: '长沙' },
    { center: [119.30, 26.08], radius: 0.7, count: 8, name: '福州' },
    { center: [126.53, 45.80], radius: 0.8, count: 10, name: '哈尔滨' },
    { center: [123.43, 41.81], radius: 0.8, count: 10, name: '沈阳' },
    { center: [117.00, 36.65], radius: 0.9, count: 12, name: '济南' },
    { center: [114.48, 38.03], radius: 0.8, count: 10, name: '石家庄' },
    { center: [112.55, 37.87], radius: 0.7, count: 8, name: '太原' },
    { center: [106.71, 26.57], radius: 0.7, count: 7, name: '贵阳' },
    { center: [102.71, 25.04], radius: 0.7, count: 7, name: '昆明' },
    { center: [108.33, 22.84], radius: 0.6, count: 6, name: '南宁' },
    { center: [115.89, 28.68], radius: 0.7, count: 8, name: '南昌' },
    { center: [113.62, 34.75], radius: 0.8, count: 10, name: '郑州' },
    { center: [91.13, 29.65], radius: 0.4, count: 3, name: '拉萨' },
    { center: [103.82, 36.06], radius: 0.5, count: 5, name: '兰州' },
    { center: [106.28, 38.47], radius: 0.4, count: 4, name: '银川' },
    { center: [87.62, 43.82], radius: 0.5, count: 5, name: '乌鲁木齐' },
    { center: [101.78, 36.62], radius: 0.4, count: 3, name: '西宁' },
    { center: [111.75, 40.84], radius: 0.5, count: 5, name: '呼和浩特' },
    { center: [121.62, 38.92], radius: 0.5, count: 5, name: '大连' },
    { center: [120.38, 36.07], radius: 0.6, count: 7, name: '青岛' },
    { center: [118.06, 24.48], radius: 0.6, count: 7, name: '厦门' },
    { center: [110.33, 20.03], radius: 0.4, count: 3, name: '海口' },
  ]

  clusters.forEach((cluster) => {
    for (let i = 0; i < cluster.count; i++) {
      const angle = Math.random() * Math.PI * 2
      const distance = Math.pow(Math.random(), 0.6) * cluster.radius
      const lon = cluster.center[0] + Math.cos(angle) * distance
      const lat = cluster.center[1] + Math.sin(angle) * distance * 0.8
      const size = 6 + Math.random() * 6
      points.push([lon, lat, size])
    }
  })

  return points
}

function renderChart() {
  if (!chartRef.value) return

  const rect = chartRef.value.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) {
    setTimeout(renderChart, 100)
    return
  }

  if (!chart) {
    chart = echarts.init(chartRef.value)
  }

  echarts.registerMap('china', chinaGeoJson as any)

  const points = generateEnterprisePoints()

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    geo: {
      map: 'china',
      roam: false,
      zoom: 1.15,
      center: [104, 36],
      itemStyle: {
        areaColor: 'rgba(15, 35, 30, 0.85)',
        borderColor: 'rgba(90, 200, 170, 0.4)',
        borderWidth: 1,
        shadowColor: 'rgba(0, 200, 150, 0.15)',
        shadowBlur: 20,
      },
      emphasis: {
        disabled: true,
      },
      select: {
        disabled: true,
      },
    },
    series: [
      {
        type: 'effectScatter',
        coordinateSystem: 'geo',
        data: points.map((p) => ({
          value: [p[0], p[1]],
          symbolSize: p[2],
        })),
        symbolSize: (val: any, params: any) => {
          return params.data.symbolSize || 8
        },
        showEffectOn: 'render',
        rippleEffect: {
          brushType: 'stroke',
          scale: 3,
          period: 4,
        },
        hoverAnimation: true,
        itemStyle: {
          color: '#4FD1B3',
          shadowBlur: 10,
          shadowColor: '#4FD1B3',
          opacity: 0.9,
        },
        emphasis: {
          itemStyle: {
            color: '#7FEDD0',
            shadowBlur: 16,
          },
        },
      },
      {
        type: 'scatter',
        coordinateSystem: 'geo',
        data: points.map((p) => ({
          value: [p[0], p[1]],
          symbolSize: p[2] * 0.5,
        })),
        symbolSize: (val: any, params: any) => {
          return params.data.symbolSize || 4
        },
        itemStyle: {
          color: '#9FF5DF',
          shadowBlur: 6,
          shadowColor: '#4FD1B3',
          opacity: 0.95,
        },
        zlevel: 2,
      },
    ],
    tooltip: {
      show: false,
    },
  }

  chart.setOption(option)
}

function handleResize() {
  chart?.resize()
}

onMounted(() => {
  renderChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.china-map-card {
  position: relative;
  width: 100%;
  height: 460px;
  border-radius: 24px;
  overflow: hidden;
  background: linear-gradient(135deg, #0A1F1A 0%, #0F2D26 50%, #0A1F1A 100%);
  box-shadow:
    0 20px 60px -20px rgba(15, 23, 42, 0.45),
    0 8px 24px -8px rgba(58, 122, 110, 0.3),
    inset 0 1px 0 rgba(100, 200, 180, 0.1);
  border: 1px solid rgba(80, 180, 160, 0.15);
}

.map-chart {
  width: 100%;
  height: 100%;
}

.map-stat-card {
  position: absolute;
  bottom: 18px;
  right: 18px;
  background: rgba(10, 23, 20, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  padding: 12px 18px;
  border-radius: 14px;
  border: 1px solid rgba(100, 200, 170, 0.2);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  min-width: 160px;
}

.stat-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: rgba(180, 220, 200, 0.8);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  margin-bottom: 6px;
  font-family: 'Inter', 'HarmonyOS Sans SC', sans-serif;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4ADE80;
  box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7);
  animation: pulseGlow 1.6s ease-in-out infinite;
}

@keyframes pulseGlow {
  0% {
    box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(74, 222, 128, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(74, 222, 128, 0);
  }
}

.stat-value {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.stat-number {
  font-family: 'JetBrains Mono', 'SF Mono', monospace;
  font-size: 20px;
  font-weight: 700;
  color: #E8F7F2;
  letter-spacing: -0.01em;
  font-variant-numeric: tabular-nums;
}

.stat-unit {
  font-size: 12px;
  color: rgba(160, 200, 180, 0.7);
  font-weight: 500;
}

@media (max-width: 960px) {
  .china-map-card {
    height: 380px;
  }
}
</style>
