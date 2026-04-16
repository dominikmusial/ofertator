import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { usePermissions } from '../../hooks/shared/auth'
import { useAuthStore } from '../../store/authStore'
import PermissionGuard from '../auth/PermissionGuard'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { getSidebarModules, getGroupedModules, MARKETPLACES, type MarketplaceType, filterModulesByMarketplace } from '../../config/moduleRegistry'
import { useFeatureFlags } from '../../hooks/shared/useFeatureFlags'

/**
 * Sidebar Component - Dynamically generated from moduleRegistry
 * 
 * SOLID Principles:
 * - Single Responsibility: Displays navigation menu
 * - Open/Closed: Add new modules to registry, sidebar updates automatically
 * - Dependency Inversion: Depends on moduleRegistry (abstraction) not hardcoded menu
 */

interface SidebarGroupProps {
  title: string
  icon?: string
  children: React.ReactNode
  defaultOpen?: boolean
}

function SidebarGroup({ title, icon, children, defaultOpen = false }: SidebarGroupProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className="mb-2">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2 rounded text-sm text-gray-300 hover:bg-gray-700 transition"
      >
        <div className="flex items-center space-x-2">
          {icon && <span>{icon}</span>}
          <span className="font-medium">{title}</span>
        </div>
        {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      </button>
      {isOpen && <div className="ml-2 mt-1 space-y-1">{children}</div>}
    </div>
  )
}

export default function Sidebar() {
  const location = useLocation()
  const { user } = useAuthStore()
  const { isMarketplaceEnabled, isAIConfigEnabled, isTeamAnalyticsEnabled, isAIUsageEnabled, isLoading } = useFeatureFlags()

  // Get modules from registry and filter by enabled marketplaces
  const allSidebarModules = getSidebarModules()
  const sidebarModules = filterModulesByMarketplace(allSidebarModules, isMarketplaceEnabled)
    .filter(module => {
      // Filter out disabled modules
      if (module.id === 'zuzycie_ai' && !isAIUsageEnabled()) return false
      return true
    })
  const groupedModules = getGroupedModules(sidebarModules)

  const linkClass = (path: string) =>
    `block rounded px-3 py-2 text-sm transition ${
      location.pathname === path ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-700'
    }`

  // Sort marketplaces by order
  const sortedMarketplaces = Array.from(groupedModules.entries())
    .sort((a, b) => MARKETPLACES[a[0]].order - MARKETPLACES[b[0]].order)

  return (
    <aside className="w-64 flex-shrink-0 bg-gray-900 text-white flex flex-col">
      <div className="px-6 py-4 text-2xl font-bold tracking-wide border-b border-gray-700">
        Ofertator
      </div>
      <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto sidebar-scrollbar">
        {/* Show loading skeleton while feature flags are loading */}
        {isLoading ? (
          <div className="space-y-4 animate-pulse">
            <div className="h-8 bg-gray-700 rounded"></div>
            <div className="h-8 bg-gray-700 rounded"></div>
            <div className="h-8 bg-gray-700 rounded"></div>
            <div className="space-y-2 pt-4">
              <div className="h-6 bg-gray-800 rounded w-3/4"></div>
              <div className="h-6 bg-gray-800 rounded w-2/3"></div>
            </div>
          </div>
        ) : (
          <>
        {/* Global Section */}
        <div className="mb-4">
          <div className="text-xs text-gray-400 uppercase tracking-wider mb-2 px-3">
            Główne
          </div>
          <Link className={linkClass('/')} to="/">
            Dashboard
          </Link>
          
          {/* Core modules from registry (general marketplace) */}
          {groupedModules.get('general')?.map(module => (
            <PermissionGuard key={module.id} module={module.id}>
              <Link className={linkClass(module.route)} to={module.route}>
                {module.icon && <span className="mr-2">{module.icon}</span>}
                {module.name}
              </Link>
            </PermissionGuard>
          ))}
        </div>

        {/* Marketplace Sections - Dynamically generated */}
        {sortedMarketplaces
          .filter(([marketplace]) => marketplace !== 'general') // General handled above
          .map(([marketplace, modules]) => {
            const marketplaceConfig = MARKETPLACES[marketplace as MarketplaceType]
            const isAllegro = marketplace === 'allegro'
            
            return (
              <SidebarGroup 
                key={marketplace}
                title={marketplaceConfig.name} 
                icon={marketplaceConfig.icon}
                defaultOpen={isAllegro} // Allegro open by default
              >
                {modules.map(module => (
                  <PermissionGuard key={module.id} module={module.id}>
                    <Link className={linkClass(module.route)} to={module.route}>
                      {module.name}
                      {module.status === 'beta' && (
                        <span className="ml-2 text-xs bg-purple-600 px-1.5 py-0.5 rounded">
                          BETA
                        </span>
                      )}
                    </Link>
                  </PermissionGuard>
                ))}
              </SidebarGroup>
            )
          })}

        {/* Analytics Section */}
        {(user?.role === 'vsprint_employee' || user?.role === 'admin') && isTeamAnalyticsEnabled() && (
          <div className="border-t border-gray-700 my-4 pt-4">
            <div className="text-xs text-gray-400 uppercase tracking-wider mb-2 px-3">
              Analityka
            </div>
            {user?.role === 'vsprint_employee' || user?.role === 'admin' ? (
              <Link className={linkClass('/team-analytics')} to="/team-analytics">
                Analityka Zespołu
              </Link>
            ) : null}
          </div>
        )}

        {/* Admin Section */}
        {user?.role === 'admin' && (
          <div className="border-t border-gray-700 my-4 pt-4">
            <div className="text-xs text-gray-400 uppercase tracking-wider mb-2 px-3">
              Administracja
            </div>
            <Link className={linkClass('/admin/users-simple')} to="/admin/users-simple">
              Zarządzanie użytkownikami
            </Link>
            {isAIConfigEnabled() && (
              <Link className={linkClass('/admin/ai-prompts')} to="/admin/ai-prompts">
                Konfiguracja AI
              </Link>
            )}
          </div>
        )}
        </>
        )}
      </nav>

      {/* User info in sidebar */}
      {user && (
        <div className="px-4 py-4 border-t border-gray-700">
          <div className="text-sm text-gray-300">
            <div className="font-medium">
              {user.first_name} {user.last_name}
            </div>
            <div className="text-xs text-gray-400">
              {user.role === 'admin' ? 'Administrator' : 'Użytkownik'}
            </div>
            {!user.is_verified && (
              <div className="text-xs text-yellow-400 mt-1">⚠️ Email nie zweryfikowany</div>
            )}
          </div>
        </div>
      )}
    </aside>
  )
}
