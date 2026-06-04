import { request } from './client'

export function uploadDocument(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request('/documents/upload', {
    method: 'POST',
    body: formData,
  })
}

export function listDocuments() {
  return request('/documents')
}

export function getDocument(documentId) {
  return request(`/documents/${documentId}`)
}

export function getDocumentTree(documentId) {
  return request(`/documents/${documentId}/tree`)
}

export function getTreeSkeleton(documentId) {
  return request(`/documents/${documentId}/tree/skeleton`)
}

export function getNode(documentId, nodeId) {
  return request(`/documents/${documentId}/nodes/${nodeId}`)
}

export function deleteDocument(documentId) {
  return request(`/documents/${documentId}`, { method: 'DELETE' })
}
