<template>
  <div class="brand-logo" :class="size">
    <svg
      class="logo-icon"
      :width="size === 'large' ? 64 : size === 'medium' ? 44 : 32"
      :height="size === 'large' ? 64 : size === 'medium' ? 44 : 32"
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <!-- 眼睛外圈 -->
      <ellipse cx="32" cy="32" rx="28" ry="20" fill="url(#eyeGradient)" />
      <!-- 眼睛内圈 -->
      <ellipse cx="32" cy="32" rx="18" ry="13" fill="url(#irisGradient)" />
      <!-- 瞳孔 -->
      <circle cx="32" cy="32" r="6" fill="url(#pupilGradient)" />
      <!-- 瞳孔高光 -->
      <circle cx="30" cy="30" r="2" fill="white" opacity="0.6" />
      <!-- 星光 -->
      <g class="sparkle">
        <path d="M50 14 L52 12 L54 14 L52 16 Z" fill="#C9D17D" />
        <path d="M52 10 L53 13 L56 14 L53 15 L52 18 L51 15 L48 14 L51 13 Z" fill="#A8C686" />
      </g>
      <!-- 底部叶子 -->
      <path d="M18 48 Q22 44 26 46 Q24 50 20 52 Q18 51 18 48 Z" fill="#7DB9A0" />
      <!-- 渐变定义 -->
      <defs>
        <linearGradient id="eyeGradient" x1="4" y1="20" x2="60" y2="44" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#3A7A6E" />
          <stop offset="50%" stop-color="#5BA394" />
          <stop offset="100%" stop-color="#7DB9A0" />
        </linearGradient>
        <linearGradient id="irisGradient" x1="14" y1="22" x2="50" y2="42" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#2D5F55" />
          <stop offset="50%" stop-color="#3A7A6E" />
          <stop offset="100%" stop-color="#4A8B7E" />
        </linearGradient>
        <linearGradient id="pupilGradient" x1="26" y1="26" x2="38" y2="38" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#1A3D35" />
          <stop offset="100%" stop-color="#2D5F55" />
        </linearGradient>
      </defs>
    </svg>
    <div v-if="showText" class="logo-text" :class="{ 'with-sub': showSubtitle }">
      <span class="logo-cn">谛观</span>
      <span class="logo-en">
        <span class="en-green">Green</span><span class="en-olive">washGuard</span>
      </span>
      <span v-if="showSubtitle" class="logo-sub">{{ subtitle }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps({
  size: {
    type: String,
    default: 'medium',
    validator: (v: string) => ['small', 'medium', 'large'].includes(v),
  },
  showText: {
    type: Boolean,
    default: true,
  },
  showSubtitle: {
    type: Boolean,
    default: false,
  },
  subtitle: {
    type: String,
    default: '企业漂绿风险监测',
  },
})
</script>

<style scoped>
.brand-logo {
  display: flex;
  align-items: center;
  gap: 14px;
}

.logo-icon {
  flex-shrink: 0;
  filter: drop-shadow(0 2px 8px rgba(58, 122, 110, 0.25));
}

.sparkle {
  transform-origin: 52px 14px;
  animation: sparkle 3s ease-in-out infinite;
}

@keyframes sparkle {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(0.9); }
}

.logo-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.logo-cn {
  font-family: 'Noto Serif SC', 'SimSun', '宋体', serif;
  font-weight: 700;
  color: var(--jade);
  line-height: 1.1;
  letter-spacing: 4px;
}

.brand-logo.small .logo-cn {
  font-size: 16px;
}
.brand-logo.medium .logo-cn {
  font-size: 22px;
}
.brand-logo.large .logo-cn {
  font-size: 48px;
}

.logo-en {
  font-weight: 700;
  letter-spacing: 1px;
  line-height: 1.1;
}

.en-green {
  color: var(--jade);
}
.en-olive {
  color: #7DB9A0;
}

.brand-logo.small .logo-en {
  font-size: 12px;
}
.brand-logo.medium .logo-en {
  font-size: 14px;
}
.brand-logo.large .logo-en {
  font-size: 32px;
}

.logo-sub {
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 2px;
  margin-top: 2px;
  font-weight: 500;
}

.brand-logo.large .logo-sub {
  font-size: 14px;
  letter-spacing: 3px;
}

.with-sub {
  gap: 4px;
}
</style>
