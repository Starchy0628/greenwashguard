<template>
  <section id="hero-banner" class="hero-banner relative">
    <!-- 云海背景层 -->
    <div class="hero-bg-clouds" :style="{ transform: `translate3d(${px * 0.15}px, ${py * 0.15}px, 0)` }" aria-hidden="true"></div>
    <div class="hero-bg-overlay" aria-hidden="true"></div>

    <!-- Hero 主体：左右 55/45 分栏 -->
    <div class="hero-grid">
      <!-- 左侧内容区 (55%) -->
      <div class="hero-left">
        <!-- 主标题 -->
        <h1 class="hero-title">
          <BrandLogo :size="'large'" :show-text="false" />
          <div class="hero-title-text">
            <div class="hero-title-main">
              <span class="title-cn">谛观</span>
              <span class="title-en">
                <span class="en-green">Green</span><span class="en-olive">washGuard</span>
              </span>
            </div>
            <div class="hero-title-sub-wrap">
              <span class="shield-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                  <path d="M9 12l2 2 4-4"/>
                </svg>
              </span>
              <span class="hero-title-sub">企业漂绿风险监测平台</span>
              <span class="title-badge">PLATFORM</span>
            </div>
          </div>
        </h1>

        <!-- 副标题 -->
        <p class="hero-subtitle">
          <span class="subtitle-line">面向 A 股上市公司的年报 MD&amp;A 智能审查</span>
          <span class="subtitle-line">让每一句环境表述都经得起追问</span>
        </p>

        <!-- 模式切换 -->
        <div class="mode-tabs">
          <button
            :class="{ active: mode === 'single' }"
            @click="mode = 'single'"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="7"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            企业查询
          </button>
          <button
            :class="{ active: mode === 'pdf' }"
            @click="mode = 'pdf'"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            PDF 上传
          </button>
        </div>

        <!-- 搜索/上传区（卡片容器） -->
        <div class="hero-card">
          <!-- 单企业查询模式 -->
          <template v-if="mode === 'single'">
            <div class="search-row">
              <input
                v-model="query"
                @keyup.enter="doSearch()"
                type="text"
                placeholder="输入股票代码或企业名称，如 贵州茅台 / 600519"
              />
              <button class="search-btn" @click="doSearch()" :disabled="searching">
                <span v-if="!searching">查询</span>
                <span v-else class="loader"></span>
              </button>
            </div>
            <div class="search-hint">
              已在库企业将直接返回结果；试试输入
              <code @click="fillDemo('贵州茅台')">贵州茅台</code>
              查看缓存分析结果
            </div>
          </template>

          <!-- PDF 上传模式 -->
          <template v-else-if="mode === 'pdf'">
            <PdfUpload ref="pdfUploadRef" />
          </template>
        </div>

        <!-- CTA 按钮组 -->
        <div class="cta-row">
          <NButton
            class="cta-btn"
            :color="inkColor"
            size="large"
            :disabled="searching"
            @click="triggerDemo"
          >
            <template #icon>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
            </template>
            立即体验示例
          </NButton>
          <a class="cta-link" href="#method-section" @click.prevent="scrollToGrading">
            查看分级规则
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
              <line x1="5" y1="12" x2="19" y2="12"/>
              <polyline points="12 5 19 12 12 19"/>
            </svg>
          </a>
        </div>
      </div>

      <!-- 右侧视觉区 (45%) -->
      <div class="hero-right">
        <div class="hero-visual" :style="visualParallaxStyle">
          <ChinaMap :company-count="metrics.total_companies" />
        </div>
      </div>
    </div>

    <!-- Hero 下方：统计卡片 -->
    <div class="hero-stats">
      <StatCard
        label="分析语句数"
        :value="metrics.total_sentences"
        unit="句"
        description="累计三模型分类语句总量"
        tone="jade"
      />
      <StatCard
        label="覆盖企业数"
        :value="metrics.covered_companies"
        unit="家"
        description="剔除金融行业上市公司及经营异常上市公司"
        tone="ink"
        help-anchor="exclusion-note"
        help-tip="查看剔除原因"
      />
      <StatCard
        label="AI 准确率"
        :value="metrics.human_agreement"
        unit="%"
        :decimals="1"
        description="三模型投票与人工标注一致率"
        tone="gold"
      />
      <StatCard
        label="Fleiss' Kappa"
        :value="metrics.fleiss_kappa"
        :decimals="2"
        description="三模型分类一致性系数"
        tone="cinnabar"
      />
    </div>

    <!-- Hero 下方：结果展示区（业务逻辑保持不变） -->
    <div class="hero-result-area">
      <ToastNotification
        :message="toast.message"
        :type="toast.type"
        :visible="toast.visible"
        @done="toast = { message: '', visible: false }"
      />

      <!-- 单企业查询结果 -->
      <template v-if="mode === 'single'">
        <LiveSteps :active="liveActive" :current-step="liveStep" />

        <div v-if="isCached && currentResult && !liveActive" class="cached-notice">
          <span>当前显示为数据库缓存结果</span>
          <button class="refresh-btn" @click="refreshAnalysis" :disabled="searching">
            {{ searching ? '拉取中...' : '拉取最新一期' }}
          </button>
        </div>

        <ResultCard
          :result="currentResult"
          :is-watched="isWatched"
          @toggle-watch="toggleWatch"
        />
      </template>

      <!-- PDF 上传结果 -->
      <template v-else-if="mode === 'pdf' && pdfUploadRef">
        <LiveSteps
          :active="pdfUploadRef.analyzing"
          :current-step="pdfUploadRef.liveStep"
          :steps="pdfUploadRef.pdfSteps"
        />
        <ResultCard
          :result="pdfUploadRef.result"
          :is-watched="false"
          @toggle-watch="() => {}"
        />
      </template>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, reactive } from 'vue'
