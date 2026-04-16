/**
 * Module Registry - Single Source of Truth for all modules/features
 * 
 * SOLID Principles:
 * - Single Responsibility: Each module config defines one feature
 * - Open/Closed: Easy to add new modules without changing existing code
 * - DRY: No duplication of module metadata across the app
 * 
 * This registry is used by:
 * - App.tsx (dynamic routing)
 * - Sidebar.tsx (dynamic navigation)
 * - Dashboard (module display)
 * - usePermissions (permission constants)
 */

export type MarketplaceType = 'allegro' | 'decathlon' | 'castorama' | 'leroymerlin' | 'general'

export interface ModuleConfig {
  // Core identification
  id: string // matches MODULES constant
  name: string // Display name
  description: string
  
  // Visual
  icon: string
  marketplace: MarketplaceType
  marketplaceIcon: string // e.g., '🟠', '🔵', '⚙️'
  
  // Routing
  route: string
  legacyRoutes?: string[] // Old routes for backward compatibility
  
  // Display settings
  showInDashboard: boolean
  showInSidebar: boolean
  order: number // Display order within marketplace group
  isCore: boolean // Core modules (dashboard, konta_marketplace, profil) always accessible
  
  // Status
  status: 'ready' | 'beta' | 'coming_soon'
  
  // Module dependencies (auto-granted)
  dependencies?: string[]
  
  // Permission requirement (for routes)
  requirePermission?: boolean // If false, route is public (default: true)
}

/**
 * Marketplace configurations
 */
export const MARKETPLACES = {
  allegro: {
    name: 'Allegro',
    icon: '🟠',
    order: 1
  },
  decathlon: {
    name: 'Decathlon', 
    icon: '🔵',
    order: 2
  },
  castorama: {
    name: 'Castorama',
    icon: '🟡',
    order: 3
  },
  leroymerlin: {
    name: 'Leroy Merlin',
    icon: '🟢',
    order: 4
  },
  general: {
    name: 'Ogólne',
    icon: '⚙️',
    order: 5
  }
} as const

/**
 * Module Registry - All modules defined here
 */
