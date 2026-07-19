import { ref, onMounted, onUnmounted } from 'vue'

/**
 * 视差滚动效果
 * 实现 Banner 区域轻微的深度感
 */
export function useParallax(strength = 0.15) {
  const offsetY = ref(0)
  const offsetX = ref(0)
  let rafId: number | null = null

  function onScroll() {
    if (rafId) cancelAnimationFrame(rafId)
    rafId = requestAnimationFrame(() => {
      offsetY.value = window.scrollY * strength
    })
  }

  function onMouseMove(e: MouseEvent) {
    if (rafId) cancelAnimationFrame(rafId)
    rafId = requestAnimationFrame(() => {
      const cx = window.innerWidth / 2
      const cy = window.innerHeight / 2
      offsetX.value = ((e.clientX - cx) / cx) * strength * 30
      offsetY.value = ((e.clientY - cy) / cy) * strength * 30 + window.scrollY * strength
    })
  }

  onMounted(() => {
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('mousemove', onMouseMove, { passive: true })
    onScroll()
  })

  onUnmounted(() => {
    if (rafId) cancelAnimationFrame(rafId)
    window.removeEventListener('scroll', onScroll)
    window.removeEventListener('mousemove', onMouseMove)
  })

  return { offsetX, offsetY }
}
