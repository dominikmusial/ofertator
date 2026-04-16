import React, { useState, useEffect } from 'react'
import { useAuthStore } from '../../store/authStore'
import { useSharedAccounts } from '../../hooks/marketplaces/allegro/accounts'
import { usePermissions } from '../../hooks/shared/auth'
import { api } from '../../lib/api'
import { getDashboardModules, getGroupedModules, MARKETPLACES, filterModulesByMarketplace } from '../../config/moduleRegistry'
import { DashboardHeader } from '../../components/dashboard/DashboardHeader'
import { AdminOverview } from '../../components/dashboard/AdminOverview'
import { ModuleGrid } from '../../components/dashboard/ModuleGrid'
import { GettingStarted } from '../../components/dashboard/GettingStarted'
import { useFeatureFlags } from '../../hooks/shared/useFeatureFlags'

export default function Home() {
  const { user } = useAuthStore()
  const { accounts } = useSharedAccounts()
  const { getPermissionStatus } = usePermissions()
  const { isMarketplaceEnabled, isLoading: flagsLoading } = useFeatureFlags()
  const [adminStats, setAdminStats] = useState<any>(null)
  const [loadingStats, setLoadingStats] = useState(false)

  // Get modules from registry and filter by enabled marketplaces
  const allDashboardModules = getDashboardModules()
  const dashboardModules = filterModulesByMarketplace(allDashboardModules, isMarketplaceEnabled)
  const groupedModules = getGroupedModules(dashboardModules)

  // Calculate stats
  const accessibleModulesCount = dashboardModules.filter(module => {
    const permissionStatus = getPermissionStatus(module.id)
    return permissionStatus.hasAccess || module.isCore
  }).length

  useEffect(() => {
    if (user?.role === 'admin') {
      loadAdminStats()
    }
  }, [user])

  const loadAdminStats = async () => {
    try {
      setLoadingStats(true)
      const response = await api.get('/admin/dashboard/stats')
      setAdminStats(response.data)
    } catch (error) {
      console.error('Failed to load admin stats:', error)
    } finally {
      setLoadingStats(false)
    }
  }

  // Get accessible module IDs for passing to children
  const getAccessibleModuleIds = (modules: any[]) => {
    return modules
      .filter(m => getPermissionStatus(m.id).hasAccess)
      .map(m => m.id)
  }

  return (
    <div className="space-y-8 pb-12 w-full max-w-[1600px] mx-auto">
      <DashboardHeader 
        user={user} 
        stats={{
          accountsCount: accounts?.length || 0,
          featuresCount: accessibleModulesCount
        }}
      />

      {user?.role === 'admin' && (
        <AdminOverview stats={adminStats} isLoading={loadingStats} />
      )}

      {(!accounts || accounts.length === 0) && (
        <GettingStarted />
      )}

      <div className="space-y-10">
        {Array.from(groupedModules.entries())
          .filter(([marketplace]) => marketplace !== 'general')
          .sort((a, b) => MARKETPLACES[a[0]].order - MARKETPLACES[b[0]].order)
          .map(([marketplace, modules]) => (
            <ModuleGrid 
              key={marketplace}
              marketplace={marketplace}
              modules={modules}
              accessibleModules={getAccessibleModuleIds(modules)}
            />
          ))
        }
      </div>
    </div>
  )
}
