import apiClient from './client'

export const documentsApi = {
  list: () => apiClient.get('/documents').then((r) => r.data),

  upload: (file, onUploadProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient
      .post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress,
      })
      .then((r) => r.data)
  },

  rename: (id, newFilename) =>
    apiClient.patch(`/documents/${id}`, { new_filename: newFilename }).then((r) => r.data),

  remove: (id) => apiClient.delete(`/documents/${id}`).then((r) => r.data),

  get: (id) => apiClient.get(`/documents/${id}`).then((r) => r.data),
}
