<template>
  <div class="china-map-card">
    <div ref="chartRef" class="map-chart"></div>
    <div class="map-glow"></div>
    <div class="map-stat-card">
      <div class="stat-label">
        <span class="pulse-dot">
          <span class="pulse-ring ring-1"></span>
          <span class="pulse-ring ring-2"></span>
          <span class="pulse-ring ring-3"></span>
          <span class="pulse-core"></span>
        </span>
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
    default: 5495,
  },
})

const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null
let animationFrameId: number | null = null

const formattedCount = computed(() =>
  props.companyCount.toLocaleString('en-US')
)

const PROVINCE_DENSITY: Record<string, number> = {
  '广东省': 902,
  '浙江省': 723,
  '江苏省': 715,
  '北京市': 476,
  '上海市': 471,
  '山东省': 312,
  '安徽省': 191,
  '四川省': 183,
  '福建省': 171,
  '湖北省': 152,
  '湖南省': 141,
  '河南省': 122,
  '辽宁省': 95,
  '河北省': 86,
  '江西省': 85,
  '陕西省': 83,
  '天津市': 76,
  '重庆市': 74,
  '新疆维吾尔自治区': 58,
  '吉林省': 46,
  '山西省': 41,
  '广西壮族自治区': 41,
  '黑龙江省': 37,
  '云南省': 37,
  '内蒙古自治区': 35,
  '贵州省': 33,
  '海南省': 33,
  '甘肃省': 32,
  '西藏自治区': 20,
  '宁夏回族自治区': 15,
  '青海省': 9,
  '台湾省': 5,
  '香港特别行政区': 5,
  '澳门特别行政区': 2,
}

interface Cluster {
  center: [number, number]
  baseRadius: number
  particleCount: number
  tier: 'major' | 'medium' | 'small'
  particles: { lon: number; lat: number; size: number; offset: number }[]
  staticParticles: { lon: number; lat: number; size: number }[]
  phase: number
  brightness: number
}

function seededRandom(seed: number) {
  let s = seed
  return () => {
    s = (s * 9301 + 49297) % 233280
    return s / 233280
  }
}

