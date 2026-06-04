<script setup>
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import ThinkingTrace from './ThinkingTrace.vue'
import NodeReference from './NodeReference.vue'

const props = defineProps({
  message: { type: Object, required: true },
  isStreaming: { type: Boolean, default: false },
})

const md = new MarkdownIt({ html: false, linkify: true })

const renderedContent = computed(() => {
  if (props.message.role === 'user') return ''
  return md.render(props.message.content || '')
})
</script>

<template>
  <div class="chat-msg" :class="`chat-msg--${message.role}`">
    <!-- User message -->
    <div v-if="message.role === 'user'" class="chat-msg__bubble chat-msg__bubble--user">
      {{ message.content }}
    </div>

    <!-- Assistant message -->
    <div v-else class="chat-msg__bubble chat-msg__bubble--assistant">
      <ThinkingTrace v-if="message.thinking" :thinking="message.thinking" />

      <div
        v-if="message.content"
        class="chat-msg__content markdown-body"
        v-html="renderedContent"
      ></div>

      <span v-if="isStreaming && !message.content" class="chat-msg__phase">
        {{ message.phase === 'tree_search' ? '🔍 Searching document tree...' : '✍️ Generating answer...' }}
      </span>

      <span v-if="isStreaming" class="chat-msg__cursor">▊</span>

      <div v-if="message.referenced_nodes?.length" class="chat-msg__refs">
        <span class="chat-msg__refs-label">Referenced:</span>
        <NodeReference
          v-for="nodeId in message.referenced_nodes"
          :key="nodeId"
          :node-id="nodeId"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-msg--user {
  display: flex;
  justify-content: flex-end;
  animation: slideIn 0.25s ease-out;
}

.chat-msg--assistant {
  display: flex;
  justify-content: flex-start;
  animation: slideIn 0.25s ease-out;
}

.chat-msg__bubble {
  max-width: 85%;
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--border-radius-lg);
  font-size: var(--text-sm);
  line-height: 1.65;
  box-shadow: var(--shadow-xs);
}

.chat-msg__bubble--user {
  background: var(--gradient-accent);
  color: var(--color-user-text);
  border-bottom-right-radius: 4px;
}

.chat-msg__bubble--assistant {
  background: var(--color-bg-primary);
  color: var(--color-assistant-text);
  border-bottom-left-radius: 4px;
  border: 1px solid var(--color-border-light);
}

.chat-msg__content :deep(p) {
  margin-bottom: 0.6em;
}
.chat-msg__content :deep(p:last-child) {
  margin-bottom: 0;
}
.chat-msg__content :deep(code) {
  background: rgba(99, 102, 241, 0.08);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 0.85em;
  color: var(--color-accent);
  font-weight: 500;
}
.chat-msg__content :deep(pre) {
  background: #1a1a2e;
  color: #e2e8f0;
  padding: var(--space-md);
  border-radius: var(--border-radius);
  overflow-x: auto;
  margin: var(--space-sm) 0;
  box-shadow: var(--shadow-inset);
}
.chat-msg__content :deep(pre code) {
  background: transparent;
  color: inherit;
  padding: 0;
}
.chat-msg__content :deep(ul), .chat-msg__content :deep(ol) {
  padding-left: 1.5em;
  margin: 0.5em 0;
}
.chat-msg__content :deep(h1), .chat-msg__content :deep(h2), .chat-msg__content :deep(h3) {
  font-weight: 700;
  margin: 1em 0 0.5em;
  letter-spacing: -0.02em;
}
.chat-msg__content :deep(blockquote) {
  border-left: 3px solid var(--color-accent);
  padding-left: var(--space-md);
  color: var(--color-text-secondary);
  margin: var(--space-sm) 0;
}

.chat-msg__phase {
  display: block;
  color: var(--color-text-muted);
  font-style: italic;
  font-size: var(--text-xs);
  padding: 2px 0;
}

.chat-msg__cursor {
  animation: blink 1s step-end infinite;
  color: var(--color-accent);
}

.chat-msg__refs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: var(--space-sm);
  padding-top: var(--space-sm);
  border-top: 1px solid var(--color-border-light);
  align-items: center;
}

.chat-msg__refs-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  font-weight: 600;
}
</style>
