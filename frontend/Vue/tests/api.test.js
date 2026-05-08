import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { fetchJson, clearEtagCache } from '../src/utils/api.js'

describe('fetchJson', () => {
  beforeEach(() => {
    clearEtagCache()
    globalThis.fetch = vi.fn()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('returns parsed JSON on 200', async () => {
    globalThis.fetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json', ETag: '"v1"' },
      })
    )
    const data = await fetchJson('/api/x')
    expect(data).toEqual({ ok: true })
  })

  it('throws on 5xx', async () => {
    globalThis.fetch.mockResolvedValueOnce(new Response('boom', { status: 500 }))
    await expect(fetchJson('/api/y')).rejects.toThrow()
  })
})
