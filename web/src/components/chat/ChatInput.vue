<script setup>
import { ref } from 'vue'

const props = defineProps({
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['send'])

const text = ref('')
const textarea = ref(null)

function handleSend() {
  const q = text.value.trim()
  if (!q || props.disabled) return
  emit('send', q)
  text.value = ''
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="chat-input">
    <div class="chat-input__wrapper">
      <textarea
        ref="textarea"
        v-model="text"
        class="chat-input__textarea"
        :placeholder="disabled ? 'Processing...' : 'Ask a question about this document...'"
        :disabled="disabled"
        rows="1"
        @keydown="handleKeydown"
      ></textarea>
      <button
        class="chat-input__send"
        :disabled="!text.trim() || disabled"
        @click="handleSend"
      >
        ➤
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat-input {
  padding: var(--space-sm) var(--space-lg) var(--space-md);
  border-top: 1px solid var(--color-border-light);
  background: var(--color-bg-primary);
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.02);
}

.chat-input__wrapper {
  display: flex;
  align-items: flex-end;
  gap: var(--space-sm);
  border: 1.5px solid var(--color-border-light);
  border-radius: var(--border-radius-lg);
  padding: var(--space-sm) var(--space-sm) var(--space-sm) var(--space-md);
  transition: all var(--transition-fast);
  background: var(--color-bg-primary);
  box-shadow: var(--shadow-xs);
}

.chat-input__wrapper:focus-within {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px var(--color-accent-subtle), var(--shadow-md);
}

.chat-input__textarea {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: var(--text-sm);
  line-height: 1.5;
  max-height: 100px;
  min-height: 24px;
  padding: 4px 0;
  background: transparent;
  color: var(--color-text-primary);
}

.chat-input__textarea::placeholder {
  color: var(--color-text-muted);
}

.chat-input__textarea:disabled {
  opacity: 0.5;
}

.chat-input__send {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gradient-accent);
  color: white;
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  flex-shrink: 0;
  transition: all var(--transition-fast);
  box-shadow: 0 2px 6px rgba(99, 102, 241, 0.25);
}

.chat-input__send:disabled {
  background: var(--color-bg-tertiary);
  box-shadow: none;
  cursor: not-allowed;
  color: var(--color-text-muted);
}

.chat-input__send:not(:disabled):hover {
  transform: scale(1.05);
  box-shadow: 0 3px 10px rgba(99, 102, 241, 0.35);
}

.chat-input__send:not(:disabled):active {
  transform: scale(0.98);
}
</style>
