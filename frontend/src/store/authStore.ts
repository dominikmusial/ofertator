import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../lib/api'

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  is_active: boolean
  is_verified: boolean
  role: 'user' | 'admin' | 'vsprint_employee'
  company_domain?: string
  google_id?: string
  created_at: string
  accessible_accounts: number[]
  permissions?: Record<string, boolean>
}

export interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  permissions: Record<string, boolean>
}

export interface AuthActions {
  login: (email: string, password: string) => Promise<void>
  googleLogin: (token: string) => Promise<void>
  register: (userData: RegisterData) => Promise<void>
  logout: () => void
  forgotPassword: (email: string) => Promise<void>
  resetPassword: (token: string, password: string) => Promise<void>
  verifyEmail: (token: string) => Promise<void>
  resendVerification: (email: string) => Promise<void>
  refreshAuth: () => Promise<void>
  setLoading: (loading: boolean) => void
  setTokens: (accessToken: string, refreshToken: string) => Promise<void>
  canAccessAccount: (accountId: number) => boolean
  isVsprintEmployee: () => boolean
  getUserRole: () => string
  getCurrentUser: () => Promise<void>
  hasPermission: (moduleName: string) => boolean
  loadUserPermissions: (force?: boolean) => Promise<void>
  updatePermissions: (permissions: Record<string, boolean>) => void
  startPermissionRefresh: () => void
  stopPermissionRefresh: () => void
  initializePermissions: () => Promise<void>
}

export interface RegisterData {
  email: string
  password: string
  first_name: string
  last_name: string
}

type AuthStore = AuthState & AuthActions

