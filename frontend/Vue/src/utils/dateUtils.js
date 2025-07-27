export function formatGermanDateWithWeekday(dateStr, showOnlyWeekday = false) {
  if (typeof dateStr !== 'string') return 'Ungültiges Datum'
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  let parsedDate = null
  if (dateStr.includes(',')) {
    const parts = dateStr.split(',')[1].trim()
    const regex = /^(\d{1,2})\.\s*([A-Za-zäöüÄÖÜß]+)/
    const match = parts.match(regex)
    if (match) {
      const [_, day, monthName] = match
      const germanMonths = [
        'januar', 'februar', 'märz', 'april', 'mai', 'juni',
        'juli', 'august', 'september', 'oktober', 'november', 'dezember'
      ]
      const monthIndex = germanMonths.indexOf(monthName.toLowerCase())
      if (monthIndex >= 0) {
        parsedDate = new Date(today.getFullYear(), monthIndex, parseInt(day, 10))
      }
    }
  } else {
    const isoDate = new Date(dateStr)
    if (!isNaN(isoDate)) {
      parsedDate = new Date(isoDate.getFullYear(), isoDate.getMonth(), isoDate.getDate())
    }
  }
  if (parsedDate) {
    if (parsedDate.getTime() === today.getTime()) {
      return 'Heute'
    }
    if (showOnlyWeekday) {
      return parsedDate.toLocaleDateString('de-DE', { weekday: 'long' })
    }
    return parsedDate.toLocaleDateString('de-DE', {
      weekday: 'long',
      day: '2-digit',
      month: 'long'
    })
  }
  return 'Ungültiges Datum'
}

export function getFormattedDate(short = false) {
  const now = new Date()
  if (short) {
    // Format: Dienstag, 22. Juli
    return now.toLocaleDateString('de-DE', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
    })
  } else {
    // Standard: Dienstag, 22. Juli 2025
    const weekday = now.toLocaleDateString('de-DE', { weekday: 'long' })
    const fullDate = now.toLocaleDateString('de-DE', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    })
    return `${weekday}, ${fullDate}`
  }
}