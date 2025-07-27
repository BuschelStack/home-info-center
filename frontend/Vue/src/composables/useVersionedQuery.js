import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { ref } from 'vue'

// Hilfsfunktion: Pollt nur die Version und triggert Daten-Reload
export function useVersionedQuery({
  versionUrl,
  dataUrl,
  queryKey,
  select,
  refetchInterval = 10000, // 10s
}) {
  const queryClient = useQueryClient()
  const lastVersion = ref(null)

  // Pollt nur die Version
  useQuery({
    queryKey: [queryKey, 'version'],
    queryFn: async () => {
      const res = await fetch(versionUrl)
      const data = await res.json()
      return data.version
    },
    refetchInterval,
    onSuccess: (version) => {
      // Wenn die Version sich ändert, Daten neu laden        
      if (lastVersion.value !== null && version !== lastVersion.value) {
        queryClient.invalidateQueries({ queryKey: [queryKey, 'data'] }, { refetchType: 'all' })
      }
      lastVersion.value = version
    },
    onError: (err) => {
      console.error('Version-Query Error:', err)
    }
  })

  // Holt die eigentlichen Daten
  const dataQuery = useQuery({
    queryKey: [queryKey, 'data'],
    queryFn: async () => {
      try {
        const res = await fetch(dataUrl)
        const data = await res.json()
        return select ? select(data) : data
      } catch (err) {
        console.error('Data-Query Error:', err)
        throw err
      }
    },
    staleTime: 0,
    refetchOnWindowFocus: false,
    onError: (err) => {
      console.error('Data-Query Error (useQuery):', err)
    }
  })

  return dataQuery
}
