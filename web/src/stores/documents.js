import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/documents'

export const useDocumentsStore = defineStore('documents', () => {
  const documents = ref([])
  const activeTree = ref(null)
  const activeDocId = ref(null)
  const loading = ref(false)

  async function fetchDocuments() {
    loading.value = true
    try {
      const res = await api.listDocuments()
      documents.value = res.documents || []
    } catch (e) {
      console.error('Failed to fetch documents:', e)
    } finally {
      loading.value = false
    }
  }

  async function fetchTree(documentId) {
    try {
      const tree = await api.getDocumentTree(documentId)
      activeTree.value = tree
      activeDocId.value = documentId
      return tree
    } catch (e) {
      console.error('Failed to fetch tree:', e)
      return null
    }
  }

  async function removeDocument(documentId) {
    await api.deleteDocument(documentId)
    documents.value = documents.value.filter(d => d.document_id !== documentId)
    if (activeDocId.value === documentId) {
      activeTree.value = null
      activeDocId.value = null
    }
  }

  function addDocument(doc) {
    documents.value.unshift(doc)
  }

  function updateDocumentStatus(documentId, status) {
    const doc = documents.value.find(d => d.document_id === documentId)
    if (doc) doc.status = status
  }

  return {
    documents, activeTree, activeDocId, loading,
    fetchDocuments, fetchTree, removeDocument, addDocument, updateDocumentStatus,
  }
})
