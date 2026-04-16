import React, { useState, useEffect } from 'react'
import { Check, X, Lock, Unlock, AlertCircle, ChevronDown, ChevronRight } from 'lucide-react'
import { useToastStore } from '../../store/toastStore'
import { api } from '../../lib/api'

interface Module {
  id: number
  name: string
  display_name: string
  route_pattern: string
  description: string
  is_core: boolean
}

interface PermissionManagerProps {
  userId: number
  onPermissionsUpdated?: () => void
  showTitle?: boolean
}

export const PermissionManager: React.FC<PermissionManagerProps> = ({
  userId,
  onPermissionsUpdated,
  showTitle = true
}) => {
  const [modules, setModules] = useState<Module[]>([])
  const [permissions, setPermissions] = useState<Record<string, boolean>>({})
  const [dependencies, setDependencies] = useState<Record<string, string[]>>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({})
  const { addToast } = useToastStore()

  useEffect(() => {
    if (userId) {
      loadData()
    }
  }, [userId])

  const loadData = async () => {
    try {
      setLoading(true)
      
      // Load restricted modules
      const modulesResponse = await api.get('/admin/modules/restricted')
      setModules(modulesResponse.data)
      
      // Load user permissions
      const permissionsResponse = await api.get(`/admin/users/${userId}/permissions`)
      setPermissions(permissionsResponse.data.permissions || {})
      setDependencies(permissionsResponse.data.dependencies || {})
    } catch (error: any) {
      console.error('Failed to load permission data:', error)
      addToast('Nie udało się wczytać danych uprawnień', 'error')
    } finally {
      setLoading(false)
    }
  }

  // Permission toggle handlers
  const toggleModulePermission = (moduleName: string) => {
    const newPermissions = { ...permissions }
    const newValue = !newPermissions[moduleName]
    
    if (newValue) {
      // Grant permission
      newPermissions[moduleName] = true
      
      // Auto-grant dependencies
      const deps = dependencies[moduleName] || []
      deps.forEach(dep => {
        newPermissions[dep] = true
      })
    } else {
      // Revoke permission
      newPermissions[moduleName] = false
      
      // Auto-revoke modules that depend on this one
      Object.entries(dependencies).forEach(([parentModule, deps]) => {
        if (deps.includes(moduleName) && newPermissions[parentModule]) {
          newPermissions[parentModule] = false
        }
      })
    }
    
    setPermissions(newPermissions)
  }

  const toggleSectionPermissions = (sectionModules: Module[]) => {
    const sectionModuleNames = sectionModules.map(m => m.name)
    const allGranted = sectionModuleNames.every(name => permissions[name] === true)
    
    const newPermissions = { ...permissions }
    
    if (allGranted) {
      // Revoke all in section
      sectionModuleNames.forEach(moduleName => {
        newPermissions[moduleName] = false
        
        // Auto-revoke dependent modules
        Object.entries(dependencies).forEach(([parentModule, deps]) => {
          if (deps.includes(moduleName) && newPermissions[parentModule]) {
            newPermissions[parentModule] = false
          }
        })
      })
    } else {
      // Grant all in section
      sectionModuleNames.forEach(moduleName => {
        newPermissions[moduleName] = true
        
        // Auto-grant dependencies
        const deps = dependencies[moduleName] || []
        deps.forEach(dep => {
          newPermissions[dep] = true
        })
      })
    }
    
    setPermissions(newPermissions)
  }

  const savePermissions = async () => {
    try {
      setSaving(true)
      
      await api.post(`/admin/users/${userId}/permissions`, {
        permissions: permissions
      })
      
      addToast('Uprawnienia zostały zaktualizowane', 'success')
      onPermissionsUpdated?.()
    } catch (error: any) {
      console.error('Failed to save permissions:', error)
      addToast(error.response?.data?.detail || 'Nie udało się zapisać uprawnień', 'error')
    } finally {
      setSaving(false)
    }
  }

  const getDependencyInfo = (moduleName: string) => {
    const deps = dependencies[moduleName] || []
    const dependentOn = Object.entries(dependencies)
      .filter(([_, moduleDeps]) => moduleDeps.includes(moduleName))
      .map(([parentModule]) => parentModule)
    
    return { dependencies: deps, dependentOn }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {showTitle && (
        <div className="mb-4">
          <h3 className="text-lg font-medium text-gray-900">Uprawnienia modułów</h3>
          <p className="text-sm text-gray-500 mt-1">
            Zaznacz uprawnienia dla użytkownika i kliknij "Zapisz" aby zastosować zmiany
          </p>
        </div>
      )}

      <div className="space-y-6">
        {/* Group modules by marketplace - dynamic based on module name prefixes */}
        {(() => {
          // Dynamically detect marketplace prefixes from module names
          const marketplaceGroups = new Map<string, typeof modules>()
          const otherModules: typeof modules = []
          
          // Known marketplace configs with icons
          const marketplaceConfigs: Record<string, { name: string; icon: string; order: number }> = {
            'allegro': { name: 'Allegro', icon: '🟠', order: 1 },
            'decathlon': { name: 'Decathlon', icon: '🔵', order: 2 },
            'castorama': { name: 'Castorama', icon: '🟡', order: 3 },
            'leroymerlin': { name: 'Leroy Merlin', icon: '🟢', order: 4 }
          }
          
          // Group modules by detected marketplace prefix
          modules.forEach(module => {
            const prefix = module.name.split('_')[0]
            if (marketplaceConfigs[prefix]) {
              if (!marketplaceGroups.has(prefix)) {
                marketplaceGroups.set(prefix, [])
              }
              marketplaceGroups.get(prefix)!.push(module)
            } else {
              otherModules.push(module)
            }
          })
          
          // Sort marketplace groups by order
          const sortedMarketplaces = Array.from(marketplaceGroups.entries())
            .sort((a, b) => {
              const orderA = marketplaceConfigs[a[0]]?.order ?? 999
              const orderB = marketplaceConfigs[b[0]]?.order ?? 999
              return orderA - orderB
            })
          
          const renderModuleGroup = (title: string, icon: string, groupModules: typeof modules, sectionKey: string) => {
            if (groupModules.length === 0) return null
            
            const isExpanded = expandedSections[sectionKey] ?? false
            const sectionModuleNames = groupModules.map(m => m.name)
            const grantedInSection = sectionModuleNames.filter(name => permissions[name] === true).length
            const allGrantedInSection = grantedInSection === sectionModuleNames.length && sectionModuleNames.length > 0
            const someGrantedInSection = grantedInSection > 0 && grantedInSection < sectionModuleNames.length
            
            return (
              <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                <div className="px-4 py-3 bg-gradient-to-r from-gray-50 to-gray-100 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={allGrantedInSection}
                        ref={input => {
                          if (input) input.indeterminate = someGrantedInSection
                        }}
                        onChange={() => toggleSectionPermissions(groupModules)}
                        className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                        onClick={(e) => e.stopPropagation()}
                        title={allGrantedInSection ? 'Odbierz wszystkie' : 'Przyznaj wszystkie'}
                      />
                      <button
                        onClick={() => setExpandedSections(prev => ({ ...prev, [sectionKey]: !isExpanded }))}
                        className="flex items-center hover:opacity-80 transition-opacity"
                      >
                        <span className="text-2xl mr-2">{icon}</span>
                        <h3 className="text-base font-semibold text-gray-900 flex items-center">
                          {title}
                          {isExpanded ? (
                            <ChevronDown className="w-5 h-5 ml-2 text-gray-500" />
                          ) : (
                            <ChevronRight className="w-5 h-5 ml-2 text-gray-500" />
                          )}
                        </h3>
                      </button>
                    </div>
                    <span className="text-xs text-gray-500">
                      {grantedInSection > 0 && (
                        <span className="text-green-600 font-medium">{grantedInSection} / </span>
                      )}
                      {groupModules.length} modułów
                    </span>
                  </div>
                </div>
                
                {isExpanded && (
                  <>
                
                <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
                  <div className="grid grid-cols-12 gap-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <div className="col-span-1"></div>
                    <div className="col-span-7">Moduł</div>
                    <div className="col-span-4">Zależności</div>
                  </div>
                </div>
                
                <div className="divide-y divide-gray-200">
                  {groupModules.map((module) => {
                    const hasPermission = permissions[module.name] === true
                    const depInfo = getDependencyInfo(module.name)
                    
                    return (
                      <div 
                        key={module.id} 
                        className={`px-4 py-4 hover:bg-gray-50 transition-colors ${hasPermission ? 'bg-green-50' : ''}`}
                      >
                        <div className="grid grid-cols-12 gap-4 items-center">
                          <div className="col-span-1 flex items-center justify-center">
                            <input
                              type="checkbox"
                              checked={hasPermission}
                              onChange={() => toggleModulePermission(module.name)}
                              className="w-5 h-5 text-green-600 border-gray-300 rounded focus:ring-green-500 cursor-pointer"
                              title={hasPermission ? 'Odbierz uprawnienie' : 'Przyznaj uprawnienie'}
                            />
                          </div>
                          <div className="col-span-7">
                            <div>
                              <h4 className="text-sm font-medium text-gray-900 flex items-center gap-2">
                                {module.display_name}
                                {hasPermission && (
                                  <Check className="w-4 h-4 text-green-600" />
                                )}
                              </h4>
                              <p className="text-xs text-gray-500 mt-1">
                                {module.description}
                              </p>
                            </div>
                          </div>
                          
                          <div className="col-span-4">
                            {depInfo.dependencies.length > 0 && (
                              <div className="text-xs">
                                <span className="text-gray-500">Wymaga:</span>
                                <div className="mt-1">
                                  {depInfo.dependencies.map(dep => {
                                    const depModule = modules.find(m => m.name === dep)
                                    return (
                                      <span
                                        key={dep}
                                        className="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs mr-1 mb-1"
                                      >
                                        {depModule?.display_name || dep}
                                      </span>
                                    )
                                  })}
                                </div>
                              </div>
                            )}
                            {depInfo.dependentOn.length > 0 && (
                              <div className="text-xs mt-2">
                                <span className="text-gray-500">Wymagane przez:</span>
                                <div className="mt-1">
                                  {depInfo.dependentOn.map(parent => {
                                    const parentModule = modules.find(m => m.name === parent)
                                    return (
                                      <span
                                        key={parent}
                                        className="inline-block bg-amber-100 text-amber-800 px-2 py-1 rounded-full text-xs mr-1 mb-1"
                                      >
                                        {parentModule?.display_name || parent}
                                      </span>
                                    )
                                  })}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
                </>
                )}
              </div>
            )
          }
          
          return (
            <>
              {sortedMarketplaces.map(([prefix, groupModules]) => {
                const config = marketplaceConfigs[prefix]
                return renderModuleGroup(
                  config.name,
                  config.icon,
                  groupModules,
                  prefix
                )
              })}
              {otherModules.length > 0 && renderModuleGroup('Ogólne', '⚙️', otherModules, 'other')}
            </>
          )
        })()}
      </div>

      <div className="flex items-center justify-between pt-4 border-t border-gray-200">
        <div className="flex items-center text-sm text-gray-500">
          <AlertCircle className="h-4 w-4 mr-2" />
          Zmiany w zależnościach zostaną zastosowane automatycznie
        </div>
        
        <button
          onClick={savePermissions}
          disabled={saving}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Zapisywanie...
            </>
          ) : (
            <>
              <Check className="h-4 w-4 mr-2" />
              Zapisz uprawnienia
            </>
          )}
        </button>
      </div>
    </div>
  )
}

export default PermissionManager
