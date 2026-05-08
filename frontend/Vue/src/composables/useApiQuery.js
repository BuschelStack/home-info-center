/**
 * Thin wrapper around `useQuery` that fetches via our ETag-aware api client.
 *
 * Polling falls back to a 60 s interval; the SSE stream invalidates the cache
 * sooner when the backend announces an update.
 */
import { useQuery } from '@tanstack/vue-query'
import { fetchJson } from '../utils/api'

export function useApiQuery(key, url, options = {}) {
  return useQuery({
    queryKey: Array.isArray(key) ? key : [key],
    queryFn: ({ signal }) => fetchJson(url, { signal }),
    staleTime: 30_000,
    refetchInterval: options.refetchInterval ?? 60_000,
    refetchOnWindowFocus: false,
    retry: 2,
    ...options,
  })
}
