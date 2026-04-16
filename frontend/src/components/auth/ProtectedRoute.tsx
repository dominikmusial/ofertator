import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { usePermissions, ModuleName } from '../../hooks/shared/auth'
import { useEffect } from 'react'

interface ProtectedRouteProps {
  children: React.ReactNode
  requireRole?: 'admin' | 'vsprint_employee'
  requireModule?: ModuleName | string
}

export default function ProtectedRoute({ children, requireRole, requireModule }: ProtectedRouteProps) {
  const { isAuthenticated, user, getCurrentUser, token } = useAuthStore()
  const { hasPermission } = usePermissions()
  const location = useLocation()

  // Try to get current user info if we have a token but no user
  useEffect(() => {
    if (token && !user) {
      getCurrentUser()
    }
  }, [token, user, getCurrentUser])

  // Not authenticated - redirect to login
  if (!isAuthenticated || !token) {
    return <Navigate to="/auth/login" state={{ from: location }} replace />
  }

  // Still loading user data
  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  // User not verified
  if (!user.is_verified) {
    return <Navigate to="/auth/verify-required" replace />
  }

  // User not active
  if (!user.is_active) {
    return <Navigate to="/auth/account-disabled" replace />
  }

  // Check role requirements
  if (requireRole) {
    if (requireRole === 'admin' && user.role !== 'admin') {
      return <Navigate to="/unauthorized" replace />
    }
    
    if (requireRole === 'vsprint_employee' && 
        !['admin', 'vsprint_employee'].includes(user.role)) {
      return <Navigate to="/unauthorized" replace />
    }
  }

  // Check module permissions
  if (requireModule && !hasPermission(requireModule)) {
    return <Navigate to="/unauthorized" replace />
  }

  return <>{children}</>
} 