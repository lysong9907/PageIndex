<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'

const props = defineProps({
  documentId: { type: String, required: true },
  targetPage: { type: Number, default: null },
  lineNum: { type: Number, default: null },
  nodeTitle: { type: String, default: '' },
  sourceInfo: { type: Object, default: null },
})

const emit = defineEmits(['close'])

const loading = ref(true)
const error = ref('')
const info = ref(props.sourceInfo)
const contentData = ref(null)
const blobUrl = ref('')
const contentRef = ref(null)
const iframeRef = ref(null)

const contentType = computed(() => contentData.value?.content_type || 'unknown')
const filename = computed(() => info.value?.filename || contentData.value?.filename || 'Loading...')

const isPdf = computed(() => contentType.value === 'pdf')
const isHtml = computed(() => contentType.value === 'html')
const isText = computed(() => contentType.value === 'text')
const isJson = computed(() => contentType.value === 'json')
const isCsv = computed(() => contentType.value === 'csv')

// JSON syntax highlighting
const highlightedJson = computed(() => {
  if (!isJson.value || !contentData.value?.text) return ''
  const text = contentData.value.text
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"([^"]*?)":/g, '<span class="json-key">"$1"</span>:')
    .replace(/: "([^"]*?)"/g, ': <span class="json-string">"$1"</span>')
    .replace(/: (\d+\.?\d*)/g, ': <span class="json-number">$1</span>')
    .replace(/: (true|false)/g, ': <span class="json-bool">$1</span>')
    .replace(/: null/g, ': <span class="json-null">null</span>')
})

// Text with line numbers
const textWithLines = computed(() => {
  if (!isText.value || !contentData.value?.text) return []
  return contentData.value.text.split('\n')
})

// CSV data
const csvHeaders = computed(() => contentData.value?.headers || [])
const csvRows = computed(() => contentData.value?.rows || [])

// Fetch source info and content
onMounted(async () => {
  try {
    // Fetch source info
    if (!info.value) {
      const infoRes = await fetch(`/api/documents/${props.documentId}/source-info`)
      if (infoRes.ok) {
        info.value = await infoRes.json()
      }
    }

    // Fetch content based on type
    const ext = info.value?.extension || ''
    if (ext === '.pdf') {
      // For PDF: fetch as blob for reliable iframe loading
      const res = await fetch(`/api/documents/${props.documentId}/source`)
      if (!res.ok) throw new Error(`Failed to load PDF (${res.status})`)
      const blob = await res.blob()
      blobUrl.value = URL.createObjectURL(blob)
      contentData.value = { content_type: 'pdf' }
    } else {
      // For all other types: fetch parsed content
      const res = await fetch(`/api/documents/${props.documentId}/source/content`)
      if (!res.ok) throw new Error(`Failed to load content (${res.status})`)
      contentData.value = await res.json()
    }

    loading.value = false
  } catch (e) {
    error.value = e.message || 'Failed to load source file'
    loading.value = false
  }
})

// Scroll to position when targetPage or lineNum changes
watch(() => [props.targetPage, props.lineNum], async ([page, line]) => {
  if (loading.value) return
  await nextTick()

  if (isPdf.value && iframeRef.value && page) {
    // Navigate iframe to specific page
    iframeRef.value.src = `${blobUrl.value}#page=${page}`
  } else if ((isText.value || isJson.value) && line && contentRef.value) {
    // Scroll to specific line in text/json view
    const lineEl = contentRef.value.querySelector(`[data-line="${line}"]`)
    if (lineEl) {
      lineEl.scrollIntoView({ block: 'center', behavior: 'smooth' })
      lineEl.classList.add('highlighted-line')
      setTimeout(() => lineEl.classList.remove('highlighted-line'), 3000)
    }
  } else if (isHtml.value && props.nodeTitle && contentRef.value) {
    // Try to scroll to heading matching node title
    const headings = contentRef.value.querySelectorAll('.docx-heading')
    for (const h of headings) {
      if (h.textContent.includes(props.nodeTitle)) {
        h.scrollIntoView({ block: 'center', behavior: 'smooth' })
        h.classList.add('highlighted-line')
        setTimeout(() => h.classList.remove('highlighted-line'), 3000)
        break
      }
    }
  }
}, { immediate: false })

function onIframeLoad() {
  loading.value = false
  // After iframe loads, apply page hash if needed
  if (props.targetPage && iframeRef.value) {
    iframeRef.value.src = `${blobUrl.value}#page=${props.targetPage}`
  }
}

function handleDownload() {
  const a = document.createElement('a')
  a.href = `/api/documents/${props.documentId}/source`
  a.download = filename.value
  a.click()
}

onBeforeUnmount(() => {
  if (blobUrl.value) URL.revokeObjectURL(blobUrl.value)
})
</script>

