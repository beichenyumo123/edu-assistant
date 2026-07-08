import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../utils/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || '')

  const isLoggedIn = computed(() => !!token.value)

  async function login(username, password) {
    const res = await api.post('/api/auth/login', { username, password })
    token.value = res.data.access_token
    user.value = res.data.user
    localStorage.setItem('token', token.value)
    return res.data
  }

  async function register(data) {
    const res = await api.post('/api/auth/register', data)
    token.value = res.data.access_token
    user.value = res.data.user
    localStorage.setItem('token', token.value)
    return res.data
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const res = await api.get('/api/auth/me')
      user.value = res.data.user
    } catch {
      logout()
    }
  }

  async function updateProfile(data) {
    const res = await api.put('/api/auth/me', data)
    user.value = res.data.user
    return res.data.user
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return { user, token, isLoggedIn, login, register, fetchUser, updateProfile, logout }
})
