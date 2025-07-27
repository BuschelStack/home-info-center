// src/utils/configLoader.js
import { ref } from 'vue'

export const config = ref(null)

export async function loadConfig() {
  if (!config.value) {
    config.value = await fetch('/api/config').then(r => r.json())
  }
  return config.value
}