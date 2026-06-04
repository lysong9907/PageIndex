<script setup>
import { ref, watch } from 'vue'
import { getNode } from '@/api/documents'

const props = defineProps({
  documentId: { type: String, required: true },
  nodeId: { type: String, required: true },
})

const emit = defineEmits(['close', 'view-source'])

const nodeDetail = ref(null)
const loading = ref(false)

watch(() => props.nodeId, async (id) => {
  if (!id) return
  loading.value = true
  try {
    nodeDetail.value = await getNode(props.documentId, id)
  } catch (e) {
    nodeDetail.value = null
  } finally {
    loading.value = false
  }
}, { immediate: true })
</script>

<template>
  <div class="node-detail">
    <div class="node-detail__header">
      <h3 class="node-detail__title">Node Detail</h3>
      <button class="node-detail__close" @click="emit('close')">✕</button>
    </div>

    <div v-if="loading" class="node-detail__loading">Loading...</div>

    <div v-else-if="nodeDetail" class="node-detail__body">
      <div class="node-detail__field">
        <label>Title</label>
        <p>{{ nodeDetail.title }}</p>
      </div>

      <div class="node-detail__row">
        <div class="node-detail__field" v-if="nodeDetail.node_id">
          <label>Node ID</label>
          <code>{{ nodeDetail.node_id }}</code>
        </div>
        <div class="node-detail__field" v-if="nodeDetail.start_index">
          <label>Pages</label>
          <p>{{ nodeDetail.start_index }} - {{ nodeDetail.end_index }}</p>
        </div>
        <div class="node-detail__field" v-if="nodeDetail.line_num">
          <label>Line</label>
          <p>{{ nodeDetail.line_num }}</p>
        </div>
      </div>

      <div class="node-detail__field" v-if="nodeDetail.summary">
        <label>Summary</label>
        <p class="node-detail__text">{{ nodeDetail.summary }}</p>
      </div>

      <div v-if="nodeDetail.start_index || nodeDetail.line_num" class="node-detail__action">
        <button
          class="node-detail__view-source"
          @click="emit('view-source', nodeDetail.start_index, nodeDetail.line_num, nodeDetail.title)"
        >
          📄 View Source <template v-if="nodeDetail.start_index">(p.{{ nodeDetail.start_index }})</template><template v-else-if="nodeDetail.line_num">(line {{ nodeDetail.line_num }})</template>
        </button>
      </div>

      <div class="node-detail__field" v-if="nodeDetail.text">
        <label>Full Text</label>
        <pre class="node-detail__text node-detail__text--pre">{{ nodeDetail.text }}</pre>
      </div>
    </div>
  </div>
</template>

<style scoped>
.node-detail {
  width: 320px;
  border-left: 1px solid var(--color-border-light);
  background: var(--color-bg-secondary);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.node-detail__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  border-bottom: 1px solid var(--color-border-light);
  background: var(--color-bg-primary);
}

.node-detail__title {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

.node-detail__close {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  padding: 5px;
  border-radius: var(--border-radius-sm);
  transition: all var(--transition-fast);
}

.node-detail__close:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

.node-detail__loading {
  padding: var(--space-lg);
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.node-detail__body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.node-detail__row {
  display: flex;
  gap: var(--space-md);
}

.node-detail__field label {
  display: block;
  font-size: var(--text-xs);
  font-weight: 700;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 5px;
}

.node-detail__field p, .node-detail__field code {
  font-size: var(--text-sm);
  line-height: 1.5;
}

.node-detail__field code {
  font-family: var(--font-mono);
  background: var(--color-bg-tertiary);
  padding: 3px 8px;
  border-radius: var(--border-radius-sm);
  font-weight: 500;
}

.node-detail__text {
  max-height: 300px;
  overflow-y: auto;
  font-size: var(--text-sm);
  line-height: 1.6;
  color: var(--color-text-secondary);
}

.node-detail__text--pre {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  white-space: pre-wrap;
  word-break: break-word;
  background: var(--color-bg-tertiary);
  padding: var(--space-sm);
  border-radius: var(--border-radius);
}

.node-detail__action {
  padding-top: var(--space-sm);
  border-top: 1px solid var(--color-border-light);
  margin-top: var(--space-xs);
}

.node-detail__view-source {
  width: 100%;
  padding: 10px var(--space-md);
  background: var(--gradient-accent);
  color: white;
  border: none;
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.25);
  letter-spacing: -0.01em;
}

.node-detail__view-source:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}
</style>
