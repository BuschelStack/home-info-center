<template>
  <div :class="themeClass">
    <div id="update-status" v-show="isWideScreen">
      <div id="status-date">{{ formattedDate }}</div>
    </div>
    <div class="container">
      <CallList />
      <Appointments />
      <Weather />
    </div>
    <!-- Overlay bei Verbindungsproblemen -->
    <div v-if="!apiOk" class="connection-lost-overlay">
      <div class="overlay-content">
        <span class="icon">&#9888;</span>
        <h2>Verbindung verloren</h2>
        <p>Das Dashboard kann keine Verbindung zum Server herstellen.</p>
        <div class="spinner"></div>
        <p>Neuer Verbindungsversuch in {{ countdown }} Sekunden ...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { getFormattedDate } from './utils/dateUtils.js'
import { loadConfig } from './utils/configLoader'

import CallList from './components/CallList.vue'
import Appointments from './components/Appointments.vue'
import Weather from './components/Weather.vue'

const formattedDate = ref(getFormattedDate(true))

let dateIntervalId

// Responsive: isWideScreen
const isWideScreen = ref(window.innerWidth > 1400)
function checkScreen() {
  isWideScreen.value = window.innerWidth > 1400
}


import { themeClass, startThemeInterval } from './utils/themeUtils.js'

onMounted(async () => {
  await loadConfig()     
  startThemeInterval() 

  dateIntervalId = setInterval(() => {
    formattedDate.value = getFormattedDate(true)
  }, 60 * 1000)

  checkApi()
  checkIntervalId = setInterval(() => {
    if (apiOk.value) {
      checkApi()
    }
  }, 10000) // alle 10 Sekunden, aber nur wenn Verbindung ok

  window.addEventListener('resize', checkScreen)
  checkScreen()
})

onBeforeUnmount(() => {
  clearInterval(dateIntervalId)
  clearInterval(checkIntervalId)
  clearInterval(countdownIntervalId)
  window.removeEventListener('resize', checkScreen)
})

// Verbindung prüfen
const apiOk = ref(true)
const countdown = ref(10)
let checkIntervalId
let countdownIntervalId

function checkApi() {
  fetch('/api/events', { cache: 'no-store' })
    .then(res => {
      if (!res.ok) throw new Error()
      if (!apiOk.value) {
        // Verbindung wurde gerade wiederhergestellt → Seite neu laden
        apiOk.value = true
        countdown.value = 10
        setTimeout(() => {
          window.location.reload()
        }, 200) // kleiner Delay, um State-Änderung zu ermöglichen (200 ms)
        return
      }
      apiOk.value = true
      countdown.value = 10
    })
    .catch(() => {
      apiOk.value = false
      startCountdown()
    })
}

function startCountdown() {
  clearInterval(countdownIntervalId)
  countdown.value = 10
  countdownIntervalId = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(countdownIntervalId)
      checkApi()
    }
  }, 1000)
}

</script>

<style>
/* Layout-spezifische Styles können hier ergänzt werden */


.connection-lost-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
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
  background: rgba(255,255,255,0.05);
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
  0% { transform: rotate(0deg);}
  100% { transform: rotate(360deg);}
}

</style>