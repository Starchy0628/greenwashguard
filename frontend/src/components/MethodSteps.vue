<template>
  <section class="method-section" id="method-section" ref="sectionRef">
    <div class="method-container">
      <SectionTitle>
        方法与数据说明
      </SectionTitle>
      
      <!-- 流程步骤卡片 -->
      <div class="method-flow">
        <div class="flow-card flow-card-1">
          <div class="flow-icon">
            <IconFilter :size="22" />
          </div>
          <div class="flow-title">语句切分过滤</div>
          <div class="flow-desc">抓取年报MD&A章节，按句切分，关键词预过滤环保相关语句</div>
        </div>
        
        <div class="flow-arrow">
          <div class="arrow-circle">
            <IconArrowRight :size="16" />
          </div>
        </div>
        
        <div class="flow-card flow-card-2">
          <div class="flow-icon">
            <IconGitMerge :size="22" />
          </div>
          <div class="flow-title">三模型集成投票</div>
          <div class="flow-desc">Deepseek、Qwen、GLM 独立判别，多数票确权，分歧样本转人工复核</div>
          <div class="voting-fanin">
            <div class="fanin-row">
              <div class="fanin-model">
                <div class="fanin-dot fs-deepseek"></div>
                <span class="fanin-label">Deepseek</span>
              </div>
              <div class="fanin-arrow">→</div>
              <div class="fanin-model">
                <div class="fanin-dot fs-qwen"></div>
                <span class="fanin-label">Qwen</span>
              </div>
              <div class="fanin-arrow">→</div>
              <div class="fanin-model">
                <div class="fanin-dot fs-glm"></div>
                <span class="fanin-label">GLM</span>
              </div>
            </div>
            <div class="fanin-converge">
              <svg viewBox="0 0 200 40" class="fanin-svg">
                <line x1="10" y1="5" x2="100" y2="35" stroke="rgba(58, 122, 110, 0.35)" stroke-width="2" stroke-dasharray="4,2"/>
                <line x1="100" y1="5" x2="100" y2="35" stroke="rgba(58, 122, 110, 0.35)" stroke-width="2" stroke-dasharray="4,2"/>
                <line x1="190" y1="5" x2="100" y2="35" stroke="rgba(58, 122, 110, 0.35)" stroke-width="2" stroke-dasharray="4,2"/>
              </svg>
              <div class="fanin-center">
                <IconCheck :size="14" />
              </div>
            </div>
          </div>
        </div>
        
        <div class="flow-arrow">
          <div class="arrow-circle">
            <IconArrowRight :size="16" />
          </div>
        </div>
        
        <div class="flow-card flow-card-3">
          <div class="flow-icon">
            <IconGauge :size="22" />
          </div>
          <div class="flow-title">语境情感打分</div>
          <div class="flow-desc">对描述性陈述做语境感知情感强度测度，而非简单关键词频次统计</div>
        </div>
        
        <div class="flow-arrow">
          <div class="arrow-circle">
            <IconArrowRight :size="16" />
          </div>
        </div>
        
        <div class="flow-card flow-card-4">
          <div class="flow-icon">
            <IconScale :size="22" />
          </div>
          <div class="flow-title">行业基准修正</div>
          <div class="flow-desc">语调分数减去行业年度中位数，计算GW指数，剔除行业间披露风格差异</div>
        </div>
      </div>
      
      <!-- 公式卡片 -->
      <div class="formula-panel">
        <div class="formula-card formula-card-main">
          <div class="formula-title">GW 指数计算公式</div>
          <div class="formula-body formula-piecewise">
            <div class="formula-piecewise-row">
              <span class="formula-gw">GW<sub>i,t</sub> =</span>
              <span class="formula-brace">{</span>
              <div class="formula-cases">
                <div class="formula-case">
                  <span class="formula-expr">Tone<sub>i,t</sub> − Median(Tone<sub>Ind,t</sub>)</span>
                  <span class="formula-condition">，Tone<sub>i,t</sub> &gt; Median(Tone<sub>Ind,t</sub>)</span>
                </div>
                <div class="formula-case">
                  <span class="formula-expr">0</span>
                  <span class="formula-condition">，其他情况</span>
                </div>
              </div>
            </div>
          </div>
          <div class="formula-params">
            <div class="param-item">
              <span class="param-name">GW<sub>i,t</sub>：</span>
              <span class="param-desc">企业 i 在年度 t 的漂绿指数，取值非负</span>
            </div>
            <div class="param-item">
              <span class="param-name">Tone<sub>i,t</sub>：</span>
              <span class="param-desc">企业 i 在年度 t 的环境语调（描述性语句平均情感分）</span>
            </div>
            <div class="param-item">
              <span class="param-name">Median(Tone<sub>Ind,t</sub>)：</span>
              <span class="param-desc">所属行业 Ind 在年度 t 的环境语调中位数</span>
            </div>
          </div>
        </div>
        <div class="formula-card formula-card-right">
          <div class="formula-title">环境语句分类关系</div>
          <div class="formula-body formula-relation">
            环境语句数 = 实质性语句数 + 描述性语句数 + 分歧语句数
          </div>
          <div class="formula-note">
            <p>· <b>实质性语句</b>：包含可量化、可验证的环境行动或绩效表述</p>
            <p>· <b>描述性语句</b>：定性、表态性的环境相关表述，用于计算语调</p>
            <p>· <b>分歧语句</b>：三模型投票存在分歧，需人工复核的语句</p>
          </div>
        </div>
      </div>
      
      <!-- 剔除说明 -->
      <div id="exclusion-note" class="exclusion-note">
        <div class="exclusion-icon">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        </div>
        <p class="exclusion-text">
          <b>样本筛选说明：</b>金融行业专用会计准则、经营模式、环境披露逻辑与实体企业差异较大，绿色信贷等业务易混淆企业自身环保行为，干扰 GW 指数测算；经营异常企业财务指标失真、环境披露动机扭曲，因此予以剔除。
        </p>
      </div>

      <!-- 合作伙伴logo -->
      <div class="partners-section">
        <div class="partners-title">技术支持 &amp; 数据来源</div>
        <div class="partners-row">
          <div class="partner-item">
            <img :src="deepseekLogo" alt="Deepseek" class="partner-logo" />
          </div>
          <div class="partner-item">
            <img :src="qwenLogo" alt="Qwen" class="partner-logo" />
          </div>
          <div class="partner-item">
            <img :src="glmLogo" alt="GLM" class="partner-logo" />
          </div>
          <div class="partner-item">
            <img :src="cnrdsLogo" alt="CNRDS" class="partner-logo" />
          </div>
          <div class="partner-item">
            <img :src="windLogo" alt="Wind" class="partner-logo" />
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SectionTitle from './SectionTitle.vue'
import { IconFilter, IconGitMerge, IconGauge, IconScale, IconArrowRight, IconCheck } from '@tabler/icons-vue'
import deepseekLogo from '../assets/images/partners/deepseek.svg'
import qwenLogo from '../assets/images/partners/qwen.svg'
import glmLogo from '../assets/images/partners/glm.svg'
import cnrdsLogo from '../assets/images/partners/cnrds.png'
import windLogo from '../assets/images/partners/wind.png'

const sectionRef = ref<HTMLElement | null>(null)
</script>

<style scoped>
.method-section {
  margin-bottom: 56px;
  position: relative;
}

.method-container {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 32px;
  border: 1px solid rgba(58, 122, 110, 0.08);
  box-shadow: 0 8px 32px rgba(58, 122, 110, 0.06);
}

/* 流程卡片 */
.method-flow {
  display: flex;
  align-items: stretch;
  gap: 0;
  margin-bottom: 28px;
}

.flow-card {
  flex: 1;
  border-radius: 16px;
  padding: 20px 18px;
  position: relative;
  transition: all 0.3s ease;
}

.flow-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(58, 122, 110, 0.1);
}

