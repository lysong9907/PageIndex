import { streamRequest, request } from './client'

export function askQuestion(documentId, question, chatHistory = []) {
  return streamRequest(`/chat/${documentId}/ask`, {
    method: 'POST',
    body: { question, chat_history: chatHistory },
  })
}

export function getChatHistory(documentId) {
  return request(`/chat/${documentId}/history`)
}

export function clearChatHistory(documentId) {
  return request(`/chat/${documentId}/history`, { method: 'DELETE' })
}
