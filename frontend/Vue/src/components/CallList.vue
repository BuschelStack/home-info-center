<template>
  <section class="column" id="calllist">
    <div class="section-heading-container">
      <div class="section-heading-row">
        <div class="section-heading">Anrufe</div>
        <div class="section-time">{{ lastUpdate }}</div>
      </div>
    </div>
    <div id="calllist-content">
      <div v-if="loading" class="loader">
        <span class="spinner"></span>
        Lade Anrufe…
      </div>
      <div v-else-if="error" class="error">Fehler beim Laden der Anrufe</div>
      <template v-else>
        <div v-if="!sortedTags.length" class="no-data">
          Keine Daten vorhanden
        </div>
        <template v-else>
          <div>
            <div v-for="tag in sortedTags" :key="tag">
              <div class="calendar-date">{{ formatGermanDateWithWeekday(tag, true) }}</div>
              <transition-group name="fade-list" tag="ul" class="call-list">
                <li
                  v-for="call in (callsData[tag] || [])"
                  :key="call.id || (call.date + call.name + call.called)"
                  :class="callTypeClass(call.type)"
                >
                  <span v-html="getCallIcon(call.type)"></span>
                  <span class="call-text">
                    {{ formatTime(call.date) }} | {{ call.name || call.caller || 'Unbekannt' }} | {{ call.called || '–' }}
                    <span v-if="call.duration && call.duration !== '–'"> ({{ formatDuration(call.duration) }})</span>
                  </span>
                </li>
              </transition-group>
            </div>
          </div>
        </template>
      </template>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useVersionedQuery } from '../composables/useVersionedQuery'
import { formatGermanDateWithWeekday } from '../utils/dateUtils'

function callTypeClass(type) {
  if (type === '1') return 'call-type-1'
  if (type === '2') return 'call-type-2'
  if (type === '3') return 'call-type-3'
  if (type === '11') return 'call-type-11'
  return 'call-type-other'
}
function getCallIcon(type) {
  const map = {
    '1': 'call-in.svg',
    '2': 'call-missed.svg',
    '3': 'call-out.svg',
    '11': 'voicemail.svg'
  }
  const filename = map[type] || 'call-other.svg'
  return `<img src="/icons/${filename}" class="call-icon" alt="" />`
}
function formatTime(dateStr) {
  if (!dateStr) return '–'
  const d = new Date(dateStr)
  if (isNaN(d)) return '–'
  return d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
}
function formatDuration(durationStr) {
  const [hStr, mStr] = durationStr.split(':')
  const hours = parseInt(hStr, 10)
  const minutes = parseInt(mStr, 10)
  if (isNaN(hours) || isNaN(minutes)) return durationStr
  const parts = []
  if (hours > 0) parts.push(hours === 1 ? '1 Stunde' : `${hours} Stunden`)
  if (minutes > 0) parts.push(`${minutes} Minute${minutes === 1 ? '' : 'n'}`)
  if (parts.length === 0) return '0 Minuten'
  return parts.join(' ')
}

const { data, isLoading, error } = useVersionedQuery({
  versionUrl: '/api/calls-version',
  dataUrl: '/api/calls',
  queryKey: 'calls',
  select: d => d.calls
})

const callsData = computed(() => data.value || {})
const sortedTags = computed(() => Object.keys(callsData.value).sort((a, b) => new Date(b) - new Date(a)))
const lastUpdate = computed(() => {
  if (!data.value) return '–'
  return new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
})
const loading = isLoading
</script>

<style>
/* Bereichsspezifische Styles können hier ergänzt werden */
</style>
