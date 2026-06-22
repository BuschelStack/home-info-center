/**
 * Composable that listens to the backend SSE stream and invalidates
 * Vue Query caches when the server announces an update.
 *
 * On connection loss it marks the connection store offline and keeps
 * retrying via EventSource reconnect (every RECONNECT_DELAY_MS) until
 * the stream is back.
 */
import { onBeforeUnmount, onMounted } from 'vue'
import { useQueryClient } from '@tanstack/vue-query'
import { useConnectionStore } from '../stores/connection'

const STREAM_URL = '/api/stream'
const RECONNECT_DELAY_MS = 5000

export function useCacheStream() {
  const queryClient = useQueryClient()
  const connection = useConnectionStore()

  let source = null
  let reconnectTimer = null
  let stopped = false

  function connect() {
    if (typeof EventSource === 'undefined') return
    source = new EventSource(STREAM_URL)

    source.onopen = () => {
      connection.setOnline()
    }

    source.addEventListener('cache-updated', (ev) => {
      try {
        const { name } = JSON.parse(ev.data)
        if (name) queryClient.invalidateQueries({ queryKey: [name] })
      } catch {
        // ignore malformed
      }
    })

    source.onerror = () => {
      connection.setOffline(new Error('SSE connection lost'))
      source?.close()
      source = null
      if (!stopped) {
        reconnectTimer = setTimeout(connect, RECONNECT_DELAY_MS)
      }
    }
  }

  onMounted(() => {
    stopped = false
    connect()
  })

  onBeforeUnmount(() => {
    stopped = true
    if (reconnectTimer) clearTimeout(reconnectTimer)
    source?.close()
  })
}