// Note: Authentication interceptors are configured in lib/api.ts

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => {
      // Listen for auth refresh events from api.ts
      if (typeof window !== 'undefined') {
        window.addEventListener('auth:refresh-needed', async () => {
          const store = get()
          if (store.refreshToken) {
            try {
              await store.refreshAuth()
            } catch {
              store.logout()
            }
          } else {
            store.logout()
          }
        })
      }
      
      return {
      // State
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      permissions: {},

      // Actions
      setLoading: (loading: boolean) => set({ isLoading: loading }),

      setTokens: async (accessToken: string, refreshToken: string) => {
        set({
          token: accessToken,
          refreshToken: refreshToken,
          isAuthenticated: true
        })
        
        // Get user info after setting tokens
        const { getCurrentUser, loadUserPermissions, startPermissionRefresh } = get()
        try {
          await getCurrentUser()
          await loadUserPermissions(true) // Force refresh
          startPermissionRefresh()
        } catch (error) {
          console.error('Failed to load user data after setting tokens:', error)
        }
      },

      login: async (email: string, password: string) => {
        set({ isLoading: true })
        try {
          const response = await api.post('/auth/login', {
            email,
            password
          })
          
          const { access_token, refresh_token, user } = response.data
          
          set({
            user,
            token: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
            isLoading: false
          })
          
          // Load user permissions after successful login (force refresh)
          const { loadUserPermissions, startPermissionRefresh } = get()
          await loadUserPermissions(true) // Force refresh on login
          startPermissionRefresh()
        } catch (error: any) {
          set({ isLoading: false })
          throw new Error(error.response?.data?.detail || 'Logowanie nie powiodło się')
        }
      },

      googleLogin: async (token: string) => {
        set({ isLoading: true })
        try {
          const response = await api.post('/auth/google-login', {
            token
          })
          
          const { access_token, refresh_token, user } = response.data
          
          set({
            user,
            token: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
            isLoading: false
          })
          
          // Load user permissions after successful login (force refresh)
          const { loadUserPermissions, startPermissionRefresh } = get()
          await loadUserPermissions(true) // Force refresh on login
          startPermissionRefresh()
        } catch (error: any) {
          set({ isLoading: false })
          throw new Error(error.response?.data?.detail || 'Logowanie przez Google nie powiodło się')
        }
      },

      register: async (userData: RegisterData) => {
        set({ isLoading: true })
        try {
          await api.post('/auth/register', userData)
          set({ isLoading: false })
        } catch (error: any) {
          set({ isLoading: false })
          throw new Error(error.response?.data?.detail || 'Rejestracja nie powiodła się')
        }
      },

      logout: () => {
        const { stopPermissionRefresh } = get()
        stopPermissionRefresh()
        set({
          user: null,
          token: null,
          refreshToken: null,
          isAuthenticated: false,
          isLoading: false,
          permissions: {}
        })
      },

      forgotPassword: async (email: string) => {
        set({ isLoading: true })
        try {
          await api.post('/auth/forgot-password', { email })
          set({ isLoading: false })
        } catch (error: any) {
          set({ isLoading: false })
          throw new Error(error.response?.data?.detail || 'Nie udało się wysłać emaila resetującego')
        }
      },

      resetPassword: async (token: string, new_password: string) => {
        set({ isLoading: true })
        try {
          await api.post('/auth/reset-password', {
            token,
            new_password
          })
          set({ isLoading: false })
        } catch (error: any) {
          set({ isLoading: false })
          throw new Error(error.response?.data?.detail || 'Reset hasła nie powiódł się')
        }
      },

      verifyEmail: async (token: string) => {
        set({ isLoading: true })
        try {
          await api.post(`/auth/verify-email/${token}`)
          set({ isLoading: false })
        } catch (error: any) {
          set({ isLoading: false })
          throw new Error(error.response?.data?.detail || 'Weryfikacja emaila nie powiodła się')
        }
      },

      resendVerification: async (email: string) => {
        set({ isLoading: true })
        try {
          await api.post('/auth/resend-verification', { email })
          set({ isLoading: false })
        } catch (error: any) {
          set({ isLoading: false })
          throw new Error(error.response?.data?.detail || 'Nie udało się ponownie wysłać weryfikacji')
        }
      },

      refreshAuth: async () => {
        const { refreshToken } = get()
        if (!refreshToken) {
          throw new Error('Token odświeżania niedostępny')
        }

        try {
          const response = await api.post('/auth/refresh-token', {
            refresh_token: refreshToken
          })
          
          const { access_token, refresh_token, user } = response.data
          
          set({
            user,
            token: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true
          })
        } catch (error) {
          set({
            user: null,
            token: null,
            refreshToken: null,
            isAuthenticated: false
          })
          throw error
        }
      },

      getCurrentUser: async () => {
        try {
          const response = await api.get('/auth/me')
          set({ user: response.data })
          
          // Load user permissions after getting user info
          const { loadUserPermissions } = get()
          await loadUserPermissions()
        } catch (error) {
          console.error('Nie udało się pobrać danych użytkownika:', error)
        }
      },

      // Getters
      canAccessAccount: (accountId: number) => {
        const { user } = get()
        if (!user) return false
        
        // Admin can access everything
        if (user.role === 'admin') return true
        
        // Check if user has access to this account
        return user.accessible_accounts?.includes(accountId) || false
      },

      isVsprintEmployee: () => {
        const { user } = get()
        return user?.role === 'vsprint_employee' || user?.role === 'admin'
      },

      getUserRole: () => {
        const { user } = get()
        return user?.role || 'user'
      },

      hasPermission: (moduleName: string) => {
        const { user, permissions } = get()
        
        if (!user) return false
        
        // Core modules are always accessible
        const coreModules = ['dashboard', 'konta_marketplace', 'profil']
        if (coreModules.includes(moduleName)) return true
        
        // Admins and vsprint employees get all permissions
        if (user.role === 'admin' || user.role === 'vsprint_employee') return true
        
        // Check explicit permissions
        return permissions[moduleName] === true
      },

      loadUserPermissions: async (force = false) => {
        const { user } = get()
        if (!user) return
        
        // Throttle permission checks to avoid too many API calls (unless forced)
        if (!force) {
          const now = Date.now()
          const lastCheck = (window as any).__lastPermissionCheck || 0
          
          // Only check if more than 30 seconds have passed since last check
          if (now - lastCheck < 30000) {
            return
          }
        }
        
        try {
          const response = await api.get('/auth/me/permissions')
          const permissions = response.data.permissions || {}
          set({ permissions })
          ;(window as any).__lastPermissionCheck = Date.now()
        } catch (error) {
          console.error('Failed to load user permissions:', error)
          // If we can't load permissions, default to empty (restrictive)
          set({ permissions: {} })
        }
      },

      updatePermissions: (permissions: Record<string, boolean>) => {
        set({ permissions })
      },

      startPermissionRefresh: () => {
        const { user, loadUserPermissions } = get()
        if (!user) return

        // Refresh permissions every 2 minutes
        const refreshInterval = setInterval(async () => {
          const currentState = get()
          if (currentState.user && currentState.isAuthenticated) {
            await loadUserPermissions()
          } else {
            clearInterval(refreshInterval)
          }
        }, 2 * 60 * 1000) // 2 minutes

        // Refresh permissions when window gains focus
        const handleFocus = async () => {
          const currentState = get()
          if (currentState.user && currentState.isAuthenticated) {
            await loadUserPermissions()
          }
        }
        
        window.addEventListener('focus', handleFocus)

        // Store cleanup function
        ;(window as any).__authCleanup = () => {
          clearInterval(refreshInterval)
          window.removeEventListener('focus', handleFocus)
        }
      },

      stopPermissionRefresh: () => {
        if ((window as any).__authCleanup) {
          ;(window as any).__authCleanup()
          delete (window as any).__authCleanup
        }
      },

      initializePermissions: async () => {
        const { user, isAuthenticated, loadUserPermissions, startPermissionRefresh } = get()
        if (user && isAuthenticated) {
          await loadUserPermissions()
          startPermissionRefresh()
        }
      }
      }
    },
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
        permissions: state.permissions
      })
    }
  )
) 