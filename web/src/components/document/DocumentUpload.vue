<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDocumentsStore } from '@/stores/documents'
import { uploadDocument } from '@/api/documents'

const router = useRouter()
const store = useDocumentsStore()

const isDragging = ref(false)
const uploading = ref(false)
const uploadError = ref('')

function onDragOver(e) {
  e.preventDefault()
  isDragging.value = true
}

function onDragLeave() {
  isDragging.value = false
}

function onDrop(e) {
  e.preventDefault()
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) handleFile(file)
}

function onFileSelect(e) {
  const file = e.target?.files?.[0]
  if (file) handleFile(file)
}

async function handleFile(file) {
  const ext = file.name.split('.').pop()?.toLowerCase()
  if (!['pdf', 'md', 'markdown', 'txt', 'json', 'csv', 'docx', 'doc'].includes(ext)) {
    uploadError.value = 'Unsupported format. Supports: PDF, Markdown, TXT, JSON, CSV, Word'
    return
  }

  if (file.size > 50 * 1024 * 1024) {
    uploadError.value = 'File too large (max 50MB)'
    return
  }

  uploading.value = true
  uploadError.value = ''

  try {
    const result = await uploadDocument(file)
    store.addDocument(result)
    router.push(`/doc/${result.document_id}`)
  } catch (e) {
    uploadError.value = e.message || 'Upload failed'
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="upload">
    <div
      class="upload__dropzone"
      :class="{ 'upload__dropzone--active': isDragging, 'upload__dropzone--uploading': uploading }"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
      @drop="onDrop"
    >
      <div v-if="uploading" class="upload__loading">
        <div class="upload__spinner"></div>
        <p>Uploading & Processing...</p>
      </div>
      <div v-else class="upload__content">
        <div class="upload__icon">📁</div>
        <h3 class="upload__title">Upload Document</h3>
        <p class="upload__desc">Drag and drop a file here</p>
        <label class="upload__btn">
          Browse Files
          <input type="file" accept=".pdf,.md,.markdown,.txt,.json,.csv,.docx,.doc" hidden @change="onFileSelect" />
        </label>
        <p class="upload__hint">Supports PDF, Markdown, TXT, JSON, CSV, Word • Max 50MB</p>
      </div>
    </div>

    <p v-if="uploadError" class="upload__error">{{ uploadError }}</p>
  </div>
</template>

<style scoped>
.upload {
  width: 100%;
  max-width: 520px;
  margin: 0 auto;
}

.upload__dropzone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  border: 2px dashed var(--color-border);
  border-radius: var(--border-radius-xl);
  padding: var(--space-2xl) var(--space-xl);
  transition: all var(--transition-normal);
  background: var(--color-bg-primary);
  box-shadow: var(--shadow-xs);
}

.upload__loading {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  padding: var(--space-xl) var(--space-lg);
  text-align: center;
}

.upload__dropzone::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: inherit;
  padding: 2px;
  background: linear-gradient(135deg, transparent 30%, var(--color-accent) 50%, #8b5cf6 70%, transparent 100%);
  background-size: 200% 200%;
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0;
  transition: opacity var(--transition-normal);
  animation: shimmer 3s linear infinite;
  pointer-events: none;
}

.upload__dropzone:hover::before,
.upload__dropzone--active::before {
  opacity: 1;
}

.upload__dropzone--active {
  border-color: var(--color-accent);
  background: var(--color-accent-subtle);
  box-shadow: var(--shadow-glow);
}

.upload__dropzone--uploading {
  border-color: var(--color-accent);
  background: var(--color-accent-subtle);
}

.upload__content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
}

.upload__icon {
  font-size: 56px;
  margin-bottom: var(--space-sm);
  opacity: 0.7;
  filter: grayscale(20%);
}

.upload__title {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
}

.upload__desc {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.upload__btn {
  display: inline-block;
  padding: 10px var(--space-lg);
  background: var(--gradient-accent);
  color: white;
  border-radius: var(--border-radius);
  font-weight: 600;
  font-size: var(--text-sm);
  cursor: pointer;
  margin-top: var(--space-sm);
  transition: all var(--transition-fast);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.25);
  letter-spacing: -0.01em;
}

.upload__btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}

.upload__hint {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: var(--space-xs);
}

.upload__loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  padding: var(--space-xl) var(--space-lg);
  text-align: center;
}

.upload__spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border-light);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.upload__loading p {
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  font-weight: 500;
  text-align: center;
  line-height: 1.5;
}

.upload__error {
  color: var(--color-error);
  font-size: var(--text-sm);
  text-align: center;
  margin-top: var(--space-sm);
  font-weight: 500;
  padding: var(--space-sm) var(--space-md);
  background: var(--color-error-bg);
  border-radius: var(--border-radius);
}
</style>
