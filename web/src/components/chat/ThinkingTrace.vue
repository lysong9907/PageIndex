<script setup>
import { ref } from 'vue'

const props = defineProps({
  thinking: { type: String, required: true },
})

const expanded = ref(false)
</script>

<template>
  <div class="thinking-trace">
    <button class="thinking-trace__toggle" @click="expanded = !expanded">
      <span class="thinking-trace__icon">{{ expanded ? '▼' : '▶' }}</span>
      <span class="thinking-trace__label">{{ expanded ? 'Hide reasoning' : 'Show reasoning' }}</span>
    </button>
    <div v-show="expanded" class="thinking-trace__content">
      {{ thinking }}
    </div>
  </div>
</template>

<style scoped>
.thinking-trace {
  margin-bottom: var(--space-sm);
  border-radius: var(--border-radius);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  overflow: hidden;
  transition: all var(--transition-fast);
}

.thinking-trace__toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 12px;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  width: 100%;
  text-align: left;
  transition: all var(--transition-fast);
  font-weight: 500;
}

.thinking-trace__toggle:hover {
  color: var(--color-text-secondary);
  background: var(--color-bg-tertiary);
}

.thinking-trace__icon {
  font-size: 8px;
  transition: transform var(--transition-fast);
}

.thinking-trace__label {
  font-style: italic;
}

.thinking-trace__content {
  padding: 0 12px 12px;
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  font-family: var(--font-mono);
  line-height: 1.6;
  white-space: pre-wrap;
  background: var(--color-bg-primary);
  margin: 0 6px 6px;
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--border-radius-sm);
  border: 1px solid var(--color-border-light);
}
</style>