import { NButton } from 'naive-ui'
import { useWatchlistStore } from '../stores/watchlist'
import { dashboardApi, companiesApi } from '../api'
import LiveSteps from './LiveSteps.vue'
import ResultCard from './ResultCard.vue'
import ToastNotification from './ToastNotification.vue'
import PdfUpload from './PdfUpload.vue'
import BrandLogo from './BrandLogo.vue'
import ChinaMap from './ChinaMap.vue'
import StatCard from './StatCard.vue'
import { useParallax } from '../composables/useParallax'

// Naive UI 主题色：与设计系统的 jade 色对齐
const jadeColor = '#3A7A6E'
const inkColor = '#0A0A0A'

const watchlistStore = useWatchlistStore()
const mode = ref<'single' | 'pdf'>('single')
const query = ref('')
const searching = ref(false)
const liveActive = ref(false)
const liveStep = ref(-1)
const currentResult = ref<any>(null)
const isCached = ref(false)
const currentStockCode = ref('')
const toast = ref<{ message: string; type: 'info' | 'error'; visible: boolean }>({
  message: '',
  type: 'info',
  visible: false,
})
const pdfUploadRef = ref<any>(null)

// 仪表盘指标
const metrics = reactive({
  total_sentences: 0,
  total_companies: 5495,
  covered_companies: 5495,
  human_agreement: 94.22,
  fleiss_kappa: 0.84,
})

const isWatched = computed(() =>
  currentResult.value
    ? watchlistStore.isWatched(currentResult.value.company_id)
    : false
)

// 视差效果
const { offsetX, offsetY } = useParallax(0.08)
const px = offsetX
const py = offsetY

const visualParallaxStyle = computed(() => ({
  transform: `translate3d(${px.value * 0.6}px, ${py.value * 0.6}px, 0)`,
}))

function showToast(message: string, type: 'info' | 'error' = 'info') {
  toast.value = { message, type, visible: true }
}

async function doSearch(forceRefresh = false) {
  const q = query.value.trim()
  if (!q) {
    showToast('请输入股票代码或企业名称', 'error')
    return
  }

  searching.value = true
  liveActive.value = true
  liveStep.value = -1
  currentResult.value = null
  isCached.value = false

  try {
    const results = await companiesApi.search(q)
    if (!results.length) {
      showToast('查询错误：未找到该企业，请确认是否为A股上市公司', 'error')
      searching.value = false
      liveActive.value = false
      return
    }
    const found = results[0]
    currentStockCode.value = found.stock_code
    await streamAnalysis(found.stock_code, forceRefresh)
  } catch (err) {
    console.error(err)
    showToast('查询失败，请重试', 'error')
    searching.value = false
    liveActive.value = false
  }
}

