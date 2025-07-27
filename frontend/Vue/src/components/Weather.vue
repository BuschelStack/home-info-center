<template>
  <section class="column" id="weather">
    <div class="section-heading-container">
      <div class="section-heading-row">
        <div class="section-heading">Wetter</div>
        <div class="section-time">{{ lastUpdate }}</div>
      </div>
    </div>
    <div id="weather-content">
      <div v-if="loading" class="loader">
        <span class="spinner"></span>
        Daten werden geladen…
      </div>
      <div v-else-if="error" class="error">Fehler beim Laden des Wetters</div>
      <template v-else>
        <div v-if="(!weatherDaily.length && !Object.keys(weatherHourly).length)" class="no-data">
          Keine Daten vorhanden
        </div>
        <template v-else>
            <div class="calendar-date">4-Tage-Vorhersage</div>
            <ul class="weather-daily">
            <li v-for="day in weatherDaily" :key="day.tag" class="weather-daily-item">
              <div class="weather-daily-icon">
              <i :class="['wi', iconMap[extractWeatherCode(day.icon)] || 'wi-na']" aria-hidden="true"></i>
              </div>
              <div class="weather-daily-info">
              <div class="weather-daily-date"><strong>{{ formatGermanDateWithWeekday(day.tag, true) }}</strong></div>
              <div class="weather-daily-desc">{{ day.beschreibung }}, {{ day.temp_min }}–{{ day.temp_max }} °C</div>
              </div>
            </li>
            </ul>
          <div class="weather-grid">
            <div v-for="(stunden, tag) in weatherHourly" :key="tag">
              <div class="calendar-date">{{ formatGermanDateWithWeekday(tag, true) }}</div>
              <ul class="weather-hour-list">
                <div class="weather-hour-box" v-for="item in stunden" :key="item.zeit + item.beschreibung">
                  <div class="weather-time">{{ item.zeit }}</div>
                  <i :class="['wi', iconMap[extractWeatherCode(item.icon)] || 'wi-na']" aria-hidden="true"></i>
                  <div class="weather-temp">{{ Math.round(item.temperatur) }} °C</div>
                  <div class="weather-desc">{{ item.beschreibung }}</div>
                </div>
              </ul>
            </div>
          </div>
        </template>
      </template>
    </div>
  </section>
</template>

<script setup>

import { computed } from 'vue'
import { formatGermanDateWithWeekday } from '../utils/dateUtils'
import { iconMap }  from '/src/utils/icon-map.js';
import { useVersionedQuery } from '../composables/useVersionedQuery'

function extractWeatherCode(iconUrl) {
  const match = iconUrl ? iconUrl.match(/\/(\d{2}[dn])@/) : null
  return match ? match[1] : ''
}

const { data, isLoading, error } = useVersionedQuery({
  versionUrl: '/api/weather-version',
  dataUrl: '/api/weather',
  queryKey: 'weather',
  select: d => d
})

const weatherDaily = computed(() => data.value?.daily_weather || [])

// Wetterstunden: Heute zuerst, dann morgen, dann Rest
const weatherHourly = computed(() => {
  const wh = data.value?.weekly_weather || {};
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const tomorrow = new Date(today);
  tomorrow.setDate(today.getDate() + 1);
  const todayKey = Object.keys(wh).find(k => {
    const d = new Date(k);
    d.setHours(0, 0, 0, 0);
    return d.getTime() === today.getTime();
  });
  const tomorrowKey = Object.keys(wh).find(k => {
    const d = new Date(k);
    d.setHours(0, 0, 0, 0);
    return d.getTime() === tomorrow.getTime();
  });
  const restKeys = Object.keys(wh).filter(k => k !== todayKey && k !== tomorrowKey);
  const ordered = {};
  if (todayKey) ordered[todayKey] = wh[todayKey];
  if (tomorrowKey) ordered[tomorrowKey] = wh[tomorrowKey];
  for (const k of restKeys) ordered[k] = wh[k];
  return ordered;
});
const lastUpdate = computed(() => {
  if (!data.value) return '–'
  return new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
})
const loading = isLoading
</script>

