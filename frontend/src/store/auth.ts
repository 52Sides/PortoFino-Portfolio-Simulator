import { create } from 'zustand'
import api from '../api/client'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  setTokens: (access: string, refresh: string) => void
  clear: () => void
  login: (email: string, password: string) => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),

  setTokens: (access, refresh) => {
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
    set({ accessToken: access, refreshToken: refresh })
  },

  clear: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ accessToken: null, refreshToken: null })
  },

  login: async (email: string, password: string) => {
    const params = new URLSearchParams()
    params.append('username', email)
    params.append('password', password)

    try {
      const response = await api.post('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      const { access_token, refresh_token } = response.data
      set({ accessToken: access_token, refreshToken: refresh_token })
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
    } catch (err: any) {
      console.error('Login failed', err.response?.data)
      throw err
    }
  },
}))