async function streamAnalysis(stockCode: string, forceRefresh = false) {
  let eventSource: EventSource | null = null
  let hasBusinessError = false

  try {
    const url = new URL(`/api/analysis/stream`, window.location.origin)
    url.searchParams.set('stock_code', stockCode)
    url.searchParams.set('force_refresh', forceRefresh ? 'true' : 'false')
    eventSource = new EventSource(url.href)

    eventSource.addEventListener('status', (e) => {
      const data = JSON.parse(e.data)
      liveStep.value = stepIndex[data.phase] ?? -1
    })

    eventSource.addEventListener('progress', (e) => {
      const data = JSON.parse(e.data)
      liveStep.value = 2
    })

    eventSource.addEventListener('result', async (e) => {
      const data = JSON.parse(e.data)
      currentResult.value = data.result
      isCached.value = data.cached === true
      if (data.cached) showToast('已从数据库加载结果', 'info')

      liveActive.value = false
      searching.value = false
      eventSource?.close()
      scrollToResult()
    })

    eventSource.addEventListener('analysis_error', (e) => {
      try {
        const data = JSON.parse(e.data)
        hasBusinessError = true
        let msg = data.message
        if (data.fallback === 'pdf_upload') {
          msg += '（可切换到 PDF 上传模式手动分析）'
        }
        showToast(msg, 'error')
        if (!data.retryable) {
          liveActive.value = false
          searching.value = false
          eventSource?.close()
        }
      } catch (err) {
        hasBusinessError = true
        showToast('分析失败，请稍后重试', 'error')
        searching.value = false
        liveActive.value = false
        eventSource?.close()
      }
    })

    eventSource.addEventListener('done', (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.status === 'error' && !hasBusinessError) {
          showToast('分析未能完成，请稍后重试或上传 PDF', 'error')
        }
      } catch (err) {
        // ignore
      }
      liveActive.value = false
      searching.value = false
      eventSource?.close()
    })

    eventSource.onerror = () => {
      if (hasBusinessError) {
        return
      }
      showToast('网络连接失败，请检查网络后重试', 'error')
      searching.value = false
      liveActive.value = false
      eventSource?.close()
    }
  } catch (err) {
    console.error(err)
    showToast('打开分析连接失败', 'error')
    searching.value = false
    liveActive.value = false
    if (eventSource) eventSource.close()
  }
}

const stepIndex: Record<string, number> = {
  checking: 0,
  fetching: 1,
  segmenting: 2,
  classifying: 3,
  voting: 4,
  scoring: 4,
}

async function fetchAdditionalData(companyId: number) {
  try {
    const [sentenceData, trendData] = await Promise.all([
      companiesApi.getAllSentences(companyId),
      companiesApi.getTrend(companyId),
    ])

    if (currentResult.value) {
      currentResult.value.yearGroups = sentenceData.year_groups || []
      currentResult.value.summary = sentenceData.summary || {}
      currentResult.value.trend = trendData || []
    }
  } catch (err) {
    console.error('Failed to fetch additional data:', err)
  }
}

function toggleWatch() {
  if (!currentResult.value) return
  const id = currentResult.value.company_id
  const stockCode = currentResult.value.stock_code
  if (watchlistStore.isWatched(id)) {
    watchlistStore.remove(stockCode)
    showToast('已取消关注')
  } else {
    watchlistStore.add(stockCode)
    showToast('已加入关注列表')
  }
}

