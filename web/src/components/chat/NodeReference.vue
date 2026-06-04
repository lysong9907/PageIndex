<script setup>
import { useChatStore } from '@/stores/chat'

const props = defineProps({
  nodeId: { type: String, required: true },
})

const chatStore = useChatStore()

function handleClick() {
  chatStore.highlightedNodes = new Set([props.nodeId])
  // Scroll to the node in the tree viewer
  setTimeout(() => {
    const el = document.querySelector(`[data-node-id="${props.nodeId}"]`)
    el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, 100)
}
</script>

<template>
  <button class="node-ref" @click="handleClick" :title="`Node ${nodeId}`">
    📎 {{ nodeId }}
  </button>
</template>

<style scoped>
.node-ref {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  font-size: 11px;
  font-family: var(--font-mono);
  background: var(--color-accent-subtle);
  color: var(--color-accent);
  border: 1px solid var(--color-accent);
  border-radius: var(--border-radius-full);
  cursor: pointer;
  transition: all var(--transition-fast);
  font-weight: 500;
}

.node-ref:hover {
  background: var(--color-accent);
  color: white;
  box-shadow: 0 2px 6px rgba(99, 102, 241, 0.25);
  transform: translateY(-1px);
}
</style>
