import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 2,
      staleTime: 30_000,
    },
  },
})

export function installVueQuery(app) {
  app.use(VueQueryPlugin, { queryClient })
}
