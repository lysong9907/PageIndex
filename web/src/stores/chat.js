import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api/chat'

export const useChatStore = defineStore('chat', () => {
  const sessions = ref({})          // { [documentId]: Message[] }
  const streamingDocId = ref(null)
  const streamingMessage = ref(null)
  const highlightedNodes = ref(new Set())

  const isStreaming = computed(() => streamingDocId.value !== null)

  function getMessages(documentId) {
    return sessions.value[documentId] || []
  }

  function addMessage(documentId, message) {
    if (!sessions.value[documentId]) {
      sessions.value[documentId] = []
    }
    sessions.value[documentId].push(message)
  }

  async function askQuestion(documentId, question) {
    // Add user message
    addMessage(documentId, {
      id: Date.now().toString(),
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    })

    // Create streaming placeholder
    streamingDocId.value = documentId
    streamingMessage.value = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      thinking: '',
      referenced_nodes: [],
      phase: 'tree_search',
      timestamp: new Date().toISOString(),
    }

    try {
      const chatHistory = (sessions.value[documentId] || [])
        .filter(m => m.role === 'user' || m.role === 'assistant')
        .slice(-6)
        .map(m => ({ role: m.role, content: m.content }))

      const response = await api.askQuestion(documentId, question, chatHistory)
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
            if (line.startsWith('event: ')) eventType = line.slice(7).trim()
            else if (line.startsWith('data: ')) data += line.slice(6)
          }

          if (!data) continue

          let parsed
          try { parsed = JSON.parse(data) } catch { continue }

          switch (eventType) {
            case 'phase':
              streamingMessage.value.phase = parsed.phase
              break
            case 'thinking':
              streamingMessage.value.thinking = parsed.content
              break
            case 'nodes_found':
              streamingMessage.value.referenced_nodes = parsed.node_ids || []
              highlightedNodes.value = new Set(parsed.node_ids || [])
              break
            case 'answer_chunk':
              streamingMessage.value.content += parsed.content || ''
              break
            case 'done':
              break
            case 'error':
              streamingMessage.value.content += `\n\n**Error:** ${parsed.message}`
              break
          }
        }
      }

      // Finalize message
      addMessage(documentId, { ...streamingMessage.value })

    } catch (e) {
      addMessage(documentId, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${e.message}`,
        timestamp: new Date().toISOString(),
      })
    } finally {
      streamingMessage.value = null
      streamingDocId.value = null
    }
  }

  function clearHighlights() {
    highlightedNodes.value = new Set()
  }

  async function clearHistory(documentId) {
    await api.clearChatHistory(documentId)
    sessions.value[documentId] = []
  }

  return {
    sessions, streamingDocId, streamingMessage, highlightedNodes, isStreaming,
    getMessages, addMessage, askQuestion, clearHighlights, clearHistory,
  }
})
