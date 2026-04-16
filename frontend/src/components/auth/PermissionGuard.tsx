import React from 'react'
import { usePermissions, ModuleName } from '../../hooks/shared/auth'

interface PermissionGuardProps {
  children: React.ReactNode
  module: ModuleName | string
  fallback?: React.ReactNode
  requireAll?: boolean // If multiple modules, require all or any
}

interface MultiplePermissionGuardProps {
  children: React.ReactNode
  modules: (ModuleName | string)[]
  fallback?: React.ReactNode
  requireAll?: boolean // Require all permissions or just any
}

/**
 * Component that conditionally renders children based on user permissions
 */
export const PermissionGuard: React.FC<PermissionGuardProps> = ({
  children,
  module,
  fallback = null
}) => {
  const { hasPermission } = usePermissions()
  
  if (hasPermission(module)) {
    return <>{children}</>
  }
  
  return <>{fallback}</>
}

/**
 * Component that checks multiple permissions
 */
export const MultiplePermissionGuard: React.FC<MultiplePermissionGuardProps> = ({
  children,
  modules,
  fallback = null,
  requireAll = false
}) => {
  const { hasAnyPermission, hasAllPermissions } = usePermissions()
  
  const hasAccess = requireAll 
    ? hasAllPermissions(modules)
    : hasAnyPermission(modules)
  
  if (hasAccess) {
    return <>{children}</>
  }
  
  return <>{fallback}</>
}

/**
 * Higher-order component for permission checking
 */
export const withPermission = (
  WrappedComponent: React.ComponentType<any>,
  requiredModule: ModuleName | string,
  fallbackComponent?: React.ComponentType
) => {
  return (props: any) => {
    const { hasPermission } = usePermissions()
    
    if (hasPermission(requiredModule)) {
      return <WrappedComponent {...props} />
    }
    
    if (fallbackComponent) {
      const FallbackComponent = fallbackComponent
      return <FallbackComponent {...props} />
    }
    
    return null
  }
}

export default PermissionGuard
