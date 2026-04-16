/**
 * Route Component Map - Maps module IDs to their page components
 * 
 * SOLID Principles:
 * - Single Responsibility: Each component handles one page
 * - Open/Closed: Add new routes without modifying existing code
 * - Dependency Inversion: Depends on abstractions (ComponentType) not concrete implementations
 */

import { ComponentType, lazy } from 'react'

// Lazy load pages for better performance
// Dashboard
const Home = lazy(() => import('../pages/dashboard/Home'))
const TeamAnalytics = lazy(() => import('../pages/dashboard/TeamAnalytics'))
const Usage = lazy(() => import('../pages/dashboard/Usage'))

// Accounts
const Accounts = lazy(() => import('../pages/accounts/Accounts'))

// Allegro - Offers
const AllegroOfferEditor = lazy(() => import('../pages/allegro/offers/OfferEditor'))
const AllegroCreateOffer = lazy(() => import('../pages/allegro/offers/CreateOffer'))
const AllegroCopyOffers = lazy(() => import('../pages/allegro/offers/CopyOffers'))
const AllegroDisableOffers = lazy(() => import('../pages/allegro/offers/DisableOffers'))
const AllegroProductCards = lazy(() => import('../pages/allegro/offers/ProductCards'))
const AllegroTitles = lazy(() => import('../pages/allegro/offers/Titles'))

// Allegro - Images
const AllegroImages = lazy(() => import('../pages/allegro/images/Images'))
const AllegroBannerImages = lazy(() => import('../pages/allegro/images/BannerImages'))
const AllegroSavedImages = lazy(() => import('../pages/allegro/images/SavedImages'))
const AllegroThumbnails = lazy(() => import('../pages/allegro/images/Thumbnails'))
const AllegroReplaceImages = lazy(() => import('../pages/allegro/images/ReplaceImages'))

// Allegro - Promotions & Pricing
const AllegroPromotions = lazy(() => import('../pages/allegro/promotions/Promotions'))
const AllegroPriceScheduler = lazy(() => import('../pages/allegro/pricing/PriceScheduler'))

// Decathlon - Offers
const DecathlonCreateOffer = lazy(() => import('../pages/decathlon/offers/CreateOffer'))

// Castorama - Offers
const CastoramaCreateOffer = lazy(() => import('../pages/castorama/offers/CreateOffer'))

// Leroy Merlin - Offers
const LeroyMerlinCreateOffer = lazy(() => import('../pages/leroymerlin/offers/CreateOffer'))

// Admin & Profile
const AdminUsers = lazy(() => import('../pages/admin/AdminUsers'))
const SimpleUserManagement = lazy(() => import('../pages/admin/SimpleUserManagement'))
const AdminAIPrompts = lazy(() => import('../pages/admin/AdminAIPrompts'))
const Profile = lazy(() => import('../pages/profile/Profile'))
const AIConfig = lazy(() => import('../pages/profile/AIConfig'))

/**
 * Component map - Maps module IDs to their React components
 * This is the single source of truth for route -> component mapping
 */
export const ROUTE_COMPONENT_MAP: Record<string, ComponentType> = {
  // Core
  'dashboard': Home,
  'konta_marketplace': Accounts,
  'profil': Profile,
  'ai_config': AIConfig,
  
  // Allegro
  'allegro_edytor_ofert': AllegroOfferEditor,
  'allegro_wystawianie_ofert': AllegroCreateOffer,
  'allegro_kopiowanie_ofert': AllegroCopyOffers,
  'allegro_promocje': AllegroPromotions,
  'allegro_harmonogram_cen': AllegroPriceScheduler,
  'allegro_tytuly': AllegroTitles,
  'allegro_miniatury': AllegroThumbnails,
  'allegro_podmiana_zdjec': AllegroReplaceImages,
  'allegro_wylaczanie_ofert': AllegroDisableOffers,
  'allegro_zdjecia_na_banerach': AllegroBannerImages,
  'allegro_karty_produktowe': AllegroProductCards,
  'allegro_dodawanie_grafik': AllegroImages,
  'allegro_zapisane_zdjecia': AllegroSavedImages,
  
  // Decathlon
  'decathlon_wystawianie_ofert': DecathlonCreateOffer,
  
  // Castorama
  'castorama_wystawianie_ofert': CastoramaCreateOffer,
  
  // Leroy Merlin
  'leroymerlin_wystawianie_ofert': LeroyMerlinCreateOffer,
  
  // General
  'zuzycie_ai': Usage,
  
  // Admin (special routes, not in module registry)
  'admin_users': AdminUsers,
  'simple_user_management': SimpleUserManagement,
  'admin_ai_prompts': AdminAIPrompts,
  'team_analytics': TeamAnalytics,
}

/**
 * Get component for a module ID
 */
export const getComponentForModule = (moduleId: string): ComponentType | undefined => {
  return ROUTE_COMPONENT_MAP[moduleId]
}

/**
 * Check if a module has a registered component
 */
export const hasRegisteredComponent = (moduleId: string): boolean => {
  return moduleId in ROUTE_COMPONENT_MAP
}