<template>
  <div class="source-viewer">
    <!-- Header -->
    <div class="source-viewer__header">
      <div class="source-viewer__title">
        <span class="source-viewer__icon">📄</span>
        <span class="source-viewer__filename" :title="filename">{{ filename }}</span>
        <span v-if="isPdf" class="source-viewer__badge source-viewer__badge--pdf">PDF</span>
        <span v-else-if="isHtml" class="source-viewer__badge source-viewer__badge--docx">DOCX</span>
        <span v-else-if="isText" class="source-viewer__badge source-viewer__badge--text">TXT</span>
        <span v-else-if="isJson" class="source-viewer__badge source-viewer__badge--json">JSON</span>
        <span v-else-if="isCsv" class="source-viewer__badge source-viewer__badge--csv">CSV</span>
      </div>
      <div class="source-viewer__actions">
        <span v-if="contentData?.total_pages" class="source-viewer__meta">{{ contentData.total_pages }} pages</span>
        <span v-else-if="contentData?.total_lines" class="source-viewer__meta">{{ contentData.total_lines }} lines</span>
        <span v-else-if="contentData?.total_rows !== undefined" class="source-viewer__meta">{{ contentData.total_rows }} rows</span>
        <button class="source-viewer__btn" @click="handleDownload" title="Download">⬇️</button>
        <button class="source-viewer__btn source-viewer__btn--close" @click="emit('close')" title="Close">✕</button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="source-viewer__loading">
      <div class="source-viewer__spinner"></div>
      <p>Loading source file...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="source-viewer__error">
      <p>❌ {{ error }}</p>
      <button class="source-viewer__btn" @click="() => { loading = true; error = ''; onMounted() }">Retry</button>
    </div>

    <!-- PDF Viewer -->
    <div v-else-if="isPdf" class="source-viewer__pdf">
      <iframe
        ref="iframeRef"
        :src="blobUrl"
        class="source-viewer__iframe"
        @load="onIframeLoad"
      ></iframe>
    </div>

    <!-- DOCX / HTML Viewer -->
    <div v-else-if="isHtml" class="source-viewer__html" ref="contentRef">
      <div class="source-viewer__html-content" v-html="contentData.html"></div>
    </div>

    <!-- Text / Markdown Viewer -->
    <div v-else-if="isText" class="source-viewer__text" ref="contentRef">
      <div class="source-viewer__line-numbers">
        <div
          v-for="(line, idx) in textWithLines"
          :key="idx"
          :data-line="idx + 1"
          class="line-number"
          :class="{ 'line-number--target': lineNum === idx + 1 }"
        >{{ idx + 1 }}</div>
      </div>
      <pre class="source-viewer__text-content">
        <div
          v-for="(line, idx) in textWithLines"
          :key="idx"
          :data-line="idx + 1"
          class="text-line"
          :class="{ 'text-line--target': lineNum === idx + 1 }"
        >{{ line || ' ' }}</div>
      </pre>
    </div>

    <!-- JSON Viewer -->
    <div v-else-if="isJson" class="source-viewer__json" ref="contentRef">
      <div class="source-viewer__line-numbers">
        <div
          v-for="i in contentData.total_lines"
          :key="i"
          :data-line="i"
          class="line-number"
          :class="{ 'line-number--target': lineNum === i }"
        >{{ i }}</div>
      </div>
      <pre class="source-viewer__json-content" v-html="highlightedJson"></pre>
    </div>

    <!-- CSV Table Viewer -->
    <div v-else-if="isCsv" class="source-viewer__csv">
      <table class="source-viewer__csv-table">
        <thead>
          <tr>
            <th class="csv-row-num">#</th>
            <th v-for="(h, i) in csvHeaders" :key="i">{{ h }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, idx) in csvRows"
            :key="idx"
            :class="{ 'csv-row--target': lineNum === idx + 2 }"
          >
            <td class="csv-row-num">{{ idx + 1 }}</td>
            <td v-for="(cell, ci) in row" :key="ci">{{ cell }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Fallback -->
    <div v-else class="source-viewer__unsupported">
      <p>Preview not available for this file type.</p>
      <button class="source-viewer__btn" @click="handleDownload">⬇️ Download</button>
    </div>
  </div>
</template>

<style scoped>
.source-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-bg-primary);
  border-left: 1px solid var(--color-border-light);
}

.source-viewer__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-sm) var(--space-md);
  border-bottom: 1px solid var(--color-border-light);
  background: var(--color-bg-primary);
  min-height: 48px;
  gap: var(--space-sm);
  box-shadow: var(--shadow-xs);
}

.source-viewer__title {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--color-text-primary);
  overflow: hidden;
  flex: 1;
  min-width: 0;
  letter-spacing: -0.01em;
}

.source-viewer__filename {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 220px;
}

.source-viewer__badge {
  padding: 3px 8px;
  border-radius: var(--border-radius-sm);
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.source-viewer__badge--pdf { background: var(--color-error-bg); color: var(--color-error); }
.source-viewer__badge--docx { background: var(--color-info-bg); color: var(--color-info); }
.source-viewer__badge--text { background: var(--color-bg-tertiary); color: var(--color-text-secondary); }
.source-viewer__badge--json { background: var(--warning-bg); color: var(--color-warning); }
.source-viewer__badge--csv { background: var(--success-bg); color: var(--color-success); }

.source-viewer__actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}

.source-viewer__meta {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  font-weight: 500;
}

