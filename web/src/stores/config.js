import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/config'

export const useConfigStore = defineStore('config', () => {
  const config = ref(null)
  const loading = ref(false)

  async function fetchConfig() {
    loading.value = true
    try {
      config.value = await api.getConfig()
    } catch (e) {
      console.error('Failed to fetch config:', e)
    } finally {
      loading.value = false
    }
  }

  async function saveConfig(data) {
    const result = await api.updateConfig(data)
    config.value = result
    return result
  }

  async function testLLMConnection(data) {
    return await api.testConnection(data)
  }

  return { config, loading, fetchConfig, saveConfig, testLLMConnection }
})