export const MODULE_REGISTRY: ModuleConfig[] = [
  // === CORE MODULES ===
  {
    id: 'dashboard',
    name: 'Dashboard',
    description: 'Strona główna z przeglądem modułów',
    icon: '🏠',
    marketplace: 'general',
    marketplaceIcon: MARKETPLACES.general.icon,
    route: '/',
    showInDashboard: false, // Dashboard itself is not shown in dashboard
    showInSidebar: false, // Shown separately in sidebar
    order: -1,
    isCore: true,
    status: 'ready',
    requirePermission: false // Core module, always accessible
  },
  {
    id: 'konta_marketplace',
    name: 'Integracje',
    description: 'Zarządzaj połączonymi kontami marketplace',
    icon: '👥',
    marketplace: 'general',
    marketplaceIcon: MARKETPLACES.general.icon,
    route: '/accounts',
    showInDashboard: false, // Utility feature, not a primary workflow
    showInSidebar: true,
    order: 0,
    isCore: true,
    status: 'ready',
    requirePermission: false // Core module, always accessible
  },
  
  // === ALLEGRO MODULES ===
  {
    id: 'allegro_edytor_ofert',
    name: 'Edytor Ofert',
    description: 'Masowa aktualizacja opisów z AI',
    icon: '✏️',
    marketplace: 'allegro',
    marketplaceIcon: MARKETPLACES.allegro.icon,
    route: '/allegro/offer-editor',
    legacyRoutes: ['/offer-editor'], // Backward compatibility
    showInDashboard: true,
    showInSidebar: true,
    order: 1,
    isCore: false,
    status: 'ready',
    dependencies: ['allegro_dodawanie_grafik', 'allegro_zapisane_zdjecia', 'zuzycie_ai']
  },
  {
    id: 'allegro_wystawianie_ofert',
    name: 'Wystawianie Ofert',
    description: 'Wystawiaj nowe oferty na Allegro',
    icon: '➕',
    marketplace: 'allegro',
    marketplaceIcon: MARKETPLACES.allegro.icon,
    route: '/allegro/create-offer',
    legacyRoutes: ['/create-offer'],
    showInDashboard: true,
    showInSidebar: true,
    order: 2,
    isCore: false,
    status: 'ready'
  },
  {
    id: 'allegro_kopiowanie_ofert',
    name: 'Kopiowanie Ofert',
    description: 'Kopiuj oferty między kontami',
    icon: '📋',
    marketplace: 'allegro',
    marketplaceIcon: MARKETPLACES.allegro.icon,
    route: '/allegro/copy-offers',
    legacyRoutes: ['/copy-offers'],
    showInDashboard: true,
    showInSidebar: true,
    order: 3,
    isCore: false,
    status: 'ready'
  },
  {
    id: 'allegro_promocje',
    name: 'Promocje',
    description: 'Zarządzaj promocjami i rabatami',
    icon: '🎯',
    marketplace: 'allegro',
    marketplaceIcon: MARKETPLACES.allegro.icon,
    route: '/allegro/promotions',
    legacyRoutes: ['/promotions'],
    showInDashboard: true,
    showInSidebar: true,
    order: 4,
    isCore: false,
    status: 'ready'
  },
  {
    id: 'allegro_harmonogram_cen',
    name: 'Harmonogram Cen',
    description: 'Automatyczne zmiany cen w czasie',
    icon: '📅',
    marketplace: 'allegro',
    marketplaceIcon: MARKETPLACES.allegro.icon,
    route: '/allegro/price-scheduler',
    legacyRoutes: ['/price-scheduler'],
    showInDashboard: true,
    showInSidebar: true,
    order: 5,
    isCore: false,
    status: 'ready'
  },
  {
    id: 'allegro_tytuly',
    name: 'Tytuły',
    description: 'Pobieraj, edytuj i przywracaj tytuły',
    icon: '📝',
    marketplace: 'allegro',
    marketplaceIcon: MARKETPLACES.allegro.icon,
    route: '/allegro/titles',
    legacyRoutes: ['/titles'],
    showInDashboard: true,
    showInSidebar: true,
    order: 6,
    isCore: false,
    status: 'ready'
  },
  {
    id: 'allegro_miniatury',
    name: 'Miniatury',
    description: 'Zarządzaj miniaturkami ofert',
    icon: '🖼️',
    marketplace: 'allegro',
    marketplaceIcon: MARKETPLACES.allegro.icon,
    route: '/allegro/thumbnails',
    legacyRoutes: ['/thumbnails'],
    showInDashboard: true,
    showInSidebar: true,
    order: 7,
    isCore: false,
    status: 'ready'
  },
  {
    id: 'allegro_podmiana_zdjec',
    name: 'Podmiana Zdjęć',
    description: 'Nakładaj kompozytowe obrazy',
    icon: '🔄',
    marketplace: 'allegro',
    marketplaceIcon: MARKETPLACES.allegro.icon,
    route: '/allegro/replace-images',
    legacyRoutes: ['/replace-images'],
    showInDashboard: true,
    showInSidebar: true,
    order: 8,
    isCore: false,
    status: 'ready'
  },
  {
    id: 'allegro_wylaczanie_ofert',
    name: 'Wyłączanie Ofert',
    description: 'Masowo zakańczaj lub przywracaj oferty',
    icon: '🔴',
    marketplace: 'allegro',
    marketplaceIcon: MARKETPLACES.allegro.icon,
    route: '/allegro/disable-offers',
    legacyRoutes: ['/disable-offers'],
    showInDashboard: true,
    showInSidebar: true,
    order: 9,
    isCore: false,
    status: 'ready'
  },
  {
    id: 'allegro_zdjecia_na_banerach',
    name: 'Zdjęcia na Banerach',
    description: 'Zarządzaj zdjęciami banerów',
    icon: '🏷️',
    marketplace: 'allegro',
    marketplaceIcon: MARKETPLACES.allegro.icon,
    route: '/allegro/banner-images',
    legacyRoutes: ['/banner-images'],
    showInDashboard: true,
    showInSidebar: true,
    order: 10,
    isCore: false,
    status: 'ready'
  },
  {
    id: 'allegro_karty_produktowe',
    name: 'Karty Produktowe',
    description: 'Generuj karty produktowe PDF',
    icon: '📄',
    marketplace: 'allegro',
    marketplaceIcon: MARKETPLACES.allegro.icon,
    route: '/allegro/product-cards',
    legacyRoutes: ['/product-cards'],
    showInDashboard: true,
    showInSidebar: true,
    order: 11,
    isCore: false,
    status: 'ready',
    dependencies: ['allegro_dodawanie_grafik']
  },
  
  // === ALLEGRO DEPENDENCY MODULES (auto-granted) ===
  {
    id: 'allegro_dodawanie_grafik',
    name: 'Dodawanie Grafik',
    description: 'Dodawaj i zarządzaj grafikami',
    icon: '🖨️',
    marketplace: 'allegro',
    marketplaceIcon: MARKETPLACES.allegro.icon,
    route: '/allegro/images',
    legacyRoutes: ['/images'],
    showInDashboard: false,
    showInSidebar: true,
    order: 12,
    isCore: false,
    status: 'ready'
  },
  {
    id: 'allegro_zapisane_zdjecia',
    name: 'Zapisane Zdjęcia',
    description: 'Zarządzaj zapisanymi obrazami',
    icon: '💾',
    marketplace: 'allegro',
    marketplaceIcon: MARKETPLACES.allegro.icon,
    route: '/allegro/saved-images',
    legacyRoutes: ['/saved-images'],
    showInDashboard: false,
    showInSidebar: true,
    order: 13,
    isCore: false,
    status: 'ready'
  },
  
  // === DECATHLON MODULES ===
  {
    id: 'decathlon_wystawianie_ofert',
    name: 'Wystawianie Ofert',
    description: 'Wystawianie nowych ofert na Decathlon',
    icon: '➕',
    marketplace: 'decathlon',
    marketplaceIcon: MARKETPLACES.decathlon.icon,
    route: '/decathlon/create-offer',
    showInDashboard: true,
    showInSidebar: true,
    order: 1,
    isCore: false,
    status: 'ready'
  },
  
  // === CASTORAMA MODULES ===
  {
    id: 'castorama_wystawianie_ofert',
    name: 'Wystawianie Ofert',
    description: 'Wystawianie nowych ofert na Castorama',
    icon: '➕',
    marketplace: 'castorama',
    marketplaceIcon: MARKETPLACES.castorama.icon,
    route: '/castorama/create-offer',
    showInDashboard: true,
    showInSidebar: true,
    order: 1,
    isCore: false,
    status: 'ready'
  },
  
  // === LEROY MERLIN MODULES ===
  {
    id: 'leroymerlin_wystawianie_ofert',
    name: 'Wystawianie Ofert',
    description: 'Wystawianie nowych ofert na Leroy Merlin',
    icon: '➕',
    marketplace: 'leroymerlin',
    marketplaceIcon: MARKETPLACES.leroymerlin.icon,
    route: '/leroymerlin/create-offer',
    showInDashboard: true,
    showInSidebar: true,
    order: 1,
    isCore: false,
    status: 'ready'
  },
  
  // === GENERAL/CROSS-MARKETPLACE MODULES ===
  {
    id: 'zuzycie_ai',
    name: 'Zużycie AI',
    description: 'Monitoruj zużycie tokenów AI',
    icon: '🤖',
    marketplace: 'general',
    marketplaceIcon: MARKETPLACES.general.icon,
    route: '/usage',
    showInDashboard: false,
    showInSidebar: true,
    order: 1,
    isCore: false,
    status: 'ready'
  }
]