function generateClusters(): Cluster[] {
  const scaleFactor = props.companyCount / 5495
  const rand = seededRandom(42)

  const clusterDefs: { center: [number, number]; radius: number; count: number; tier: 'major' | 'medium' | 'small' }[] = [
    { center: [121.47, 31.23], radius: 2.0, count: Math.round(85 * scaleFactor), tier: 'major' },
    { center: [120.15, 30.28], radius: 1.1, count: Math.round(48 * scaleFactor), tier: 'major' },
    { center: [118.78, 32.04], radius: 1.0, count: Math.round(32 * scaleFactor), tier: 'medium' },
    { center: [113.26, 23.13], radius: 1.8, count: Math.round(72 * scaleFactor), tier: 'major' },
    { center: [114.06, 22.54], radius: 1.0, count: Math.round(42 * scaleFactor), tier: 'major' },
    { center: [116.41, 39.91], radius: 2.0, count: Math.round(60 * scaleFactor), tier: 'major' },
    { center: [117.20, 31.86], radius: 1.0, count: Math.round(22 * scaleFactor), tier: 'medium' },
    { center: [120.38, 36.07], radius: 0.9, count: Math.round(18 * scaleFactor), tier: 'medium' },
    { center: [117.00, 36.65], radius: 0.9, count: Math.round(22 * scaleFactor), tier: 'medium' },
    { center: [113.00, 28.22], radius: 0.9, count: Math.round(22 * scaleFactor), tier: 'medium' },
    { center: [114.31, 30.60], radius: 1.4, count: Math.round(36 * scaleFactor), tier: 'major' },
    { center: [104.07, 30.67], radius: 1.5, count: Math.round(36 * scaleFactor), tier: 'major' },
    { center: [106.55, 29.56], radius: 0.9, count: Math.round(18 * scaleFactor), tier: 'medium' },
    { center: [108.94, 34.34], radius: 1.0, count: Math.round(20 * scaleFactor), tier: 'medium' },
    { center: [113.62, 34.75], radius: 0.9, count: Math.round(20 * scaleFactor), tier: 'medium' },
    { center: [119.30, 26.08], radius: 0.9, count: Math.round(22 * scaleFactor), tier: 'medium' },
    { center: [118.06, 24.48], radius: 0.8, count: Math.round(16 * scaleFactor), tier: 'small' },
    { center: [126.53, 45.80], radius: 0.9, count: Math.round(14 * scaleFactor), tier: 'small' },
    { center: [123.43, 41.81], radius: 0.9, count: Math.round(16 * scaleFactor), tier: 'small' },
    { center: [121.62, 38.92], radius: 0.6, count: Math.round(10 * scaleFactor), tier: 'small' },
    { center: [114.48, 38.03], radius: 0.7, count: Math.round(10 * scaleFactor), tier: 'small' },
    { center: [112.55, 37.87], radius: 0.6, count: Math.round(9 * scaleFactor), tier: 'small' },
    { center: [115.89, 28.68], radius: 0.7, count: Math.round(12 * scaleFactor), tier: 'small' },
    { center: [106.71, 26.57], radius: 0.7, count: Math.round(10 * scaleFactor), tier: 'small' },
    { center: [102.71, 25.04], radius: 0.7, count: Math.round(10 * scaleFactor), tier: 'small' },
    { center: [108.33, 22.84], radius: 0.6, count: Math.round(9 * scaleFactor), tier: 'small' },
    { center: [91.13, 29.65], radius: 0.5, count: Math.round(5 * scaleFactor), tier: 'small' },
    { center: [103.82, 36.06], radius: 0.6, count: Math.round(9 * scaleFactor), tier: 'small' },
    { center: [106.28, 38.47], radius: 0.4, count: Math.round(5 * scaleFactor), tier: 'small' },
    { center: [87.62, 43.82], radius: 0.6, count: Math.round(9 * scaleFactor), tier: 'small' },
    { center: [101.78, 36.62], radius: 0.4, count: Math.round(4 * scaleFactor), tier: 'small' },
    { center: [111.75, 40.84], radius: 0.5, count: Math.round(7 * scaleFactor), tier: 'small' },
    { center: [110.33, 20.03], radius: 0.5, count: Math.round(7 * scaleFactor), tier: 'small' },
  ]

  return clusterDefs.map((def, idx) => {
    const radius = def.radius
    const dynamicCount = def.count * 8
    const staticCount = Math.max(0, Math.round(def.count * 30))

    const particles: Cluster['particles'] = []
    for (let i = 0; i < dynamicCount; i++) {
      const angle = rand() * Math.PI * 2
      const r = Math.pow(rand(), 0.5) * radius * 0.7
      particles.push({
        lon: def.center[0] + Math.cos(angle) * r,
        lat: def.center[1] + Math.sin(angle) * r * 0.75,
        size: def.tier === 'major' ? 3 + rand() * 6 : def.tier === 'medium' ? 2.5 + rand() * 5 : 2 + rand() * 4,
        offset: rand() * Math.PI * 2,
      })
    }

    const staticParticles: Cluster['staticParticles'] = []
    for (let i = 0; i < staticCount; i++) {
      const angle = rand() * Math.PI * 2
      const r = Math.pow(rand(), 0.5) * radius * (0.25 + rand() * 0.55)
      staticParticles.push({
        lon: def.center[0] + Math.cos(angle) * r,
        lat: def.center[1] + Math.sin(angle) * r * 0.75,
        size: def.tier === 'major' ? 0.7 + rand() * 1.4 : def.tier === 'medium' ? 0.5 + rand() * 1 : 0.4 + rand() * 0.8,
      })
    }

    return {
      center: def.center,
      baseRadius: radius,
      particleCount: dynamicCount + staticCount,
      tier: def.tier,
      particles,
      staticParticles,
      phase: rand() * Math.PI * 2,
      brightness: 0.7 + rand() * 0.3,
    }
  })
}

function getProvinceData() {
  const entries = Object.entries(PROVINCE_DENSITY)
  const maxVal = Math.max(...entries.map(([, v]) => v))
  return entries.map(([name, value]) => ({ name, value, _max: maxVal }))
}

function getRadiusScale(tier: string, breath: number): number {
  const base = tier === 'major' ? 1 : tier === 'medium' ? 0.7 : 0.45
  return base * (0.72 + breath * 0.48)
}