.source-viewer__btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: var(--text-base);
  padding: 4px 6px;
  border-radius: var(--border-radius-sm);
  opacity: 0.7;
  transition: all var(--transition-fast);
  color: var(--color-text-secondary);
}

.source-viewer__btn:hover {
  opacity: 1;
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

.source-viewer__btn--close:hover {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.source-viewer__loading,
.source-viewer__error,
.source-viewer__unsupported {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: var(--space-md);
  padding: var(--space-xl);
  text-align: center;
  animation: fadeIn 0.3s ease-out;
}

.source-viewer__spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-border-light);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.source-viewer__error p {
  color: var(--color-error);
  font-weight: 500;
}

.source-viewer__pdf {
  flex: 1;
  overflow: hidden;
}

.source-viewer__iframe {
  width: 100%;
  height: 100%;
  border: none;
}

/* HTML / DOCX viewer */
.source-viewer__html {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-md) var(--space-lg);
  font-size: var(--text-sm);
  line-height: 1.6;
  color: var(--color-text-primary);
  background: var(--color-bg-subtle);
}

.source-viewer__html-content :deep(h4.docx-heading) {
  font-size: var(--text-base);
  font-weight: 700;
  margin: var(--space-md) 0 var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-primary);
  border-radius: var(--border-radius);
  border-left: 3px solid var(--color-accent);
  box-shadow: var(--shadow-xs);
  letter-spacing: -0.01em;
}

.source-viewer__html-content :deep(h4.docx-heading--target) {
  background: var(--color-accent-light);
  border-left-color: var(--color-accent);
}

.source-viewer__html-content :deep(p) {
  margin: var(--space-xs) 0;
  line-height: 1.6;
}

.source-viewer__html-content :deep(table.docx-table) {
  width: 100%;
  border-collapse: collapse;
  margin: var(--space-sm) 0;
  font-size: var(--text-xs);
  background: var(--color-bg-primary);
  border-radius: var(--border-radius);
  overflow: hidden;
  box-shadow: var(--shadow-xs);
}

.source-viewer__html-content :deep(th),
.source-viewer__html-content :deep(td) {
  border: 1px solid var(--color-border-light);
  padding: var(--space-sm) var(--space-md);
  text-align: left;
}

.source-viewer__html-content :deep(th) {
  background: var(--color-bg-secondary);
  font-weight: 700;
  color: var(--color-text-primary);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

/* Text viewer with line numbers */
.source-viewer__text {
  flex: 1;
  display: flex;
  overflow: hidden;
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  line-height: 1.6;
  background: var(--color-bg-subtle);
}

.source-viewer__line-numbers {
  flex-shrink: 0;
  width: 48px;
  overflow-y: auto;
  background: var(--color-bg-primary);
  border-right: 1px solid var(--color-border-light);
  user-select: none;
  text-align: right;
  padding: var(--space-sm) var(--space-xs);
  color: var(--color-text-muted);
  font-size: 10px;
}

.line-number {
  padding: 0 var(--space-xs);
}

.line-number--target,
.text-line--target {
  background: #fef08a !important;
  border-radius: 2px;
  font-weight: 700;
}

.source-viewer__text-content {
  flex: 1;
  overflow-y: auto;
  margin: 0;
  padding: var(--space-sm) var(--space-md);
  white-space: pre;
  background: var(--color-bg-primary);
}

.text-line {
  display: block;
}

/* JSON viewer */
.source-viewer__json {
  flex: 1;
  display: flex;
  overflow: hidden;
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  line-height: 1.6;
  background: var(--color-bg-subtle);
}

.source-viewer__json-content {
  flex: 1;
  overflow-y: auto;
  margin: 0;
  padding: var(--space-sm) var(--space-md);
  white-space: pre;
  background: var(--color-bg-primary);
  border-radius: var(--border-radius);
  margin: var(--space-xs);
}

.source-viewer__json-content :deep(.json-key) { color: #d946ef; font-weight: 500; }
.source-viewer__json-content :deep(.json-string) { color: #10b981; }
.source-viewer__json-content :deep(.json-number) { color: #f59e0b; }
.source-viewer__json-content :deep(.json-bool) { color: #3b82f6; font-weight: 600; }
.source-viewer__json-content :deep(.json-null) { color: #6b7280; font-style: italic; }

/* CSV table viewer */
.source-viewer__csv {
  flex: 1;
  overflow: auto;
  padding: var(--space-sm);
  background: var(--color-bg-subtle);
}

.source-viewer__csv-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-xs);
  background: var(--color-bg-primary);
  border-radius: var(--border-radius);
  overflow: hidden;
  box-shadow: var(--shadow-xs);
}

.source-viewer__csv-table th,
.source-viewer__csv-table td {
  border: 1px solid var(--color-border-light);
  padding: var(--space-sm) var(--space-md);
  text-align: left;
}

.source-viewer__csv-table th {
  background: var(--color-bg-secondary);
  font-weight: 700;
  position: sticky;
  top: 0;
  color: var(--color-text-primary);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.csv-row-num {
  width: 36px;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 10px;
  background: var(--color-bg-secondary);
  flex-shrink: 0;
}

.csv-row--target {
  background: #fef08a !important;
}
</style>
