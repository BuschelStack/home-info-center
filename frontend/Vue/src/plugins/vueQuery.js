import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'

// QueryClient global konfigurieren
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 1000 * 60, // 1 Minute
    },
  },
})

export function installVueQuery(app) {
  app.use(VueQueryPlugin, { queryClient })
}
