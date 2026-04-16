/**
 * Route Generator - Dynamically creates routes from moduleRegistry
 * 
 * SOLID Principles:
 * - Single Responsibility: Generates React Router routes
 * - Open/Closed: Add modules to registry, routes generated automatically
 * - Liskov Substitution: All routes follow same protection pattern
 */

import { Route } from 'react-router-dom'
import { Suspense } from 'react'
import ProtectedRoute from '../components/auth/ProtectedRoute'
import { MODULE_REGISTRY, getAllRoutesForModule, filterModulesByMarketplace } from './moduleRegistry'
import { ROUTE_COMPONENT_MAP } from './routeComponentMap'

/**
 * Loading fallback for lazy-loaded components
 */
const LoadingFallback = () => (
  <div className="flex items-center justify-center h-64">
    <div className="flex flex-col items-center space-y-4">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      <p className="text-gray-500 text-sm">Ładowanie...</p>
    </div>
  </div>
)

/**
 * Generate routes for all modules in the registry
 * Returns an array of Route elements
 * @param isMarketplaceEnabled - Optional function to filter modules by marketplace
 */
export const generateModuleRoutes = (isMarketplaceEnabled?: (marketplace: string) => boolean) => {
  const routes: JSX.Element[] = []

  // Filter modules by marketplace if filter function provided
  const modulesToRender = isMarketplaceEnabled 
    ? filterModulesByMarketplace(MODULE_REGISTRY, isMarketplaceEnabled)
    : MODULE_REGISTRY

  console.log('🔄 Generating routes for', modulesToRender.length, 'modules', isMarketplaceEnabled ? '(filtered by feature flags)' : '')

  modulesToRender.forEach(module => {
    const Component = ROUTE_COMPONENT_MAP[module.id]
    
    if (!Component) {
      console.warn(`⚠️ No component mapped for module: ${module.id} (route: ${module.route})`)
      return
    }
    
    console.log(`✅ Route registered: ${module.route} → ${module.id}`)

    // Get all routes (main + legacy)
    const allRoutes = getAllRoutesForModule(module)

    allRoutes.forEach((routePath, index) => {
      const isLegacyRoute = index > 0
      const routeKey = isLegacyRoute ? `${module.id}-legacy-${index}` : module.id

      // Create element with Suspense for lazy loading
      const element = (
        <Suspense fallback={<LoadingFallback />}>
          <Component />
        </Suspense>
      )

      // Core modules don't require permission check
      if (module.isCore || module.requirePermission === false) {
        routes.push(
          <Route 
            key={routeKey} 
            path={routePath} 
            element={element}
          />
        )
      } else {
        // Protected route with permission check
        routes.push(
          <Route
            key={routeKey}
            path={routePath}
            element={
              <ProtectedRoute requireModule={module.id}>
                {element}
              </ProtectedRoute>
            }
          />
        )
      }
    })
  })

  return routes
}

/**
 * Special routes not in module registry (admin, profile, etc.)
 * @param featureFlags - Optional feature flag checker functions
 */
export const generateSpecialRoutes = (featureFlags?: {
  isAIConfigEnabled?: () => boolean
  isTeamAnalyticsEnabled?: () => boolean
  isAIUsageEnabled?: () => boolean
  isUserAIConfigEnabled?: () => boolean
}) => {
  const routes: JSX.Element[] = []
  
  // Profile routes - always accessible
  const ProfileComponent = ROUTE_COMPONENT_MAP['profil']
  if (ProfileComponent) {
    routes.push(
      <Route 
        key="profile" 
        path="/profile" 
        element={
          <Suspense fallback={<LoadingFallback />}>
            <ProfileComponent />
          </Suspense>
        } 
      />
    )
  }
  
  // User AI Config route - conditional based on feature flag
  const AIConfigComponent = ROUTE_COMPONENT_MAP['ai_config']
  if (AIConfigComponent && (!featureFlags?.isUserAIConfigEnabled || featureFlags.isUserAIConfigEnabled())) {
    routes.push(
      <Route 
        key="ai-config" 
        path="/profile/ai-config" 
        element={
          <Suspense fallback={<LoadingFallback />}>
            <AIConfigComponent />
          </Suspense>
        } 
      />
    )
  }
  
  // Simple user management (for clients - simplified version)
  const SimpleUserManagementComponent = ROUTE_COMPONENT_MAP['simple_user_management']
  if (SimpleUserManagementComponent) {
    routes.push(
      <Route 
        key="simple-user-management"
        path="/admin/users-simple" 
        element={
          <ProtectedRoute requireRole="admin">
            <Suspense fallback={<LoadingFallback />}>
              <SimpleUserManagementComponent />
            </Suspense>
          </ProtectedRoute>
        } 
      />
    )
  }
  
  // Admin routes - role-based protection (complex version - hidden for clients)
  const AdminUsersComponent = ROUTE_COMPONENT_MAP['admin_users']
  if (AdminUsersComponent) {
    routes.push(
      <Route 
        key="admin-users"
        path="/admin/users" 
        element={
          <ProtectedRoute requireRole="admin">
            <Suspense fallback={<LoadingFallback />}>
              <AdminUsersComponent />
            </Suspense>
          </ProtectedRoute>
        } 
      />
    )
  }
  
  const AdminAIPromptsComponent = ROUTE_COMPONENT_MAP['admin_ai_prompts']
  if (AdminAIPromptsComponent && (!featureFlags?.isAIConfigEnabled || featureFlags.isAIConfigEnabled())) {
    routes.push(
      <Route 
        key="admin-ai-prompts"
        path="/admin/ai-prompts" 
        element={
          <ProtectedRoute requireRole="admin">
            <Suspense fallback={<LoadingFallback />}>
              <AdminAIPromptsComponent />
            </Suspense>
          </ProtectedRoute>
        } 
      />
    )
  }
  
  // Team analytics - role-based
  const TeamAnalyticsComponent = ROUTE_COMPONENT_MAP['team_analytics']
  if (TeamAnalyticsComponent && (!featureFlags?.isTeamAnalyticsEnabled || featureFlags.isTeamAnalyticsEnabled())) {
    routes.push(
      <Route 
        key="team-analytics"
        path="/team-analytics" 
        element={
          <ProtectedRoute requireRole="vsprint_employee">
            <Suspense fallback={<LoadingFallback />}>
              <TeamAnalyticsComponent />
            </Suspense>
          </ProtectedRoute>
        } 
      />
    )
  }
  
  return routes
}
