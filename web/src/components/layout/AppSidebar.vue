<script setup>
import { useRouter, useRoute } from 'vue-router'
import { useDocumentsStore } from '@/stores/documents'
import DocumentList from '@/components/document/DocumentList.vue'

const router = useRouter()
const route = useRoute()
const documentsStore = useDocumentsStore()

function onUploadClick() {
  if (route.path === '/') {
    // Already on home page — trigger the file input directly
    const fileInput = document.querySelector('.upload__dropzone input[type="file"]')
    if (fileInput) fileInput.click()
  } else {
    router.push('/')
  }
}
</script>

<template>
  <div class="sidebar">
    <div class="sidebar__header">
      <h1 class="sidebar__title">📄 PageIndex</h1>
      <p class="sidebar__subtitle">Document Intelligence</p>
    </div>

    <button class="sidebar__new-btn" @click="onUploadClick">
      <span class="sidebar__new-icon">＋</span>
      Upload Document
    </button>

    <div class="sidebar__documents">
      <DocumentList />
    </div>

    <div class="sidebar__footer">
      <button class="sidebar__settings-btn" @click="router.push('/settings')">
        ⚙️ Settings
      </button>
    </div>
  </div>
</template>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: var(--space-lg) var(--space-md);
  background: linear-gradient(180deg, var(--color-bg-subtle) 0%, var(--color-bg-secondary) 100%);
}

.sidebar__header {
  margin-bottom: var(--space-lg);
  padding: 0 4px;
}

.sidebar__title {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
  background: var(--gradient-accent);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.sidebar__subtitle {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: 2px;
  font-weight: 500;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.sidebar__new-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  width: 100%;
  padding: 11px var(--space-md);
  background: var(--gradient-accent);
  color: white;
  border-radius: var(--border-radius);
  font-weight: 600;
  font-size: var(--text-sm);
  transition: all var(--transition-fast);
  margin-bottom: var(--space-md);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.25);
  letter-spacing: -0.01em;
}

.sidebar__new-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}

.sidebar__new-btn:active {
  transform: translateY(0);
}

.sidebar__new-icon {
  font-size: var(--text-lg);
  font-weight: 300;
}

.sidebar__documents {
  flex: 1;
  overflow-y: auto;
  margin: 0 calc(var(--space-md) * -1);
  padding: 0 var(--space-md);
}

.sidebar__footer {
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border-light);
}

.sidebar__settings-btn {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  text-align: left;
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  font-weight: 500;
  border-radius: var(--border-radius);
  transition: all var(--transition-fast);
}

.sidebar__settings-btn:hover {
  background: var(--color-accent-ghost);
  color: var(--color-accent);
}
</style>