function renderFrame(time: number, clusters: Cluster[]) {
  if (!chart) return

  const t = time / 1000

  const outerGlow: any[] = []
  const midRing: any[] = []
  const innerRing: any[] = []
  const particles: any[] = []
  const brightCores: any[] = []

  clusters.forEach((cluster) => {
    const clusterBreath = (Math.sin(t * Math.PI + cluster.phase) + 1) / 2
    const baseR = cluster.tier === 'major' ? 34 : cluster.tier === 'medium' ? 24 : 16
    const outerR = baseR
    const midR = outerR * 0.62
    const innerR = outerR * 0.34
    const glowOpacity = 0.28 + clusterBreath * 0.52
    const coreOpacity = (0.6 + clusterBreath * 0.4) * cluster.brightness

    outerGlow.push({
      value: cluster.center,
      symbolSize: outerR * 2.6,
      itemStyle: {
        color: 'rgba(80, 220, 180, 0.06)',
        opacity: glowOpacity * 0.28,
        shadowBlur: 12 + clusterBreath * 8,
        shadowColor: 'rgba(80, 220, 180, 0.32)',
      },
    })
    midRing.push({
      value: cluster.center,
      symbolSize: midR * 2.1,
      itemStyle: {
        color: 'rgba(100, 240, 200, 0.12)',
        opacity: glowOpacity * 0.5,
        shadowBlur: 8 + clusterBreath * 6,
        shadowColor: 'rgba(100, 240, 200, 0.35)',
      },
    })
    innerRing.push({
      value: cluster.center,
      symbolSize: innerR * 2.0,
      itemStyle: {
        color: 'rgba(130, 255, 220, 0.2)',
        opacity: glowOpacity * 0.7,
        shadowBlur: 4 + clusterBreath * 4,
        shadowColor: 'rgba(130, 255, 220, 0.4)',
      },
    })

    cluster.particles.forEach((p) => {
      const pBreath = 0.5 + 0.5 * Math.sin(t * Math.PI + p.offset)
      particles.push({
        value: [p.lon, p.lat],
        symbolSize: p.size * pBreath * 2.4,
      })
    })

    brightCores.push({
      value: cluster.center,
      symbolSize: cluster.tier === 'major' ? 11 : cluster.tier === 'medium' ? 8 : 6,
      itemStyle: {
        color: '#E6FFF8',
        opacity: coreOpacity,
        shadowBlur: 16 + clusterBreath * 16,
        shadowColor: 'rgba(140, 255, 220, 0.95)',
      },
    })
  })

  chart.setOption({
    series: [
      { name: '省域密度' },
      { name: '外发光晕', data: outerGlow },
      { name: '中层圆环', data: midRing },
      { name: '内层圆环', data: innerRing },
      { name: '粒子点', data: particles },
      { name: '中心亮核', data: brightCores },
    ],
  }, { lazyUpdate: true })

  animationFrameId = requestAnimationFrame((ft) => renderFrame(ft, clusters))
}

