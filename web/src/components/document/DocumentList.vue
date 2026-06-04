<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useDocumentsStore } from '@/stores/documents'

const router = useRouter()
const route = useRoute()
const store = useDocumentsStore()

const activeDocId = computed(() => route.params.id)

function selectDoc(docId) {
  router.push(`/doc/${docId}`)
}

async function deleteDoc(docId) {
  if (confirm('Delete this document and its tree?')) {
    await store.removeDocument(docId)
    if (activeDocId.value === docId) {
      router.push('/')
    }
  }
}

function getStatusDot(status) {
  const colors = { completed: '#10b981', processing: '#f59e0b', failed: '#ef4444' }
  return colors[status] || '#9ca3af'
}

function getFileIcon(type) {
  const icons = {
    pdf: '📕',
    markdown: '📝',
    text: '📄',
    json: '📋',
    csv: '📊',
    word: '📘',
  }
  return icons[type] || '📄'
}
</script>

<template>
  <div class="doc-list">
    <div class="doc-list__label">Documents</div>

    <div v-if="store.documents.length === 0" class="doc-list__empty">
      No documents yet.<br>Upload one to get started.
    </div>

    <div
      v-for="doc in store.documents"
      :key="doc.document_id"
      class="doc-item"
      :class="{ 'doc-item--active': doc.document_id === activeDocId }"
      @click="selectDoc(doc.document_id)"
    >
      <span class="doc-item__icon">{{ getFileIcon(doc.file_type) }}</span>
      <div class="doc-item__info">
        <div class="doc-item__name" :title="doc.filename">{{ doc.filename }}</div>
        <div class="doc-item__meta">
          <span class="doc-item__status-dot" :style="{ background: getStatusDot(doc.status) }"></span>
          {{ doc.status }}
        </div>
      </div>
      <button class="doc-item__delete" @click.stop="deleteDoc(doc.document_id)" title="Delete">✕</button>
    </div>
  </div>
</template>

<style scoped>
.doc-list__label {
  font-size: var(--text-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
  margin-bottom: var(--space-sm);
  padding-left: 4px;
}

.doc-list__empty {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  text-align: center;
  padding: var(--space-xl) 0;
  line-height: 1.6;
}

.doc-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) 10px;
  margin-bottom: 2px;
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
  background: transparent;
}

.doc-item:hover {
  background: var(--color-accent-ghost);
  transform: translateX(2px);
}

.doc-item--active {
  background: var(--color-accent-light);
  box-shadow: inset 3px 0 0 var(--color-accent);
}

.doc-item--active .doc-item__name {
  color: var(--color-accent);
  font-weight: 600;
}

.doc-item__icon {
  font-size: 1.1rem;
  flex-shrink: 0;
  opacity: 0.85;
}

.doc-item__info {
  flex: 1;
  min-width: 0;
}

.doc-item__name {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color var(--transition-fast);
}

.doc-item__meta {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: 2px;
  text-transform: capitalize;
}

.doc-item__status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 0 2px rgba(255,255,255,0.8);
}

.doc-item__delete {
  opacity: 0;
  font-size: 0.7rem;
  color: var(--color-text-muted);
  padding: 5px;
  border-radius: var(--border-radius-sm);
  transition: all var(--transition-fast);
}

.doc-item:hover .doc-item__delete {
  opacity: 1;
}

.doc-item__delete:hover {
  color: var(--color-error);
  background: var(--color-error-bg);
}
</style>
