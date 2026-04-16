import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { useAuthStore } from '../../../store/authStore'

/**
 * Hook that refreshes permissions on route navigation
 * This ensures permissions are up-to-date when users navigate between pages
 */
export const usePermissionGuard = () => {
  const location = useLocation()
  const loadUserPermissions = useAuthStore((state) => state.loadUserPermissions)
  const user = useAuthStore((state) => state.user)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  useEffect(() => {
    // Refresh permissions on route change if user is authenticated
    if (user && isAuthenticated) {
      loadUserPermissions()
    }
  }, [location.pathname, user, isAuthenticated, loadUserPermissions])

  useEffect(() => {
    // Refresh permissions when page becomes visible (handles refresh, tab switching)
    const handleVisibilityChange = () => {
      if (!document.hidden && user && isAuthenticated) {
        loadUserPermissions()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [user, isAuthenticated, loadUserPermissions])
}

export default usePermissionGuard
