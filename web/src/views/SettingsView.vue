<script setup>
import LLMConfigForm from '@/components/settings/LLMConfigForm.vue'
</script>

<template>
  <div class="settings-view">
    <div class="settings-view__container">
      <h2 class="settings-view__title">⚙️ Settings</h2>
      <LLMConfigForm />
    </div>
  </div>
</template>

<style scoped>
.settings-view {
  padding: var(--space-xl);
  overflow-y: auto;
  height: 100%;
  background: var(--gradient-hero);
}

.settings-view__container {
  max-width: 600px;
  margin: 0 auto;
}

.settings-view__title {
  font-size: 1.75rem;
  font-weight: 800;
  margin-bottom: var(--space-xl);
  letter-spacing: -0.03em;
  background: var(--gradient-accent);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
</style>