.flow-card-1 {
  background: rgba(58, 122, 110, 0.04);
}

.flow-card-2 {
  background: rgba(58, 122, 110, 0.06);
}

.flow-card-3 {
  background: rgba(58, 122, 110, 0.08);
}

.flow-card-4 {
  background: rgba(58, 122, 110, 0.10);
}

.flow-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
  color: var(--jade);
}

.flow-card-1 .flow-icon {
  background: rgba(58, 122, 110, 0.08);
}

.flow-card-2 .flow-icon {
  background: rgba(58, 122, 110, 0.12);
}

.flow-card-3 .flow-icon {
  background: rgba(58, 122, 110, 0.16);
}

.flow-card-4 .flow-icon {
  background: rgba(58, 122, 110, 0.20);
}

.flow-title {
  font-family: 'HarmonyOS Sans SC', 'Noto Sans SC', var(--font-sans);
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.flow-desc {
  font-family: 'HarmonyOS Sans SC', 'Noto Sans SC', var(--font-sans);
  font-size: 12px;
  font-weight: 400;
  color: var(--text-muted);
  line-height: 1.6;
}

/* 流程箭头 */
.flow-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 12px;
}

.arrow-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--jade);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  flex-shrink: 0;
}

/* 三模型投票扇入可视化 */
.voting-fanin {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px dashed rgba(58, 122, 110, 0.15);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.fanin-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  flex-wrap: wrap;
}

.fanin-model {
  display: flex;
  align-items: center;
  gap: 6px;
}

