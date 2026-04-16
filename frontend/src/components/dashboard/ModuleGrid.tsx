import React from 'react'
import { Link } from 'react-router-dom'
import { ModuleConfig, MARKETPLACES } from '../../config/moduleRegistry'
import { ArrowRight, Lock } from 'lucide-react'

interface ModuleGridProps {
  marketplace: string
  modules: ModuleConfig[]
  accessibleModules: string[]
}

export const ModuleGrid: React.FC<ModuleGridProps> = ({ 
  marketplace, 
  modules, 
  accessibleModules 
}) => {
  // Sort modules: Accessible first, then by order
  const sortedModules = [...modules].sort((a, b) => {
    const aAccess = accessibleModules.includes(a.id)
    const bAccess = accessibleModules.includes(b.id)
    if (aAccess === bAccess) return a.order - b.order
    return aAccess ? -1 : 1
  })

  const marketplaceConfig = MARKETPLACES[marketplace as keyof typeof MARKETPLACES]
  const accessibleCount = accessibleModules.filter(id => modules.find(m => m.id === id)).length
  const totalCount = modules.length

  if (!marketplaceConfig) return null

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 border-b border-gray-100 pb-3">
        <span className="text-2xl">{marketplaceConfig.icon}</span>
        <h2 className="text-xl font-bold text-gray-900">
          {marketplaceConfig.name}
        </h2>
        <span className="text-sm text-gray-400 font-medium px-2 bg-gray-50 rounded-md">
          {accessibleCount}/{totalCount} dostępnych
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {sortedModules.map((module) => {
          const hasAccess = accessibleModules.includes(module.id)
          
          if (hasAccess) {
            return (
              <Link
                key={module.id}
                to={module.route}
                className="group relative bg-white p-5 rounded-xl border border-gray-200 shadow-sm hover:shadow-md hover:border-blue-300 transition-all duration-200 flex flex-col h-full"
              >
                <div className="flex items-start justify-between mb-3">
                  <span className="text-3xl group-hover:scale-110 transition-transform duration-200">
                    {module.icon}
                  </span>
                  {module.status === 'beta' && (
                    <span className="px-2 py-1 bg-purple-50 text-purple-700 text-xs font-semibold rounded-md border border-purple-100">
                      BETA
                    </span>
                  )}
                </div>
                
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 mb-1 group-hover:text-blue-600 transition-colors">
                    {module.name}
                  </h3>
                  <p className="text-sm text-gray-500 line-clamp-2">
                    {module.description}
                  </p>
                </div>

                <div className="mt-4 flex items-center text-blue-600 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity transform translate-y-1 group-hover:translate-y-0">
                  Otwórz <ArrowRight className="w-4 h-4 ml-1" />
                </div>
              </Link>
            )
          } else {
            // Show locked/blocked module
            return (
              <div
                key={module.id}
                className="relative bg-gray-50 p-5 rounded-xl border border-gray-200 border-dashed flex flex-col h-full cursor-not-allowed opacity-60"
              >
                <div className="flex items-start justify-between mb-3">
                  <span className="text-3xl grayscale">
                    {module.icon}
                  </span>
                  <div className="flex items-center gap-1 px-2 py-1 bg-gray-200 text-gray-600 text-xs font-semibold rounded-md">
                    <Lock className="w-3 h-3" />
                    ZABLOKOWANE
                  </div>
                </div>
                
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-600 mb-1">
                    {module.name}
                  </h3>
                  <p className="text-sm text-gray-400 line-clamp-2">
                    {module.description}
                  </p>
                </div>

                <div className="mt-4 text-xs text-gray-400">
                  Skontaktuj się z administratorem
                </div>
              </div>
            )
          }
        })}
      </div>
    </div>
  )
}
