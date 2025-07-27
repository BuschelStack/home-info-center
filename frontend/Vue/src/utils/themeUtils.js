// src/utils/themeUtils.js
import { ref } from 'vue'
import { config } from './configLoader'

export const themeClass = ref('theme-day')

// Wie gelb/orange soll das Evening-Theme maximal werden? (0 = kein Gelb, 1 = sehr gelb)
const EVENING_INTENSITY = 0.7 // Wert zwischen 0 und 1


// Hilfsfunktion: 8-stellige Hex-Werte auf 6 Stellen kürzen
function normalizeHex(hex) {
  hex = hex.replace(/^#/, '');
  if (hex.length === 8) return '#' + hex.slice(0, 6);
  return '#' + hex;
}

// Basisfarben (Tag)
// Farben aus config (geladen aus .env des Backends)
// Die Farben werden jetzt dynamisch in updateTheme() geladen

// Hilfsfunktion: Hex nach RGB
function hexToRgb(hex) {
    hex = hex.replace(/^#/, '')
    if (hex.length === 3) {
        hex = hex.split('').map(x => x + x).join('')
    }
    const num = parseInt(hex, 16)
    return [(num >> 16) & 255, (num >> 8) & 255, num & 255]
}


function lerp(a, b, t) {
  return a + (b - a) * t
}
function lerpColor(rgbA, rgbB, t) {
  return [
    Math.round(lerp(rgbA[0], rgbB[0], t)),
    Math.round(lerp(rgbA[1], rgbB[1], t)),
    Math.round(lerp(rgbA[2], rgbB[2], t))
  ]
}
function rgbToHex(rgb) {
  return '#' + rgb.map(x => x.toString(16).padStart(2, '0')).join('')
}

function getSunTimes(date, lat, lon) {
  // Original Berechnung wie gehabt
  const zenith = 90.8333
  const D2R = Math.PI / 180
  const R2D = 180 / Math.PI
  const day = date.getDate()
  const month = date.getMonth() + 1
  const year = date.getFullYear()
  const N1 = Math.floor(275 * month / 9)
  const N2 = Math.floor((month + 9) / 12)
  const N3 = (1 + Math.floor((year - 4 * Math.floor(year / 4) + 2) / 3))
  const N = N1 - (N2 * N3) + day - 30
  const lngHour = lon / 15
  // Sonnenaufgang
  let t_rise = N + ((6 - lngHour) / 24)
  let M_rise = (0.9856 * t_rise) - 3.289
  let L_rise = M_rise + (1.916 * Math.sin(D2R * M_rise)) + (0.020 * Math.sin(2 * D2R * M_rise)) + 282.634
  L_rise = (L_rise + 360) % 360
  let RA_rise = R2D * Math.atan(0.91764 * Math.tan(D2R * L_rise))
  RA_rise = (RA_rise + 360) % 360
  let Lquadrant_rise  = Math.floor(L_rise/90) * 90
  let RAquadrant_rise = Math.floor(RA_rise/90) * 90
  RA_rise = RA_rise + (Lquadrant_rise - RAquadrant_rise)
  RA_rise = RA_rise / 15
  let sinDec_rise = 0.39782 * Math.sin(D2R * L_rise)
  let cosDec_rise = Math.cos(Math.asin(sinDec_rise))
  let cosH_rise = (Math.cos(D2R * zenith) - (sinDec_rise * Math.sin(D2R * lat))) / (cosDec_rise * Math.cos(D2R * lat))
  let H_rise = 360 - R2D * Math.acos(cosH_rise)
  H_rise = H_rise / 15
  let T_rise = H_rise + RA_rise - (0.06571 * t_rise) - 6.622
  let UT_rise = (T_rise - lngHour) % 24
  let sunrise = new Date(Date.UTC(year, month - 1, day))
  sunrise.setUTCHours(Math.floor(UT_rise), Math.floor((UT_rise % 1) * 60), 0, 0)
  // Sonnenuntergang
  let t_set = N + ((18 - lngHour) / 24)
  let M_set = (0.9856 * t_set) - 3.289
  let L_set = M_set + (1.916 * Math.sin(D2R * M_set)) + (0.020 * Math.sin(2 * D2R * M_set)) + 282.634
  L_set = (L_set + 360) % 360
  let RA_set = R2D * Math.atan(0.91764 * Math.tan(D2R * L_set))
  RA_set = (RA_set + 360) % 360
  let Lquadrant_set  = Math.floor(L_set/90) * 90
  let RAquadrant_set = Math.floor(RA_set/90) * 90
  RA_set = RA_set + (Lquadrant_set - RAquadrant_set)
  RA_set = RA_set / 15
  let sinDec_set = 0.39782 * Math.sin(D2R * L_set)
  let cosDec_set = Math.cos(Math.asin(sinDec_set))
  let cosH_set = (Math.cos(D2R * zenith) - (sinDec_set * Math.sin(D2R * lat))) / (cosDec_set * Math.cos(D2R * lat))
  let H_set = R2D * Math.acos(cosH_set)
  H_set = H_set / 15
  let T_set = H_set + RA_set - (0.06571 * t_set) - 6.622
  let UT_set = (T_set - lngHour) % 24
  let sunset = new Date(Date.UTC(year, month - 1, day))
  sunset.setUTCHours(Math.floor(UT_set), Math.floor((UT_set % 1) * 60), 0, 0)

  // Keine Korrektur/keine Rekursion! Nur für den aktuellen Tag berechnen
  return { sunrise, sunset }
}

function updateTheme() {
  const now = new Date()
  const lat = Number(config.value?.lat ?? 48)
  const lon = Number(config.value?.lon ?? 10)
  const { sunrise, sunset } = getSunTimes(now, lat, lon)
  // Farben dynamisch aus config holen
  const DAY_BG_HEX = normalizeHex(config.value?.theme_day_bg ?? '#eaeaeaff');
  const DAY_TEXT_HEX = normalizeHex(config.value?.theme_day_text ?? '#222222');
  const EVENING_BG_HEX = normalizeHex(config.value?.theme_evening_bg ?? '#ffeebbff');
  const EVENING_TEXT_HEX = normalizeHex(config.value?.theme_evening_text ?? '#3a2c00');
  const DAY_BG = hexToRgb(DAY_BG_HEX)
  const DAY_TEXT = hexToRgb(DAY_TEXT_HEX)
  const EVENING_BG = hexToRgb(EVENING_BG_HEX)
  const EVENING_TEXT = hexToRgb(EVENING_TEXT_HEX)
  // Nur Uhrzeiten vergleichen (ohne Datum)
  const nowMinutes = now.getHours() * 60 + now.getMinutes()
  const sunriseMinutes = sunrise.getHours() * 60 + sunrise.getMinutes()
  const sunsetMinutes = sunset.getHours() * 60 + sunset.getMinutes()
  const yellowMaxMinutes = 22 * 60 // 22:00 Uhr
  const oneHour = 60
  const eveningStartMinutes = sunsetMinutes - oneHour
  const morningFadeStartMinutes = sunriseMinutes - oneHour

  let t = 0
  if (
    (nowMinutes >= eveningStartMinutes && nowMinutes < yellowMaxMinutes && sunsetMinutes < yellowMaxMinutes) ||
    (sunsetMinutes > yellowMaxMinutes && nowMinutes >= eveningStartMinutes && nowMinutes < sunsetMinutes)
  ) {
    // Übergang von weiß zu gelb: linear von eveningStart bis 22 Uhr (oder bis Sonnenuntergang, falls dieser nach 22 Uhr liegt)
    const fadeEnd = Math.min(yellowMaxMinutes, sunsetMinutes)
    t = (nowMinutes - eveningStartMinutes) / (fadeEnd - eveningStartMinutes)
    t = Math.min(Math.max(t, 0), 1) * EVENING_INTENSITY
  } else if (
    // NACHT: nach Sonnenuntergang ODER vor Sonnenaufgang → maximal gelb
    (nowMinutes >= sunsetMinutes || nowMinutes < sunriseMinutes)
  ) {
    t = EVENING_INTENSITY
  } else if (
    (nowMinutes >= morningFadeStartMinutes && nowMinutes < sunriseMinutes) ||
    (morningFadeStartMinutes < 0 && nowMinutes < sunriseMinutes)
  ) {
    // Übergang von gelb zu weiß: linear von 1h vor Sonnenaufgang bis Sonnenaufgang
    t = (sunriseMinutes - nowMinutes) / (sunriseMinutes - morningFadeStartMinutes)
    t = Math.min(Math.max(t, 0), 1) * EVENING_INTENSITY
  } else {
    // Tag: weiß
    t = 0
  }
  // Interpolierte Farben berechnen
  const bg = lerpColor(DAY_BG, EVENING_BG, t)
  const text = lerpColor(DAY_TEXT, EVENING_TEXT, t)
  document.documentElement.style.setProperty('--background', rgbToHex(bg))
  document.documentElement.style.setProperty('--text', rgbToHex(text))
  themeClass.value = t > 0 ? 'theme-evening' : 'theme-day'
  //themeClass.value = 'theme-evening' // <- Zeile einfügen, um das Theme immer zu erzwingen
}

let themeIntervalId = null
export function startThemeInterval() {
  updateTheme()
  themeIntervalId = setInterval(updateTheme, 60 * 1000)
}
export function stopThemeInterval() {
  clearInterval(themeIntervalId)
}
