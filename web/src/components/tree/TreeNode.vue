<script setup>
import { computed, inject } from 'vue'

const props = defineProps({
  node: { type: Object, required: true },
  depth: { type: Number, default: 0 },
})

const expandedNodeIds = inject('expandedNodeIds')
const selectedNodeId = inject('selectedNodeId')
const highlightedNodeIds = inject('highlightedNodeIds')
const toggleExpand = inject('toggleExpand')
const selectNode = inject('selectNode')

const hasChildren = computed(() => props.node.nodes?.length > 0)
const isExpanded = computed(() => expandedNodeIds.value.has(props.node.node_id))
const isSelected = computed(() => selectedNodeId.value === props.node.node_id)
const isHighlighted = computed(() => highlightedNodeIds.value.has(props.node.node_id))

const depthColors = ['#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#f43f5e', '#f97316', '#eab308']
const borderColor = computed(() => depthColors[props.depth % depthColors.length])
</script>

<template>
  <div
    class="tree-node"
    :class="{ 'tree-node--highlighted': isHighlighted, 'tree-node--selected': isSelected }"
    :style="{ marginLeft: `${depth * 16}px`, borderLeftColor: borderColor }"
    :data-node-id="node.node_id"
  >
    <div class="tree-node__header" @click="selectNode(node.node_id, node)">
      <button
        v-if="hasChildren"
        class="tree-node__toggle"
        @click.stop="toggleExpand(node.node_id)"
      >
        <span class="tree-node__chevron" :class="{ 'tree-node__chevron--open': isExpanded }">▶</span>
      </button>
      <span v-else class="tree-node__leaf"></span>

      <span class="tree-node__title">{{ node.title }}</span>

      <span v-if="node.node_id" class="tree-node__id">{{ node.node_id }}</span>
      <span v-if="node.start_index" class="tree-node__pages">
        p.{{ node.start_index }}<template v-if="node.end_index !== node.start_index">-{{ node.end_index }}</template>
      </span>
      <span v-else-if="node.line_num" class="tree-node__pages">
        #{{ node.line_num }}
      </span>
    </div>

    <div v-if="node.summary && isExpanded" class="tree-node__summary">
      {{ node.summary?.slice(0, 120) }}{{ node.summary?.length > 120 ? '...' : '' }}
    </div>

    <div v-show="isExpanded && hasChildren" class="tree-node__children">
      <TreeNode
        v-for="child in node.nodes"
        :key="child.node_id || child.title"
        :node="child"
        :depth="depth + 1"
      />
    </div>
  </div>
</template>

<style scoped>
.tree-node {
  border-left: 3px solid transparent;
  margin-bottom: 1px;
  border-radius: 0 var(--border-radius) var(--border-radius) 0;
  transition: all var(--transition-fast);
}

.tree-node--highlighted {
  background: var(--color-tree-highlight);
  animation: pulse 2s ease-in-out 3;
}

.tree-node--selected {
  background: var(--color-accent-light);
  border-left-color: var(--color-accent) !important;
}

.tree-node__header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  cursor: pointer;
  border-radius: var(--border-radius-sm);
  transition: all var(--transition-fast);
  margin: 1px 2px;
}

.tree-node__header:hover {
  background: var(--color-accent-ghost);
}

.tree-node__toggle {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--color-text-muted);
  font-size: 9px;
  transition: color var(--transition-fast);
}

.tree-node__header:hover .tree-node__toggle {
  color: var(--color-text-secondary);
}

.tree-node__chevron {
  display: inline-block;
  transition: transform var(--transition-fast);
}

.tree-node__chevron--open {
  transform: rotate(90deg);
}

.tree-node__leaf {
  width: 20px;
  flex-shrink: 0;
}

.tree-node__title {
  flex: 1;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color var(--transition-fast);
}

.tree-node__header:hover .tree-node__title {
  color: var(--color-accent);
}

.tree-node__id {
  font-size: 10px;
  font-family: var(--font-mono);
  color: var(--color-text-muted);
  background: var(--color-bg-tertiary);
  padding: 1px 6px;
  border-radius: var(--border-radius-sm);
  flex-shrink: 0;
  font-weight: 500;
}

.tree-node__pages {
  font-size: 10px;
  font-weight: 600;
  color: var(--color-accent);
  background: var(--color-accent-subtle);
  padding: 2px 7px;
  border-radius: var(--border-radius-sm);
  flex-shrink: 0;
}

.tree-node__summary {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  padding: 4px 10px 6px 30px;
  line-height: 1.5;
  animation: fadeIn 0.2s ease-out;
}

.tree-node__children {
  padding-left: 2px;
}
</style>
