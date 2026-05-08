/**
 * Centralised API client.
 *
 * Uses fetch + browser ETag handling (manual to allow Vue Query integration).
 * The browser would normally cache 304 responses transparently, but with our
 * Vue Query layer we want explicit access to the previous cached body.
 */

const _etagMap = new Map()
const _bodyMap = new Map()

/**
 * Fetch JSON with ETag support.
 * On 304, returns the previously cached body.
 */
export async function fetchJson(url, { signal } = {}) {
  const headers = {}
  const etag = _etagMap.get(url)
  if (etag) headers['If-None-Match'] = etag

  const res = await fetch(url, { headers, cache: 'no-store', signal })

  if (res.status === 304) {
    return _bodyMap.get(url)
  }
  if (!res.ok) {
    throw new Error(`HTTP ${res.status} on ${url}`)
  }

  const newEtag = res.headers.get('ETag')
  if (newEtag) _etagMap.set(url, newEtag)

  const body = await res.json()
  _bodyMap.set(url, body)
  return body
}

export function clearEtagCache() {
  _etagMap.clear()
  _bodyMap.clear()
}