function renderChart() {
  if (!chartRef.value) return

  const rect = chartRef.value.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) {
    setTimeout(renderChart, 100)
    return
  }

  if (chart) {
    chart.dispose()
    chart = null
  }
  if (animationFrameId !== null) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }

  chart = echarts.init(chartRef.value)
  echarts.registerMap('china', chinaGeoJson as any)

  const clusters = generateClusters()
  const staticGlowData = clusters.flatMap((c) =>
    c.staticParticles.map((p) => ({
      value: [p.lon, p.lat],
      symbolSize: p.size * 2.4,
    })),
  )
  const provinceData = getProvinceData()
  const maxDensity = Math.max(...provinceData.map((d) => d.value))

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      show: true,
      trigger: 'item',
      backgroundColor: 'rgba(10, 28, 24, 0.92)',
      borderColor: 'rgba(80, 200, 170, 0.35)',
      borderWidth: 1,
      padding: [8, 14],
      textStyle: { color: '#C8E8DE', fontSize: 12 },
      formatter: (params: any) => {
        if (params.seriesType === 'scatter' || params.seriesType === 'effectScatter' || params.seriesType === 'custom') return ''
        const name = params.name
        const val = params.value ?? 0
        return `<div style="font-weight:600;color:#7FEDD0;margin-bottom:4px">${name}</div><div>监测企业约 <b style="color:#4FD1B3">${val}</b> 家</div>`
      },
    },
    visualMap: {
      type: 'continuous',
      min: 0,
      max: maxDensity,
      left: 20,
      bottom: 20,
      show: false,
      inRange: {
        color: [
          'rgba(10, 28, 23, 0.0)',
          'rgba(20, 60, 50, 0.6)',
          'rgba(30, 100, 85, 0.7)',
          'rgba(50, 150, 125, 0.55)',
          'rgba(80, 200, 170, 0.45)',
        ],
      },
    },
    geo: [
      {
        map: 'china',
        roam: false,
        zoom: 1.18,
        center: [104.5, 36],
        zlevel: 0,
        itemStyle: {
          areaColor: 'rgba(8, 22, 18, 0.0)',
          borderColor: 'rgba(0,0,0,0)',
          borderWidth: 0,
        },
        emphasis: { disabled: true },
        select: { disabled: true },
      },
    ],
    series: [
      {
        name: '省域密度',
        type: 'map',
        map: 'china',
        roam: false,
        zoom: 1.18,
        center: [104.5, 36],
        zlevel: 1,
        label: { show: false },
        itemStyle: {
          areaColor: 'rgba(12, 30, 25, 0.95)',
          borderColor: 'rgba(80, 200, 170, 0.12)',
          borderWidth: 0.8,
          shadowColor: 'rgba(0, 0, 0, 0.3)',
          shadowBlur: 8,
          shadowOffsetY: 4,
        },
        emphasis: {
          disabled: false,
          itemStyle: {
            areaColor: 'rgba(60, 170, 145, 0.35)',
            borderColor: 'rgba(120, 230, 200, 0.7)',
            borderWidth: 1.5,
            shadowColor: 'rgba(80, 210, 180, 0.5)',
            shadowBlur: 20,
          },
          label: { show: false },
        },
        select: { disabled: true },
        data: provinceData,
      },
      {
        name: '外发光晕',
        type: 'scatter',
        coordinateSystem: 'geo',
        geoIndex: 0,
        data: [],
        zlevel: 2,
        silent: true,
        symbol: 'circle',
        symbolSize: 20,
        itemStyle: {
          color: 'rgba(80, 220, 180, 0.12)',
          shadowBlur: 28,
          shadowColor: 'rgba(80, 220, 180, 0.55)',
          opacity: 0.85,
        },
      },
      {
        name: '中层圆环',
        type: 'scatter',
        coordinateSystem: 'geo',
        geoIndex: 0,
        data: [],
        zlevel: 3,
        silent: true,
        symbol: 'circle',
        symbolSize: 14,
        itemStyle: {
          color: 'rgba(100, 240, 200, 0.22)',
          shadowBlur: 20,
          shadowColor: 'rgba(100, 240, 200, 0.5)',
          opacity: 0.9,
        },
      },
      {
        name: '内层圆环',
        type: 'scatter',
        coordinateSystem: 'geo',
        geoIndex: 0,
        data: [],
        zlevel: 4,
        silent: true,
        symbol: 'circle',
        symbolSize: 10,
        itemStyle: {
          color: 'rgba(130, 255, 220, 0.32)',
          shadowBlur: 14,
          shadowColor: 'rgba(130, 255, 220, 0.55)',
          opacity: 0.92,
        },
      },
      {
        name: '静态微光',
        type: 'scatter',
        coordinateSystem: 'geo',
        geoIndex: 0,
        data: staticGlowData,
        zlevel: 4,
        silent: true,
        symbol: 'circle',
        itemStyle: {
          color: 'rgba(110, 230, 195, 0.1)',
          shadowBlur: 0,
          shadowColor: 'rgba(100, 230, 190, 0.2)',
          opacity: 0.08,
        },
      },
      {
        name: '粒子点',
        type: 'scatter',
        coordinateSystem: 'geo',
        geoIndex: 0,
        data: [],
        zlevel: 5,
        silent: true,
        symbol: 'circle',
        symbolSize: 3,
        itemStyle: {
          color: 'rgba(210, 255, 245, 0.88)',
          shadowBlur: 14,
          shadowColor: 'rgba(120, 255, 215, 0.95)',
          opacity: 0.92,
        },
      },
      {
        name: '中心亮核',
        type: 'scatter',
        coordinateSystem: 'geo',
        geoIndex: 0,
        data: [],
        zlevel: 6,
        silent: true,
        symbol: 'circle',
        symbolSize: 5,
        itemStyle: {
          color: '#E6FFF8',
          shadowBlur: 18,
          shadowColor: 'rgba(140, 255, 220, 0.95)',
          opacity: 1,
        },
      },
    ],
  }

  chart.setOption(option)
  animationFrameId = requestAnimationFrame((t) => renderFrame(t, clusters))
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
  if (animationFrameId !== null) {
    cancelAnimationFrame(animationFrameId)
  }
  chart?.dispose()
  chart = null
})

