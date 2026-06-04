<script setup>
import DocumentUpload from '@/components/document/DocumentUpload.vue'
</script>

<template>
  <div class="home-view">
    <div class="home-view__hero">
      <h2 class="home-view__title">Welcome to PageIndex</h2>
      <p class="home-view__desc">
        Upload a PDF or Markdown document to generate a hierarchical tree index,
        then ask questions using AI-powered reasoning retrieval.
      </p>
      <DocumentUpload />
    </div>
  </div>
</template>

<style scoped>
.home-view {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: var(--space-xl);
  background: var(--gradient-hero);
}

.home-view__hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: var(--space-md);
  animation: fadeIn 0.6s ease-out;
}

.home-view__title {
  font-size: 2.25rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  background: var(--gradient-accent);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.home-view__desc {
  font-size: var(--text-base);
  color: var(--color-text-secondary);
  max-width: 520px;
  line-height: 1.7;
  margin-bottom: var(--space-md);
  font-weight: 400;
}
</style>
