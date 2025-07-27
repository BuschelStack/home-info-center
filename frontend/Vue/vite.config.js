import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  base: './',
  plugins: [vue()],
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': 'http://localhost:8080'
    }
  }
})