.fanin-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.fs-deepseek { background: #5B8FF9; }
.fs-qwen { background: #61DDAA; }
.fs-glm { background: #F6BD16; }

.fanin-label {
  font-family: 'HarmonyOS Sans SC', 'Noto Sans SC', var(--font-sans);
  font-size: 10px;
  color: var(--text-muted);
  font-weight: 500;
}

.fanin-arrow {
  font-size: 10px;
  color: rgba(58, 122, 110, 0.3);
  margin: 0 2px;
}

.fanin-converge {
  width: 100%;
  height: 36px;
  position: relative;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.fanin-svg {
  width: 100%;
  height: 100%;
}

.fanin-center {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--jade);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  z-index: 1;
}

/* 剔除说明 */
.exclusion-note {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 18px;
  background: rgba(58, 122, 110, 0.04);
  border: 1px solid rgba(58, 122, 110, 0.12);
  border-radius: 12px;
  margin-bottom: 8px;
  transition: box-shadow 0.3s ease;
}

.exclusion-icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(58, 122, 110, 0.12);
  color: var(--jade);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 1px;
}

.exclusion-text {
  margin: 0;
  font-size: 12px;
  line-height: 1.8;
  color: var(--text-secondary);
  font-family: var(--font-sans);
}

.exclusion-text b {
  color: var(--jade-dim);
  font-weight: 600;
}

/* 合作伙伴logo */
.partners-section {
  margin-top: 28px;
  padding-top: 28px;
  border-top: 1px solid rgba(58, 122, 110, 0.1);
}

.partners-title {
  font-family: 'HarmonyOS Sans SC', 'Noto Sans SC', var(--font-sans);
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
  text-align: center;
  margin-bottom: 20px;
  letter-spacing: 2px;
  text-transform: uppercase;
}

.partners-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.partner-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 8px;
}

.partner-logo {
  max-width: 100%;
  max-height: 32px;
  object-fit: contain;
  filter: grayscale(20%);
  opacity: 0.85;
  transition: all 0.3s ease;
}

.partner-item:hover .partner-logo {
  filter: grayscale(0%);
  opacity: 1;
  transform: translateY(-2px);
}

/* 公式卡片 */
.formula-panel {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  align-items: stretch;
}

.formula-card {
  padding: 20px 22px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(58, 122, 110, 0.1);
  border-radius: 14px;
}

.formula-card-main {
  padding: 24px 26px;
}

.formula-card-right {
  display: flex;
  flex-direction: column;
}

.formula-title {
  font-size: 12px;
  color: var(--jade);
  margin-bottom: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.formula-body {
  font-family: var(--font-mono);
  font-size: 14px;
  color: var(--text-primary);
  text-align: center;
  line-height: 1.8;
  font-weight: 600;
}

.formula-body sub {
  font-size: 10px;
  color: var(--text-muted);
}

.formula-relation {
  white-space: nowrap;
  overflow-x: auto;
  padding-bottom: 4px;
  font-size: 13px;
}

/* 分段函数样式 */
.formula-piecewise {
  padding: 8px 0 12px;
}

.formula-piecewise-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.formula-gw {
  font-size: 15px;
  color: var(--text-primary);
}

.formula-brace {
  font-size: 52px;
  font-weight: 300;
  color: var(--jade);
  line-height: 1;
  font-family: 'Times New Roman', serif;
}

.formula-cases {
  display: flex;
  flex-direction: column;
  gap: 10px;
  text-align: left;
}

.formula-case {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.formula-expr {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.formula-condition {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 400;
  font-family: var(--font-sans);
}

/* 参数说明 */
.formula-params {
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px dashed rgba(58, 122, 110, 0.15);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.param-item {
  display: flex;
  align-items: baseline;
  gap: 10px;
  font-size: 12px;
  line-height: 1.6;
}

.param-name {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--jade-dim);
  white-space: nowrap;
  min-width: 106px;
  text-align: left;
}

.param-desc {
  color: var(--text-secondary);
}

/* 分类说明 */
.formula-note {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed rgba(58, 122, 110, 0.15);
  text-align: left;
}

.formula-note p {
  margin: 4px 0;
  font-size: 11.5px;
  color: var(--text-secondary);
  line-height: 1.7;
  font-weight: 400;
  font-family: var(--font-sans);
}

.formula-note b {
  color: var(--jade-dim);
  font-weight: 600;
}

/* 响应式 */
@media (max-width: 960px) {
  .method-flow {
    flex-direction: column;
    gap: 16px;
  }
  
  .flow-arrow {
    padding: 0;
    height: 40px;
  }
  
  .arrow-circle {
    width: 32px;
    height: 32px;
  }
  
  .formula-panel {
    grid-template-columns: 1fr;
  }
  
  .voting-fanin {
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .fanin-lines {
    display: none;
  }
  
  .fanin-center {
    position: static;
    transform: none;
    margin-top: 4px;
  }
  
  .partners-row {
    flex-wrap: wrap;
    gap: 16px;
  }
  
  .partner-item {
    flex: 0 0 calc(33.333% - 12px);
  }
}

@media (max-width: 520px) {
  .method-container {
    padding: 20px;
  }
  
  .fanin-label {
    display: none;
  }
  
  .partner-item {
    flex: 0 0 calc(50% - 8px);
  }
  
  .partner-logo {
    max-height: 24px;
  }
}
</style>
