<template>
  <section class="column" id="appointments">
    <div class="section-heading-container">
      <div class="section-heading-row">
        <div class="section-heading">Termine</div>
        <div class="section-time">{{ lastUpdate }}</div>
      </div>
    </div>
    <div id="appointments-content">
      <div v-if="isLoading" class="loader">
        <span class="spinner" aria-hidden="true"></span>
        Daten werden geladen…
      </div>
      <div v-else-if="error" class="error">Fehler beim Laden der Termine</div>
      <template v-else>
        <div v-if="!sortedDates.length" class="no-data">Keine Daten vorhanden</div>
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
import { formatGermanDateWithWeekday } from '../utils/dateUtils.js'
import { useApiQuery } from '../composables/useApiQuery.js'
import { fetchJson } from '../utils/api.js'

const calendarMap = ref({})

function normalize(str) {
  return String(str || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^\w]/g, '')
    .toLowerCase()
}

function calendarClass(event) {
  const map = calendarMap.value
  let calName = event.calendar
  if (Array.isArray(calName)) calName = calName[0]
  if (typeof calName === 'object' && calName !== null) calName = calName.name || ''
  const norm = normalize(calName)
  if (norm && Object.keys(map).length) {
    const found = Object.keys(map).find((key) => normalize(key) === norm)
    if (found) return map[found]
  }
  return 'calendar-home'
}

function eventTime(event) {
  if (event.start_time) {
    return event.end_time ? `${event.start_time} – ${event.end_time}` : event.start_time
  }
  return '(ganztägig)'
}

onMounted(async () => {
  try {
    const calendars = await fetchJson('/api/calendars')
    const map = {}
    calendars.forEach((cal) => {
      if (cal.name && cal.class) map[cal.name] = cal.class
    })
    calendarMap.value = map
  } catch {
    calendarMap.value = {}
  }
})

const { data, isLoading, error, dataUpdatedAt } = useApiQuery('events', '/api/events')

const appointments = computed(() => data.value?.data || {})
const sortedDates = computed(() =>
  Object.keys(appointments.value).sort((a, b) => new Date(a) - new Date(b))
)
const lastUpdate = computed(() =>
  dataUpdatedAt.value
    ? new Date(dataUpdatedAt.value).toLocaleTimeString('de-DE', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })
    : '–'
)
</script>
