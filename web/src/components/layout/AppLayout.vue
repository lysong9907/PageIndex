<script setup>
import { onMounted } from 'vue'
import { useDocumentsStore } from '@/stores/documents'
import AppSidebar from './AppSidebar.vue'

const documentsStore = useDocumentsStore()

onMounted(() => {
  documentsStore.fetchDocuments()
})
</script>

<template>
  <div class="app-layout">
    <AppSidebar class="app-layout__sidebar" />
    <main class="app-layout__main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--color-bg-primary);
}

.app-layout__sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  border-right: 1px solid var(--color-border-light);
  background: linear-gradient(180deg, var(--color-bg-subtle) 0%, var(--color-bg-secondary) 100%);
  box-shadow: 1px 0 0 rgba(0,0,0,0.02);
}

.app-layout__main {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-primary);
}
</style>
