import apiClient from './client'

export const healthApi = {
  check: () => apiClient.get('/health').then((r) => r.data),
}