function scrollToResult() {
  nextTick(() => {
    const resultCard = document.querySelector('.result-card')
    if (resultCard) {
      resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  })
}

function refreshAnalysis() {
  if (!currentStockCode.value) return
  isCached.value = false
  doSearch(true)
}

function fillDemo(keyword: string) {
  query.value = keyword
  doSearch()
}

function triggerDemo() {
  fillDemo('贵州茅台')
}

function scrollToGrading() {
  const el = document.getElementById('method-section')
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function fetchMetrics() {
  try {
    const data = await dashboardApi.getMetrics()
    metrics.total_sentences = data.total_sentences || 0
    metrics.total_companies = data.total_companies || 0
    metrics.covered_companies = data.covered_companies || 0
    metrics.human_agreement = data.human_agreement ?? 94.22
    metrics.fleiss_kappa = data.fleiss_kappa ?? 0.84
  } catch (err) {
    console.error('Failed to load metrics:', err)
  }
}

onMounted(() => {
  watchlistStore.fetch()
  fetchMetrics()
})

// 暴露给父组件：点击 Top10 卡片 / 关注列表后自动填入并搜索
defineExpose({
  searchByKeyword(keyword: string) {
    query.value = keyword
    doSearch()
  },
})
</script>

<style scoped>
/* ===== Hero Banner 容器 ===== */
.hero-banner {
  position: relative;
  padding: 32px 0 0;
  margin-bottom: 64px;
}

/* 云海背景层 */
.hero-bg-clouds {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  background-image: url('https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Aerial%20view%20of%20beautiful%20clouds%20and%20mist%2C%20soft%20golden%20sunlight%20rays%20breaking%20through%2C%20ethereal%20atmosphere%2C%20serene%20sky%2C%20high%20resolution%2C%20cinematic%20photography&image_size=landscape_16_9');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  opacity: 0.35;
  z-index: -3;
  animation: fadeInClouds 1.5s ease-out forwards;
}

.hero-bg-overlay {
  position: absolute;
  inset: -20px -32px -20px -32px;
  background:
    radial-gradient(ellipse 60% 60% at 80% 0%, rgba(58, 122, 110, 0.1), transparent 60%),
    radial-gradient(ellipse 50% 50% at 20% 30%, rgba(201, 169, 97, 0.08), transparent 60%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.85) 0%, rgba(246, 248, 250, 0.95) 100%);
  border-radius: 0 0 32px 32px;
  z-index: -1;
}

@keyframes fadeInClouds {
  from { opacity: 0; }
  to { opacity: 0.35; }
}

/* ===== 左右分栏 55/45 ===== */
.hero-grid {
  display: grid;
  grid-template-columns: 55fr 45fr;
  gap: 48px;
  align-items: center;
  min-height: 480px;
}
@media (max-width: 960px) {
  .hero-grid {
    grid-template-columns: 1fr;
    gap: 32px;
  }
}

/* ===== 左侧 ===== */
.hero-left {
  display: flex;
  flex-direction: column;
  gap: 22px;
  animation: fadeUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.hero-title {
  margin: 0;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 20px;
  font-family: var(--font-sans);
  line-height: 1.1;
}
.hero-title-text {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.hero-title-main {
  display: flex;
  align-items: baseline;
  gap: 14px;
}
.title-cn {
  font-family: 'Noto Serif SC', 'SimSun', '宋体', serif;
  font-size: 48px;
  font-weight: 700;
  letter-spacing: 8px;
  color: var(--jade);
}
.title-en {
  font-weight: 700;
  letter-spacing: 1.5px;
  font-size: 28px;
}
.title-en .en-green {
  color: var(--jade);
}
.title-en .en-olive {
  color: #7DB9A0;
}
.hero-title-sub-wrap {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  position: relative;
  width: fit-content;
}
.shield-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  color: var(--jade);
}
.shield-icon svg {
  width: 100%;
  height: 100%;
}
.hero-title-sub {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 3px;
  position: relative;
  padding-bottom: 4px;
}
.hero-title-sub::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--jade) 0%, #7DB9A0 100%);
  border-radius: 2px;
}
.title-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1.5px;
  color: #FFFFFF;
  background: linear-gradient(135deg, var(--jade) 0%, #5BA394 100%);
  padding: 3px 10px;
  border-radius: 999px;
  box-shadow: 0 2px 6px rgba(58, 122, 110, 0.3);
}

