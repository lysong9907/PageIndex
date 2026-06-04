import { ref, onUnmounted } from 'vue'

export function useSSE() {
  const isConnected = ref(false)
  const error = ref(null)
  let abortController = null

  async function connect(url, options = {}, handlers = {}) {
    abortController = new AbortController()
    isConnected.value = true
    error.value = null

    try {
      const fetchOptions = {
        method: options.method || 'GET',
        signal: abortController.signal,
      }

      if (options.body) {
        fetchOptions.headers = { 'Content-Type': 'application/json' }
        fetchOptions.body = JSON.stringify(options.body)
      }

      const response = await fetch(url, fetchOptions)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop()

        for (const part of parts) {
          if (!part.trim()) continue

          let eventType = 'message'
          let data = ''

          for (const line of part.split('\n')) {
            if (line.startsWith('event: ')) {
              eventType = line.slice(7).trim()
            } else if (line.startsWith('data: ')) {
              data += line.slice(6)
            }
          }

          if (data) {
            try {
              const parsed = JSON.parse(data)
              handlers.onEvent?.(eventType, parsed)
            } catch {
              handlers.onEvent?.(eventType, data)
            }
          }
        }
      }

      handlers.onComplete?.()
    } catch (err) {
      if (err.name !== 'AbortError') {
        error.value = err.message
        handlers.onError?.(err)
      }
    } finally {
      isConnected.value = false
    }
  }

  function disconnect() {
    abortController?.abort()
    isConnected.value = false
  }

  onUnmounted(() => disconnect())

  return { connect, disconnect, isConnected, error }
}
