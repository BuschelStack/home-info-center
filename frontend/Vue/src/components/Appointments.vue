<template>
  <section class="column" id="appointments">
    <div class="section-heading-container">
      <div class="section-heading-row">
        <div class="section-heading">Termine</div>
        <div class="section-time">{{ lastUpdate }}</div>
      </div>
    </div>
    <div id="appointments-content">
      <div v-if="loading" class="loader">
        <span class="spinner"></span>
        Daten werden geladen…
      </div>
      <div v-else-if="error" class="error">Fehler beim Laden der Termine</div>
      <template v-else>
        <div v-if="!sortedDates.length" class="no-data">
          Keine Daten vorhanden
        </div>
        <template v-else>
            <div v-for="date in sortedDates" :key="date" class="calendar-date-group">
              <div class="calendar-date">{{ formatGermanDateWithWeekday(date) }}</div>
              <div
                v-for="event in appointments[date]"
                :key="event.title + event.start_time"
                :class="['calendar-event', calendarClass(event)]"
            >
              <div class="event-row">
              <span class="event-time">{{ eventTime(event) }}</span>
              <span class="event-title">{{ event.title || '(kein Titel)' }}</span>
              </div>
            </div>
            </div>
        </template>
      </template>
    </div>
  </section>
</template>

<script setup>


import { computed, ref, onMounted } from 'vue'
import { formatGermanDateWithWeekday } from '../utils/dateUtils'
import { useVersionedQuery } from '../composables/useVersionedQuery'

// Kalender-Definitionen dynamisch laden
const calendarMap = ref({})

async function loadCalendars() {
  try {
    const res = await fetch('/api/calendars', { cache: 'no-store' })
    if (!res.ok) throw new Error('Fehler beim Laden der Kalenderdefinitionen')
    const calendars = await res.json()
    // Erzeuge Map: Name → CSS-Klasse (oder nutze .class, .color etc.)
    const map = {}
    calendars.forEach(cal => {
      // z.B. { "name": "Familie", "class": "calendar-family" }
      if (cal.name && cal.class) map[cal.name] = cal.class
    })
    calendarMap.value = map
  } catch (e) {
    // Fallback: leere Map
    calendarMap.value = {}
  }
}

onMounted(loadCalendars)
function normalize(str) {
  // Unicode-Normalisierung, entferne Sonderzeichen/Umlaute/Leerzeichen
  return String(str || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // entferne diakritische Zeichen
    .replace(/[^\w]/g, '') // nur Buchstaben/Zahlen/Unterstrich
    .toLowerCase()
}

function calendarClass(event) {
  const map = calendarMap.value
  let calName = event.calendar
  if (Array.isArray(calName)) calName = calName[0]
  if (typeof calName === 'object' && calName !== null) calName = calName.name || ''
  const normCalName = normalize(calName)
  if (normCalName && Object.keys(map).length) {
    const found = Object.keys(map).find(
      key => normalize(key) === normCalName
    )
    if (found) return map[found]
  }
  return 'calendar-home'
}
function eventTime(event) {
  if (event.start_time)
    return event.end_time ? `${event.start_time} – ${event.end_time}` : event.start_time
  return '(ganztägig)'
}

const { data, isLoading, error } = useVersionedQuery({
  versionUrl: '/api/events-version',
  dataUrl: '/api/events',
  queryKey: 'events',
  select: d => d.data
})

const appointments = computed(() => data.value || {})
const sortedDates = computed(() => Object.keys(appointments.value).sort((a, b) => {
  const [da, ma, ya] = a.split('.')
  const [db, mb, yb] = b.split('.')
  return new Date(parseInt(ya), parseInt(ma) - 1, parseInt(da)) - new Date(parseInt(yb), parseInt(mb) - 1, parseInt(db))
}))
const lastUpdate = computed(() => {
  if (!data.value) return '–'
  return new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
})
const loading = isLoading
</script>

<style>
/* Bereichsspezifische Styles können hier ergänzt werden */
</style>
