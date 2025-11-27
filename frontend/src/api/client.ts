import axios from 'axios'
import { useAuthStore } from '../store/auth'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
})

// Add token to each request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto renew access-token with 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const refresh = useAuthStore.getState().refreshToken

    if (error.response?.status === 401 && refresh && !originalRequest._retry) {
      originalRequest._retry = true
      try {
        const resp = await axios.post(`${api.defaults.baseURL}/auth/refresh`, {
          refresh_token: refresh,
        })
        const { access_token, refresh_token } = resp.data
        useAuthStore.getState().setTokens(access_token, refresh_token)
        originalRequest.headers.Authorization = `Bearer ${access_token}`
        return api(originalRequest)
      } catch (_) {
        useAuthStore.getState().clear()
        window.location.href = '/'
      }
    }
    return Promise.reject(error)
  },
)

export default api
