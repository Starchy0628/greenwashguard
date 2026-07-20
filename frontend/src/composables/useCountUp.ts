import { ref, onMounted, onUnmounted, watch, type Ref } from 'vue'

export interface CountUpOptions {
  start?: number
  end: number | Ref<number>
  duration?: number
  decimals?: number
  triggerOnVisible?: boolean
}

export function useCountUp(options: CountUpOptions) {
  const {
    start = 0,
    end,
    duration = 1800,
    decimals = 0,
    triggerOnVisible = true,
  } = options

  const endRef = typeof end === 'number' ? ref(end) : end
  const current = ref(start)
  const display = ref(formatNumber(start, decimals))
  let rafId: number | null = null
  let observer: IntersectionObserver | null = null
  let triggered = false

  function formatNumber(value: number, dec: number): string {
    if (dec === 0) {
      return Math.round(value).toLocaleString('en-US')
    }
    return value.toFixed(dec)
  }

  function easeOutCubic(t: number): number {
    return 1 - Math.pow(1 - t, 3)
  }

  function animate(from: number, to: number) {
    if (rafId) cancelAnimationFrame(rafId)
    const startTime = performance.now()
    const tick = (now: number) => {
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)
      const eased = easeOutCubic(progress)
      const value = from + (to - from) * eased
      current.value = value
      display.value = formatNumber(value, decimals)
      if (progress < 1) {
        rafId = requestAnimationFrame(tick)
      }
    }
    rafId = requestAnimationFrame(tick)
  }

  function startAnimation() {
    if (triggered && endRef.value === 0) return
    triggered = true
    animate(current.value, endRef.value)
  }

  function reset() {
    if (rafId) cancelAnimationFrame(rafId)
    triggered = false
    current.value = start
    display.value = formatNumber(start, decimals)
  }

  function setupObserver(el: HTMLElement | null) {
    if (!triggerOnVisible || !el) {
      startAnimation()
      return
    }
    if (observer) observer.disconnect()
    observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            startAnimation()
            observer?.disconnect()
            observer = null
          }
        }
      },
      { threshold: 0.3 }
    )
    observer.observe(el)
  }

  watch(endRef, (newEnd) => {
    if (newEnd > 0) {
      startAnimation()
    }
  }, { immediate: true })

  onUnmounted(() => {
    if (rafId) cancelAnimationFrame(rafId)
    observer?.disconnect()
  })

  return {
    current,
    display,
    startAnimation,
    reset,
    setupObserver,
  }
}
