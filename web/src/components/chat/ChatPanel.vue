<script setup>
import { computed, ref, watch, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'
import ChatMessage from './ChatMessage.vue'
import ChatInput from './ChatInput.vue'

const props = defineProps({
  documentId: { type: String, required: true },
})

const chatStore = useChatStore()
const messagesContainer = ref(null)

const messages = computed(() => chatStore.getMessages(props.documentId))
const isStreaming = computed(() => chatStore.streamingDocId === props.documentId)
const streamingMessage = computed(() => isStreaming.value ? chatStore.streamingMessage : null)

async function handleSend(question) {
  await chatStore.askQuestion(props.documentId, question)
}

async function handleClear() {
  if (confirm('Clear chat history?')) {
    await chatStore.clearHistory(props.documentId)
  }
}

// Auto-scroll to bottom
watch([messages, () => chatStore.streamingMessage?.content], async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
})
</script>

<template>
  <div class="chat-panel">
    <div class="chat-panel__header">
      <h3 class="chat-panel__title">💬 Document Q&A</h3>
      <button v-if="messages.length > 0" class="chat-panel__clear" @click="handleClear">Clear</button>
    </div>

    <div ref="messagesContainer" class="chat-panel__messages">
      <div v-if="messages.length === 0 && !streamingMessage" class="chat-panel__empty">
        <p>Ask a question about this document.</p>
        <p class="chat-panel__hint">The AI will search the document tree and provide an answer with references.</p>
      </div>

      <ChatMessage
        v-for="msg in messages"
        :key="msg.id"
        :message="msg"
      />

      <ChatMessage
        v-if="streamingMessage"
        :message="streamingMessage"
        :is-streaming="true"
      />
    </div>

    <ChatInput
      :disabled="isStreaming"
      @send="handleSend"
    />
  </div>
</template>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  border-left: 1px solid var(--color-border-light);
  background: var(--color-bg-primary);
}

.chat-panel__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--color-border-light);
  background: var(--color-bg-primary);
  box-shadow: var(--shadow-xs);
}

.chat-panel__title {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

.chat-panel__clear {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  padding: 5px 10px;
  border: 1px solid var(--color-border-light);
  border-radius: var(--border-radius-sm);
  background: var(--color-bg-secondary);
  font-weight: 500;
  transition: all var(--transition-fast);
}

.chat-panel__clear:hover {
  color: var(--color-error);
  border-color: var(--color-error);
  background: var(--color-error-bg);
}

.chat-panel__messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  background: var(--color-bg-subtle);
}

.chat-panel__empty {
  text-align: center;
  padding: var(--space-2xl);
  color: var(--color-text-muted);
  animation: fadeIn 0.4s ease-out;
}

.chat-panel__empty p:first-child {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text-secondary);
}

.chat-panel__hint {
  font-size: var(--text-sm);
  margin-top: var(--space-sm);
  line-height: 1.5;
}
</style>
