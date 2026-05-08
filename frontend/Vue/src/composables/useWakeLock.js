/**
 * Best-effort wake-lock so TVs / tablets do not dim while showing the dashboard.
 */
import { onBeforeUnmount, onMounted } from 'vue'

export function useWakeLock() {
  let lock = null

  async function request() {
    if (!('wakeLock' in navigator)) return
    try {
      lock = await navigator.wakeLock.request('screen')
      lock.addEventListener('release', () => {
        lock = null
      })
    } catch {
      // ignored – feature not granted
    }
  }

  function onVisibility() {
    if (document.visibilityState === 'visible' && !lock) request()
  }

  onMounted(() => {
    request()
    document.addEventListener('visibilitychange', onVisibility)
  })

  onBeforeUnmount(() => {
    document.removeEventListener('visibilitychange', onVisibility)
    lock?.release().catch(() => {})
  })
}
