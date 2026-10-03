import axios from 'axios'

// In dev, Vite's proxy (see vite.config.js) forwards /api/* to the FastAPI
// backend on :8000. In production, set VITE_API_BASE_URL to the deployed
// backend's URL so the app doesn't depend on a proxy being configured there.
const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

export const apiClient = axios.create({
  baseURL,
  timeout: 60_000, // generous — RAG answers can take a few seconds through Groq
})

// Normalizes our backend's { error_code, message, details } envelope into a
// single shape every caller can rely on, instead of every hook re-deriving it.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const backendError = error.response?.data
    const normalized = {
      status: error.response?.status ?? null,
      errorCode: backendError?.error_code ?? 'network_error',
      message:
        backendError?.message ??
        (error.code === 'ECONNABORTED'
          ? 'The request timed out. Please try again.'
          : 'Could not reach the server. Is the backend running?'),
      details: backendError?.details ?? {},
    }
    return Promise.reject(normalized)
  }
)

export default apiClient
