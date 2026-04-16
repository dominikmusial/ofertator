import { useState, useCallback, useMemo } from 'react'
import { Offer } from './useEnhancedOffers'

export interface OfferFilters {
  search: string
  category_id: string
  price_from: string
  price_to: string
  offer_ids: string
  page: number
  pageSize: number
}

export function useOfferSelector() {
  const [selectedOffers, setSelectedOffers] = useState<Set<string>>(new Set())
  const [filters, setFilters] = useState<OfferFilters>({
    search: '',
    category_id: '',
    price_from: '',
    price_to: '',
    offer_ids: '',
    page: 1,
    pageSize: 25
  })

  // Selection management
  const toggleOffer = useCallback((offerId: string) => {
    setSelectedOffers(prev => {
      const newSelected = new Set(prev)
      if (newSelected.has(offerId)) {
        newSelected.delete(offerId)
      } else {
        newSelected.add(offerId)
      }
      return newSelected
    })
  }, [])

  const selectAll = useCallback((offers: Offer[]) => {
    setSelectedOffers(prev => {
      const newSelected = new Set(prev)
      offers.forEach(offer => newSelected.add(offer.id))
      return newSelected
    })
  }, [])

  const deselectAll = useCallback((offers: Offer[]) => {
    setSelectedOffers(prev => {
      const newSelected = new Set(prev)
      offers.forEach(offer => newSelected.delete(offer.id))
      return newSelected
    })
  }, [])

  const clearSelection = useCallback(() => {
    setSelectedOffers(new Set())
  }, [])

  // Filter management
  const updateFilter = useCallback(<K extends keyof OfferFilters>(
    key: K, 
    value: OfferFilters[K]
  ) => {
    setFilters(prev => ({ ...prev, [key]: value }))
    // Reset to first page when filters change (except for page/pageSize)
    if (key !== 'page' && key !== 'pageSize') {
      setFilters(prev => ({ ...prev, page: 1 }))
    }
  }, [])

  const clearFilters = useCallback(() => {
    setFilters({
      search: '',
      category_id: '',
      price_from: '',
      price_to: '',
      offer_ids: '',
      page: 1,
      pageSize: filters.pageSize // Keep page size
    })
  }, [filters.pageSize])

  // API-ready filters (convert empty strings to undefined)
  const apiFilters = useMemo(() => ({
    search: filters.search || undefined,
    category_id: filters.category_id || undefined,
    price_from: filters.price_from ? parseFloat(filters.price_from) : undefined,
    price_to: filters.price_to ? parseFloat(filters.price_to) : undefined,
    offer_ids: filters.offer_ids || undefined,
    page: filters.page,
    pageSize: filters.pageSize
  }), [filters])

  // Selected offers as array and formatted string
  const selectedOfferIds = useMemo(() => Array.from(selectedOffers), [selectedOffers])
  const selectedOffersText = useMemo(() => selectedOfferIds.join('\n'), [selectedOfferIds])

  // Load selected offers from text (for manual input parsing)
  const loadFromText = useCallback((text: string) => {
    const ids = text
      .split('\n')
      .map(id => id.trim())
      .filter(id => id.length > 0 && /^\d+$/.test(id))
    
    setSelectedOffers(new Set(ids))
  }, [])

  return {
    // Selection state
    selectedOffers,
    selectedOfferIds,
    selectedOffersText,
    
    // Selection actions
    toggleOffer,
    selectAll,
    deselectAll,
    clearSelection,
    loadFromText,
    
    // Filter state
    filters,
    apiFilters,
    
    // Filter actions
    updateFilter,
    clearFilters
  }
}