.hero-subtitle {
  margin: 0;
  font-family: 'Noto Serif SC', 'SimSun', '宋体', 'Source Han Serif SC', serif;
  font-size: 15px;
  font-weight: 500;
  font-style: italic;
  line-height: 1.9;
  color: #04342C;
  max-width: 580px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.subtitle-line {
  display: block;
}

/* ===== 模式切换 ===== */
.mode-tabs {
  display: inline-flex;
  gap: 4px;
  background: #FFFFFF;
  border: 1px solid var(--panel-border);
  border-radius: 999px;
  padding: 4px;
  width: fit-content;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.mode-tabs button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  color: var(--text-muted);
  border: none;
  padding: 8px 18px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  font-family: var(--font-sans);
  border-radius: 999px;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.mode-tabs button.active {
  background: var(--jade);
  color: #FFFFFF;
  box-shadow: 0 2px 8px rgba(58, 122, 110, 0.28);
}
.mode-tabs button:not(.active):hover {
  color: var(--text-primary);
  background: var(--panel-bg-hover);
}

/* ===== 搜索/上传卡片容器 ===== */
.hero-card {
  background: #FFFFFF;
  border: 1px solid var(--panel-border);
  border-radius: 20px;
  padding: 20px;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 4px 12px rgba(15, 23, 42, 0.04);
  transition: box-shadow 0.3s ease, transform 0.3s ease;
}
.hero-card:hover {
  box-shadow:
    0 2px 4px rgba(15, 23, 42, 0.06),
    0 12px 28px rgba(15, 23, 42, 0.08);
}

.search-row {
  display: flex;
  gap: 8px;
}
.search-row input {
  flex: 1;
  background: #F6F8FA;
  color: var(--text-primary);
  border: 1px solid var(--panel-border);
  border-radius: 14px;
  padding: 14px 18px;
  font-size: 14px;
  font-family: var(--font-sans);
  transition: border-color 0.25s ease, background 0.25s ease, box-shadow 0.25s ease;
}
.search-row input::placeholder { color: var(--text-dim); }
.search-row input:focus {
  outline: none;
  border-color: var(--jade-dim);
  background: #FFFFFF;
  box-shadow: 0 0 0 3px rgba(58, 122, 110, 0.12);
}

.search-btn {
  background: var(--jade);
  color: #FFFFFF;
  border: none;
  border-radius: 14px;
  padding: 0 24px;
  font-weight: 600;
  cursor: pointer;
  font-size: 13px;
  font-family: var(--font-sans);
  transition: background 0.25s ease, transform 0.2s ease, box-shadow 0.2s ease;
  box-shadow: 0 2px 8px rgba(58, 122, 110, 0.24);
  min-width: 88px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.search-btn:hover:not(:disabled) {
  background: var(--jade-dim);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(58, 122, 110, 0.32);
}
.search-btn:active:not(:disabled) { transform: translateY(0); }
.search-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.search-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 12px;
  line-height: 1.6;
}
.search-hint code {
  background: var(--jade-soft);
  padding: 2px 10px;
  border-radius: 6px;
  color: var(--jade-dim);
  font-family: var(--font-mono);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}
.search-hint code:hover {
  background: var(--jade);
  color: #FFFFFF;
  border-color: var(--jade);
}

/* 加载小圆圈 */
.loader {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: #FFFFFF;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ===== CTA 按钮 ===== */
.cta-row {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}
.cta-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #0A0A0A 0%, #2D4A44 100%);
  color: #FFFFFF;
  border: none;
  border-radius: 14px;
  padding: 13px 24px;
  font-weight: 600;
  font-size: 13.5px;
  cursor: pointer;
  font-family: var(--font-sans);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.18);
}
.cta-btn:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.24);
}
.cta-btn:active:not(:disabled) { transform: translateY(0) scale(1); }
.cta-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.cta-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  font-family: var(--font-sans);
  padding: 10px 4px;
  transition: color 0.2s ease, gap 0.2s ease;
}
.cta-link:hover {
  color: var(--jade-dim);
  gap: 10px;
}

/* ===== 右侧视觉区 ===== */
.hero-right {
  position: relative;
  height: 100%;
  min-height: 460px;
  display: flex;
  align-items: center;
  animation: fadeIn 0.9s cubic-bezier(0.16, 1, 0.3, 1) 0.1s both;
}
.hero-visual {
  position: relative;
  width: 100%;
  height: 460px;
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: transform;
}
@media (max-width: 960px) {
  .hero-right { min-height: 380px; }
  .hero-visual { height: 380px; }
}

/* ===== 底部统计区 ===== */
.hero-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-top: 56px;
}
@media (max-width: 900px) {
  .hero-stats { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 520px) {
  .hero-stats { grid-template-columns: 1fr; }
}

/* ===== Hero 下方结果区 ===== */
.hero-result-area {
  margin-top: 56px;
}

.cached-notice {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--jade-soft);
  border: 1px solid rgba(58, 122, 110, 0.2);
  border-radius: 14px;
  padding: 12px 18px;
  margin-bottom: 20px;
  font-size: 13px;
  color: var(--text-secondary);
}
.refresh-btn {
  background: var(--jade);
  color: #FFFFFF;
  border: none;
  padding: 7px 16px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  font-family: var(--font-sans);
  white-space: nowrap;
  transition: background 0.25s ease, transform 0.2s ease;
}
.refresh-btn:hover:not(:disabled) {
  background: var(--jade-dim);
  transform: translateY(-1px);
}
.refresh-btn:disabled { opacity: .5; cursor: not-allowed; }

/* ===== 动画 ===== */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