watch(() => props.companyCount, () => {
  renderChart()
})
</script>

<style scoped>
.china-map-card {
  position: relative;
  width: 100%;
  height: 460px;
  border-radius: 24px;
  overflow: hidden;
  background:
    radial-gradient(ellipse at 30% 20%, rgba(40, 90, 75, 0.25) 0%, transparent 55%),
    radial-gradient(ellipse at 70% 80%, rgba(30, 80, 65, 0.2) 0%, transparent 50%),
    linear-gradient(135deg, #071511 0%, #0C241E 40%, #0A1F1A 100%);
  box-shadow:
    0 20px 60px -20px rgba(8, 16, 14, 0.6),
    0 8px 28px -10px rgba(58, 122, 110, 0.25),
    inset 0 1px 0 rgba(100, 200, 180, 0.08),
    inset 0 -1px 0 rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(80, 180, 160, 0.12);
}

.map-glow {
  position: absolute;
  inset: -2px;
  border-radius: 26px;
  pointer-events: none;
  z-index: 0;
  box-shadow:
    0 0 80px rgba(60, 180, 150, 0.08),
    0 0 160px rgba(40, 140, 120, 0.05);
}

.map-chart {
  position: relative;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.map-stat-card {
  position: absolute;
  bottom: 18px;
  left: 18px;
  background: rgba(8, 22, 18, 0.82);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  padding: 14px 20px;
  border-radius: 16px;
  border: 1px solid rgba(100, 200, 170, 0.22);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.4),
    0 0 20px rgba(60, 180, 150, 0.1);
  min-width: 170px;
  z-index: 10;
}

.stat-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: rgba(180, 220, 200, 0.85);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 8px;
  font-family: 'Inter', 'HarmonyOS Sans SC', sans-serif;
}

.pulse-dot {
  position: relative;
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.pulse-core {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, #E6FFF8 0%, #7FFFCC 40%, #3DE8A0 100%);
  box-shadow:
    0 0 6px rgba(100, 255, 200, 0.9),
    0 0 12px rgba(80, 240, 180, 0.6),
    0 0 20px rgba(60, 220, 160, 0.3);
  animation: corePulse 2s ease-in-out infinite;
  z-index: 4;
}

.pulse-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  border-radius: 50%;
  border: 1.5px solid rgba(100, 255, 200, 0.6);
  transform: translate(-50%, -50%);
  animation: ringBreathe 2.5s ease-out infinite;
}

.ring-1 {
  width: 10px;
  height: 10px;
  animation-delay: 0s;
  border-color: rgba(120, 255, 210, 0.5);
}

.ring-2 {
  width: 14px;
  height: 14px;
  animation-delay: 0.6s;
  border-color: rgba(100, 240, 195, 0.35);
}

.ring-3 {
  width: 18px;
  height: 18px;
  animation-delay: 1.2s;
  border-color: rgba(80, 220, 180, 0.2);
}

@keyframes corePulse {
  0%, 100% {
    transform: translate(-50%, -50%) scale(1);
    box-shadow:
      0 0 6px rgba(100, 255, 200, 0.9),
      0 0 12px rgba(80, 240, 180, 0.6),
      0 0 20px rgba(60, 220, 160, 0.3);
  }
  50% {
    transform: translate(-50%, -50%) scale(1.15);
    box-shadow:
      0 0 8px rgba(120, 255, 210, 1),
      0 0 18px rgba(100, 250, 200, 0.75),
      0 0 30px rgba(80, 230, 180, 0.45);
  }
}

@keyframes ringBreathe {
  0% {
    width: 100%;
    height: 100%;
    opacity: 0.8;
    border-width: 1.5px;
  }
  100% {
    width: 280%;
    height: 280%;
    opacity: 0;
    border-width: 0.5px;
  }
}

.stat-value {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.stat-number {
  font-family: 'JetBrains Mono', 'SF Mono', monospace;
  font-size: 24px;
  font-weight: 700;
  color: #E8F7F2;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
  text-shadow: 0 0 20px rgba(80, 210, 180, 0.3);
}

.stat-unit {
  font-size: 13px;
  color: rgba(160, 200, 180, 0.75);
  font-weight: 500;
}

@media (max-width: 960px) {
  .china-map-card {
    height: 380px;
  }
}
</style>
