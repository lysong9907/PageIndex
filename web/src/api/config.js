import { request } from './client'

export function getConfig() {
  return request('/config')
}

export function updateConfig(data) {
  return request('/config', { method: 'PATCH', body: data })
}

export function testConnection(data) {
  return request('/config/test-connection', { method: 'POST', body: data })
}
