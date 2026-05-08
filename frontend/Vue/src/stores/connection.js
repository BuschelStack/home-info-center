/**
 * Connection store: tracks API health + drives reconnection UI.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useConnectionStore = defineStore('connection', () => {
  const isOnline = ref(true)
  const lastError = ref(null)
  const failedChecks = ref(0)
  const reconnectIn = ref(0)

  const status = computed(() => (isOnline.value ? 'online' : 'offline'))

  function setOnline() {
    if (!isOnline.value) {
      // Reconnected: caller can decide to reload or invalidate queries
      isOnline.value = true
    }
    failedChecks.value = 0
    reconnectIn.value = 0
    lastError.value = null
  }

  function setOffline(err) {
    isOnline.value = false
    lastError.value = err?.message ?? String(err)
    failedChecks.value += 1
  }

  function setReconnectIn(seconds) {
    reconnectIn.value = seconds
  }

  return { isOnline, lastError, failedChecks, reconnectIn, status, setOnline, setOffline, setReconnectIn }
})
