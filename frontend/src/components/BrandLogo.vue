<template>
  <div class="brand-logo-wrapper" :style="{ width: `${size}px`, height: `${size}px` }">
    <svg :width="size" :height="size" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient :id="`logo-bg-${uid}`" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#0284c7" />
          <stop offset="45%" stop-color="#2563eb" />
          <stop offset="100%" stop-color="#1d4ed8" />
        </linearGradient>
        <linearGradient :id="`logo-top-${uid}`" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#bae6fd" />
          <stop offset="100%" stop-color="#38bdf8" />
        </linearGradient>
        <linearGradient :id="`logo-left-${uid}`" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#38bdf8" />
          <stop offset="100%" stop-color="#0284c7" />
        </linearGradient>
        <linearGradient :id="`logo-right-${uid}`" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#0369a1" />
          <stop offset="100%" stop-color="#0c4a6e" />
        </linearGradient>
        <filter :id="`logo-glow-${uid}`" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#2563eb" flood-opacity="0.35" />
        </filter>
      </defs>

      <!-- 圆角渐变底座 -->
      <rect width="48" height="48" rx="12" :fill="`url(#logo-bg-${uid})`" :filter="`url(#logo-glow-${uid})`" />
      <rect x="0.75" y="0.75" width="46.5" height="46.5" rx="11.25" stroke="#ffffff" stroke-opacity="0.25" stroke-width="1.5" />

      <!-- 3D 资产晶体节点立方体 -->
      <g transform="translate(0, 1)">
        <!-- 顶面 -->
        <path d="M24 10.5L37 17.5L24 24.5L11 17.5L24 10.5Z" :fill="`url(#logo-top-${uid})`" />
        <!-- 左侧面 -->
        <path d="M11 17.5L24 24.5V36.5L11 29.5V17.5Z" :fill="`url(#logo-left-${uid})`" />
        <!-- 右侧面 -->
        <path d="M24 24.5L37 17.5V29.5L24 36.5V24.5Z" :fill="`url(#logo-right-${uid})`" />

        <!-- 顶部芯片核 -->
        <path d="M24 14.5L30.5 18L24 21.5L17.5 18L24 14.5Z" fill="#ffffff" fill-opacity="0.95" />
        <circle cx="24" cy="18" r="2" fill="#0284c7" />

        <!-- 状态指示灯与网络连线 -->
        <circle cx="15.5" cy="24" r="1.5" fill="#34d399" />
        <circle cx="20" cy="29" r="1.5" fill="#67e8f9" />
        <circle cx="28" cy="29" r="1.5" fill="#93c5fd" />
        <circle cx="32.5" cy="24" r="1.5" fill="#a78bfa" />
        
        <path d="M15.5 24L20 29M28 29L32.5 24" stroke="#ffffff" stroke-width="1" stroke-opacity="0.6" stroke-linecap="round" />
      </g>
    </svg>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  size: {
    type: Number,
    default: 36
  }
})

const uid = ref(Math.random().toString(36).substring(2, 9))
</script>

<style scoped>
.brand-logo-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.brand-logo-wrapper:hover {
  transform: scale(1.06);
}
</style>
