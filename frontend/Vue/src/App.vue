<template>
  <div :class="themeClass">
    <header v-show="isWideScreen" id="update-status">
      <div id="status-date">{{ formattedDate }}</div>
    </header>

    <main class="container">
      <CallList />
      <Appointments />
      <Weather />
    </main>

    <transition name="fade">
      <div v-if="!connection.isOnline" class="connection-lost-overlay" role="alert" aria-live="assertive">
        <div class="overlay-content">
          <span class="icon" aria-hidden="true">&#9888;</span>
          <h2>Verbindung verloren</h2>
          <p>Das Dashboard kann den Server nicht erreichen.</p>
          <div class="spinner" aria-hidden="true"></div>
          <p>Versuche {{ connection.failedChecks }} – wird automatisch neu verbunden …</p>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { getFormattedDate } from './utils/dateUtils.js'
import { loadConfig } from './utils/configLoader.js'
import { themeClass, startThemeInterval, stopThemeInterval } from './utils/themeUtils.js'
import { useConnectionStore } from './stores/connection.js'
import { useCacheStream } from './composables/useCacheStream.js'
import { useWakeLock } from './composables/useWakeLock.js'

import CallList from './components/CallList.vue'
import Appointments from './components/Appointments.vue'
import Weather from './components/Weather.vue'

const connection = useConnectionStore()

const formattedDate = ref(getFormattedDate(true))
const isWideScreen = ref(typeof window !== 'undefined' && window.innerWidth > 1400)

let dateIntervalId
function checkScreen() {
  isWideScreen.value = window.innerWidth > 1400
}

useCacheStream()
useWakeLock()

onMounted(async () => {
  await loadConfig()
  startThemeInterval()

  dateIntervalId = setInterval(() => {
    formattedDate.value = getFormattedDate(true)
  }, 60_000)

  window.addEventListener('resize', checkScreen)
  checkScreen()
})

onBeforeUnmount(() => {
  clearInterval(dateIntervalId)
  stopThemeInterval()
  window.removeEventListener('resize', checkScreen)
})
</script>

<style>
.connection-lost-overlay {
  position: fixed;
  inset: 0;
  background: rgba(30, 41, 59, 0.95);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  font-family: 'Segoe UI', Arial, sans-serif;
}

.overlay-content {
  text-align: center;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 1rem;
  padding: 2.5rem 1.9rem 1.9rem 1.9rem;
  box-shadow: 0 0.5rem 2rem 0 rgba(31, 38, 135, 0.37);
  min-width: 20rem;
}

.overlay-content .icon {
  font-size: 3rem;
  color: #fbbf24;
  display: block;
  margin-bottom: 0.67rem;
}

.overlay-content h2 {
  margin: 0 0 0.67rem 0;
  font-size: 2rem;
  color: #fbbf24;
}

.overlay-content p {
  margin: 0.67rem 0;
  font-size: 1.1rem;
}

.spinner {
  margin: 1.33rem auto 0.67rem auto;
  border: 0.4rem solid #f3f3f3;
  border-top: 0.4rem solid #3b82f6;
  border-radius: 50%;
  width: 3rem;
  height: 3rem;
  animation: spin 1s linear infinite;
  display: inline-block;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .spinner {
    animation: none;
  }
}
</style>