/**
 * Utility functions for working with modules
 */

export const getModuleById = (id: string): ModuleConfig | undefined => {
  return MODULE_REGISTRY.find(m => m.id === id)
}

export const getModulesByMarketplace = (marketplace: MarketplaceType): ModuleConfig[] => {
  return MODULE_REGISTRY
    .filter(m => m.marketplace === marketplace)
    .sort((a, b) => a.order - b.order)
}

/**
 * Filter modules by marketplace enabled status
 * This function should be called with feature flag context
 */
export const filterModulesByMarketplace = (
  modules: ModuleConfig[],
  isMarketplaceEnabled: (marketplace: string) => boolean
): ModuleConfig[] => {
  return modules.filter(module => {
    // Always show core modules
    if (module.isCore) return true
    
    // For general modules, always show
    if (module.marketplace === 'general') return true
    
    // Check if marketplace is enabled
    return isMarketplaceEnabled(module.marketplace)
  })
}

export const getDashboardModules = (): ModuleConfig[] => {
  return MODULE_REGISTRY
    .filter(m => m.showInDashboard)
    .sort((a, b) => {
      // Sort by marketplace first, then by order
      const marketplaceOrderA = MARKETPLACES[a.marketplace].order
      const marketplaceOrderB = MARKETPLACES[b.marketplace].order
      
      if (marketplaceOrderA !== marketplaceOrderB) {
        return marketplaceOrderA - marketplaceOrderB
      }
      
      return a.order - b.order
    })
}

export const getSidebarModules = (): ModuleConfig[] => {
  return MODULE_REGISTRY
    .filter(m => m.showInSidebar)
    .sort((a, b) => a.order - b.order)
}

export const getModulesByIds = (ids: string[]): ModuleConfig[] => {
  return MODULE_REGISTRY.filter(m => ids.includes(m.id))
}

/**
 * Group modules by marketplace for display
 */
export const getGroupedModules = (modules: ModuleConfig[]) => {
  const grouped = new Map<MarketplaceType, ModuleConfig[]>()
  
  modules.forEach(module => {
    if (!grouped.has(module.marketplace)) {
      grouped.set(module.marketplace, [])
    }
    grouped.get(module.marketplace)!.push(module)
  })
  
  // Sort each group by order
  grouped.forEach((moduleList) => {
    moduleList.sort((a, b) => a.order - b.order)
  })
  
  return grouped
}

/**
 * Get all routes (including legacy) for a module
 */
export const getAllRoutesForModule = (module: ModuleConfig): string[] => {
  return [module.route, ...(module.legacyRoutes || [])]
}

/**
 * Generate type-safe module constants from registry
 * Used by usePermissions hook
 */
export const generateModuleConstants = () => {
  const constants: Record<string, string> = {}
  
  MODULE_REGISTRY.forEach(module => {
    // Convert id to CONSTANT_CASE (e.g., allegro_edytor_ofert -> ALLEGRO_EDYTOR_OFERT)
    const constantName = module.id.toUpperCase()
    constants[constantName] = module.id
  })
  
  return constants
}
