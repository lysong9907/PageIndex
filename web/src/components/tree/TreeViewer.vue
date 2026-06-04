<script setup>
import { ref, computed, provide, watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import TreeNode from './TreeNode.vue'
import TreeNodeDetail from './TreeNodeDetail.vue'

const props = defineProps({
  tree: { type: Object, required: true },
  documentId: { type: String, required: true },
})

const emit = defineEmits(['node-select-page'])

const chatStore = useChatStore()

const expandedNodeIds = ref(new Set())
const selectedNodeId = ref(null)
const filterText = ref('')

// Auto-expand first level
watch(() => props.tree, (tree) => {
  if (tree?.structure) {
    tree.structure.forEach(node => {
      if (node.node_id) expandedNodeIds.value.add(node.node_id)
    })
  }
}, { immediate: true })

function toggleExpand(nodeId) {
  if (expandedNodeIds.value.has(nodeId)) {
    expandedNodeIds.value.delete(nodeId)
  } else {
    expandedNodeIds.value.add(nodeId)
  }
  expandedNodeIds.value = new Set(expandedNodeIds.value) // trigger reactivity
}

function selectNode(nodeId, nodeData) {
  const wasSelected = selectedNodeId.value === nodeId
  selectedNodeId.value = wasSelected ? null : nodeId

  // If node has page info (PDF start_index) or line info (TXT/JSON line_num), emit to open source viewer
  if (!wasSelected && nodeData) {
    const page = nodeData.start_index || null
    const line = nodeData.line_num || null
    if (page || line) {
      emit('node-select-page', page, line, nodeData.title || '')
    }
  }
}

function expandAll() {
  function walk(node) {
    if (node.node_id) expandedNodeIds.value.add(node.node_id)
    node.nodes?.forEach(walk)
  }
  props.tree?.structure?.forEach(walk)
  expandedNodeIds.value = new Set(expandedNodeIds.value)
}

function collapseAll() {
  expandedNodeIds.value = new Set()
}

// Watch chat highlights and auto-expand ancestors
watch(() => chatStore.highlightedNodes, (newIds) => {
  if (newIds.size === 0) return
  // Expand ancestors of highlighted nodes
  function findAndExpand(node, targetIds, ancestors = []) {
    if (targetIds.has(node.node_id)) {
      ancestors.forEach(id => expandedNodeIds.value.add(id))
    }
    node.nodes?.forEach(child => {
      findAndExpand(child, targetIds, [...ancestors, node.node_id])
    })
  }
  props.tree?.structure?.forEach(node => findAndExpand(node, newIds))
  expandedNodeIds.value = new Set(expandedNodeIds.value)
}, { deep: true })

provide('expandedNodeIds', expandedNodeIds)
provide('selectedNodeId', selectedNodeId)
provide('highlightedNodeIds', computed(() => chatStore.highlightedNodes))
provide('toggleExpand', toggleExpand)
provide('selectNode', selectNode)

const filteredStructure = computed(() => {
  if (!filterText.value.trim()) return props.tree?.structure || []
  const term = filterText.value.toLowerCase()

  function matches(node) {
    if (node.title?.toLowerCase().includes(term)) return true
    if (node.summary?.toLowerCase().includes(term)) return true
    return node.nodes?.some(matches) || false
  }

  function filter(nodes) {
    return nodes.filter(matches).map(node => ({
      ...node,
      nodes: node.nodes ? filter(node.nodes) : [],
    }))
  }

  return filter(props.tree?.structure || [])
})
</script>

<template>
  <div class="tree-viewer">
    <div class="tree-viewer__toolbar">
      <input
        v-model="filterText"
        class="tree-viewer__search"
        type="text"
        placeholder="🔍 Search nodes..."
      />
      <div class="tree-viewer__actions">
        <button class="tree-viewer__btn" @click="expandAll" title="Expand All">▼</button>
        <button class="tree-viewer__btn" @click="collapseAll" title="Collapse All">▶</button>
      </div>
    </div>

    <div class="tree-viewer__content">
      <div class="tree-viewer__tree">
        <TreeNode
          v-for="node in filteredStructure"
          :key="node.node_id || node.title"
          :node="node"
          :depth="0"
        />
        <div v-if="filteredStructure.length === 0" class="tree-viewer__empty">
          No matching nodes found.
        </div>
      </div>

      <TreeNodeDetail
        v-if="selectedNodeId"
        :document-id="documentId"
        :node-id="selectedNodeId"
        @close="selectedNodeId = null"
        @view-source="(page, line, title) => emit('node-select-page', page, line, title)"
      />
    </div>
  </div>
</template>

<style scoped>
.tree-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.tree-viewer__toolbar {
  display: flex;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-bottom: 1px solid var(--color-border-light);
  background: var(--color-bg-primary);
  align-items: center;
}

.tree-viewer__search {
  flex: 1;
  padding: 8px 14px;
  border: 1px solid var(--color-border-light);
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  background: var(--color-bg-secondary);
  outline: none;
  transition: all var(--transition-fast);
  color: var(--color-text-primary);
}

.tree-viewer__search::placeholder {
  color: var(--color-text-muted);
}

.tree-viewer__search:focus {
  border-color: var(--color-accent);
  background: var(--color-bg-primary);
  box-shadow: 0 0 0 3px var(--color-accent-subtle);
}

.tree-viewer__actions {
  display: flex;
  gap: 4px;
}

.tree-viewer__btn {
  padding: 7px 10px;
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--border-radius-sm);
  background: var(--color-bg-secondary);
  transition: all var(--transition-fast);
  font-weight: 500;
}

.tree-viewer__btn:hover {
  background: var(--color-accent-ghost);
  color: var(--color-accent);
  border-color: var(--color-accent);
}

.tree-viewer__content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.tree-viewer__tree {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-xs) var(--space-xs) var(--space-sm);
}

.tree-viewer__empty {
  text-align: center;
  padding: var(--space-xl);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}
</style>
