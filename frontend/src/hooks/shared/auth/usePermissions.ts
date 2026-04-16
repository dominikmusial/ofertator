import { useAuthStore } from '../../../store/authStore'
import { MODULE_REGISTRY, getModuleById } from '../../../config/moduleRegistry'

/**
 * Hook for checking user permissions
 * 
 * SOLID Principles:
 * - Single Responsibility: Manages permission checking logic
 * - Dependency Inversion: Depends on moduleRegistry (abstraction) not hardcoded values
 */
export const usePermissions = () => {
  const hasPermission = useAuthStore((state) => state.hasPermission)
  const loadUserPermissions = useAuthStore((state) => state.loadUserPermissions)
  const permissions = useAuthStore((state) => state.permissions)
  const user = useAuthStore((state) => state.user)

  /**
   * Check if user has permission for a specific module
   */
  const checkPermission = (moduleName: string): boolean => {
    return hasPermission(moduleName)
  }

  /**
   * Check if user has any of the specified permissions
   */
  const hasAnyPermission = (moduleNames: string[]): boolean => {
    return moduleNames.some(moduleName => hasPermission(moduleName))
  }

  /**
   * Check if user has all of the specified permissions
   */
  const hasAllPermissions = (moduleNames: string[]): boolean => {
    return moduleNames.every(moduleName => hasPermission(moduleName))
  }

  /**
   * Get all user permissions as an object
   */
  const getAllPermissions = (): Record<string, boolean> => {
    return permissions
  }

  /**
   * Check if user is admin or vsprint employee (full access)
   */
  const hasFullAccess = (): boolean => {
    return user?.role === 'admin' || user?.role === 'vsprint_employee'
  }

  /**
   * Get permission status with reason
   */
  const getPermissionStatus = (moduleName: string): {
    hasAccess: boolean
    reason: 'core' | 'admin' | 'vsprint' | 'granted' | 'denied'
  } => {
    if (!user) return { hasAccess: false, reason: 'denied' }

    // Check if module is core (from registry)
    const module = getModuleById(moduleName)
    if (module?.isCore) {
      return { hasAccess: true, reason: 'core' }
    }

    if (user.role === 'admin') {
      return { hasAccess: true, reason: 'admin' }
    }

    if (user.role === 'vsprint_employee') {
      return { hasAccess: true, reason: 'vsprint' }
    }

    if (permissions[moduleName] === true) {
      return { hasAccess: true, reason: 'granted' }
    }

    return { hasAccess: false, reason: 'denied' }
  }

  return {
    hasPermission: checkPermission,
    hasAnyPermission,
    hasAllPermissions,
    getAllPermissions,
    hasFullAccess,
    getPermissionStatus,
    loadUserPermissions
  }
}

/**
 * Module name constants for type safety
 * Auto-generated from MODULE_REGISTRY (Single Source of Truth)
 */
export const MODULES = MODULE_REGISTRY.reduce((acc, module) => {
  // Convert id to CONSTANT_CASE (e.g., allegro_edytor_ofert -> ALLEGRO_EDYTOR_OFERT)
  const constantName = module.id.toUpperCase()
  acc[constantName] = module.id
  return acc
}, {} as Record<string, string>)

// Add special routes (not in registry)
export const SPECIAL_ROUTES = {
  ADMIN_USERS: 'admin_users',
  ADMIN_AI_PROMPTS: 'admin_ai_prompts',
  TEAM_ANALYTICS: 'team_analytics',
  PROFILE: 'profil',
  AI_CONFIG: 'ai_config',
  DASHBOARD: 'dashboard'
} as const

// Merge for convenience
export const ALL_MODULES = {
  ...MODULES,
  ...SPECIAL_ROUTES
} as const

export type ModuleName = typeof MODULES[keyof typeof MODULES]
