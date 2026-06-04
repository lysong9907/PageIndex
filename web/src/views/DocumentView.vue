<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useDocumentsStore } from '@/stores/documents'
import TreeViewer from '@/components/tree/TreeViewer.vue'
import ChatPanel from '@/components/chat/ChatPanel.vue'
import SourceFileViewer from '@/components/SourceFileViewer.vue'

const route = useRoute()
const store = useDocumentsStore()

const documentId = computed(() => route.params.id)
const loading = ref(true)
const error = ref('')
const processingStatus = ref('')
const processingMessage = ref('')

// Source viewer state
const showSourceViewer = ref(false)
const sourceTargetPage = ref(null)
const sourceLineNum = ref(null)
const sourceNodeTitle = ref('')

function openSourceViewer(page, lineNum, nodeTitle) {
  sourceTargetPage.value = page
  sourceLineNum.value = lineNum
  sourceNodeTitle.value = nodeTitle || ''
  showSourceViewer.value = true
}

function closeSourceViewer() {
  showSourceViewer.value = false
  sourceTargetPage.value = null
  sourceLineNum.value = null
  sourceNodeTitle.value = ''
}

async function loadDocument() {
  loading.value = true
  error.value = ''

  try {
    // Check if document is still processing
    const docMeta = store.documents.find(d => d.document_id === documentId.value)

    if (docMeta?.status === 'processing') {
      processingStatus.value = 'processing'
      // Connect to SSE for progress
      pollProgress()
      return
    }

    // Fetch tree
    await store.fetchTree(documentId.value)
    processingStatus.value = 'completed'
  } catch (e) {
    error.value = e.message || 'Failed to load document'
  } finally {
    loading.value = false
  }
}

async function pollProgress() {
  try {
    const response = await fetch(`/api/documents/${documentId.value}/progress`)
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
        const dataLine = part.split('\n').find(l => l.startsWith('data: '))
        if (!dataLine) continue

        try {
          const data = JSON.parse(dataLine.slice(6))
          processingMessage.value = data.message || data.stage || ''

          if (data.status === 'completed') {
            processingStatus.value = 'completed'
            store.updateDocumentStatus(documentId.value, 'completed')
            store.fetchDocuments()
            await store.fetchTree(documentId.value)
            loading.value = false
            return
          }
          if (data.status === 'failed') {
            error.value = data.message || 'Processing failed'
            processingStatus.value = 'failed'
            loading.value = false
            return
          }
        } catch {}
      }
    }
  } catch (e) {
    // If SSE fails, try fetching tree directly (maybe already done)
    try {
      await store.fetchTree(documentId.value)
      processingStatus.value = 'completed'
      loading.value = false
    } catch {
      error.value = 'Failed to connect to processing stream'
      loading.value = false
    }
  }
}

onMounted(loadDocument)
watch(documentId, loadDocument)
</script>

<template>
  <div class="doc-view">
    <!-- Loading / Processing -->
    <div v-if="loading || processingStatus === 'processing'" class="doc-view__loading">
      <div class="doc-view__spinner"></div>
      <h3>Processing Document...</h3>
      <p>{{ processingMessage || 'Analyzing document structure with AI...' }}</p>
      <p class="doc-view__hint">This may take 1-3 minutes depending on document size.</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="doc-view__error">
      <p>❌ {{ error }}</p>
      <button @click="loadDocument">Retry</button>
    </div>

    <!-- Document loaded -->
    <div v-else-if="store.activeTree" class="doc-view__content">
      <div class="doc-view__tree-panel">
        <TreeViewer
          :tree="store.activeTree"
          :document-id="documentId"
          @node-select-page="openSourceViewer"
        />
      </div>
      <div v-if="showSourceViewer" class="doc-view__source-panel">
        <SourceFileViewer
          :document-id="documentId"
          :target-page="sourceTargetPage"
          :line-num="sourceLineNum"
          :node-title="sourceNodeTitle"
          :source-info="null"
          @close="closeSourceViewer"
        />
      </div>
      <div class="doc-view__chat-panel">
        <ChatPanel :document-id="documentId" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.doc-view {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--color-bg-primary);
}

.doc-view__content {
  display: flex;
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.doc-view__loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100vh;
  gap: var(--space-md);
  text-align: center;
}

.doc-view__loading h3 {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--color-text-primary);
  text-align: center;
}

.doc-view__loading p {
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  text-align: center;
}

.doc-view__hint {
  font-size: var(--text-xs) !important;
  color: var(--color-text-muted) !important;
  text-align: center;
}

.doc-view__spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border-light);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.doc-view__error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  gap: var(--space-md);
}

.doc-view__error p {
  color: var(--color-error);
  font-size: var(--text-base);
  font-weight: 600;
}

.doc-view__error button {
  padding: var(--space-sm) var(--space-lg);
  background: var(--gradient-accent);
  color: white;
  border: none;
  border-radius: var(--border-radius);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.doc-view__error button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}

.doc-view__tree-panel {
  width: 340px;
  flex-shrink: 0;
  border-right: 1px solid var(--color-border-light);
  display: flex;
  flex-direction: column;
  background: var(--color-bg-primary);
}

.doc-view__source-panel {
  width: 380px;
  flex-shrink: 0;
  border-right: 1px solid var(--color-border-light);
  display: flex;
  flex-direction: column;
  background: var(--color-bg-secondary);
  transition: width var(--transition-normal);
}

.doc-view__chat-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
</style>
