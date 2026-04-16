import { useState, useEffect, useRef } from 'react'
import { useAccountStore } from '../../../store/accountStore'
import { useToastStore } from '../../../store/toastStore'
import AccountSelector from '../../../components/ui/AccountSelector'
import Modal from '../../../components/ui/Modal'
import api from '../../../lib/api'
import { parseFile } from '../../../utils/fileParser'

interface Product {
  id: string
  name: string
  category: {
    id: string
    path: Array<{ id: string; name: string }>
  }
  images?: Array<{ url: string }>
  parameters?: Array<{
    id: string
    name: string
    values?: string[]
    valuesIds?: string[]
    type?: string
  }>
}

interface ProductDetails {
  id: string
  name: string
  category: {
    id: string
    path: Array<{ id: string; name: string }>
  }
  images?: Array<{ url: string }>
  parameters?: Array<{
    id: string
    name: string
    values?: string[] | string  // Can be string (JSON) or array
    valuesIds?: string[] | string  // Can be string (JSON) or array
    type?: string
    required?: boolean
    requiredForProduct?: boolean
  }>
  offerRequirements?: {
    parameters: Array<{
      id: string
      name: string
      required: boolean
    }>
  }
}

interface CategoryParameter {
  id: string
  name: string
  type: string
  required: boolean
  requiredForProduct?: boolean
  requiredIf?: {
    parametersWithValue?: Array<{
      id: string
      oneOfValueIds?: string[]
    }>
    parametersWithoutValue?: string[]
  }
  displayedIf?: {
    parametersWithValue?: Array<{
      id: string
      oneOfValueIds?: string[]
    }>
    parametersWithoutValue?: string[]
  }
  restrictions?: {
    min?: number
    max?: number
  }
  dictionary?: Array<{
    id: string
    value: string
    dependsOnValueIds?: string[]
  }>  // Dictionary can be directly on parameter (from category parameters API)
  options?: {
    describesProduct?: boolean
    identifiesProduct?: boolean  // Alternative name for describesProduct
    dictionary?: Array<{
      id: string
      value: string
      dependsOnValueIds?: string[]
    }>  // Dictionary can also be nested in options (fallback)
  }
  values?: Array<{
    name?: string
    value?: string
  }> | string[]  // Can be array of objects or strings
  valuesLabels?: string[]  // Labels for dictionary/select values
  valuesIds?: string[]     // IDs for dictionary/select values
  unit?: string            // Unit of measurement (e.g., "g", "kg", "ml")
}

interface ShippingRate {
  id: string
  name: string
  marketplaces?: Array<{ id: string }>
}

interface LogEntry {
  timestamp: string
  level: 'info' | 'success' | 'error'
  message: string
}

interface OfferConfig {
  ean: string
  products: Product[]  // Wszystkie produkty dla tego EAN
  selectedProductId: string | null  // ID wybranego produktu
  selectedProductDetails: ProductDetails | null  // Szczegóły wybranego produktu
  categoryParameters: CategoryParameter[]  // Parametry kategorii dla tej oferty (per-offer)
  offerName: string
  price: string
  stock: string
  selectedParameters: Record<string, any>
  selectedOfferParameters: Record<string, any>
  selectedShippingRate: string
  handlingTime: string
  sku: string
  duration: string
  durationType: 'fixed' | 'unlimited'
  returnPolicyId: string
  selectedResponsibleProducerId: string
  selectedResponsiblePersonId: string
  safetyInformation: string
  invoiceType: string
  selectedTaxRates: Record<string, string>
  selectedTaxSubject: string
  selectedTaxExemption: string
}

export default function CreateOffer() {
  const { current } = useAccountStore()
  const { addToast, removeToast, updateToast } = useToastStore()
  
  const [ean, setEan] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [searchProgress, setSearchProgress] = useState<{ current: number; total: number } | null>(null)  // Progress for EAN search
  const [loadingOffers, setLoadingOffers] = useState<Set<string>>(new Set())  // Track which offers are loading
  const [isCreating, setIsCreating] = useState(false)
  const [loadingProgress, setLoadingProgress] = useState<{ current: number; total: number } | null>(null)
  const progressToastIdRef = useRef<string | null>(null)  // Store ID of progress toast to update it
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(50)  // Fixed page size
  
  // Publication status: "ACTIVE" for published offer, "INACTIVE" for draft (global for all offers)
  const [publicationStatus, setPublicationStatus] = useState<'ACTIVE' | 'INACTIVE'>('ACTIVE')
  
  // CSV import data - stores data from CSV for each EAN
  const [csvData, setCsvData] = useState<Record<string, {
    title?: string
    price?: string
    sku?: string
    stock?: string
    selectedShippingRate?: string
    handlingTime?: string
    duration?: string
    durationType?: 'fixed' | 'unlimited'
    returnPolicyId?: string
    selectedResponsibleProducerId?: string
    selectedResponsiblePersonId?: string
    safetyInformation?: string
    invoiceType?: string
    selectedTaxRates?: Record<string, string>
    selectedTaxSubject?: string
    selectedTaxExemption?: string
  }>>({})
  
  // New structure: offers array (prepared for multiple, but starting with one)
  const [offers, setOffers] = useState<OfferConfig[]>([])
  const currentOffer = offers.length > 0 ? offers[0] : null
  
  // Expanded sections state
  const [expandedParams, setExpandedParams] = useState<Record<string, boolean>>({})
  const [expandedData, setExpandedData] = useState<Record<string, boolean>>({})
  
  // Product selector modal state
  const [showProductSelectorModal, setShowProductSelectorModal] = useState(false)
  const [currentEanForModal, setCurrentEanForModal] = useState<string>('')
  
  // Bulk operations state
  const [selectedOffers, setSelectedOffers] = useState<Set<number>>(new Set())
  const [expandedBulkSections, setExpandedBulkSections] = useState<Set<string>>(new Set())
  const [bulkSettings, setBulkSettings] = useState<Partial<Pick<OfferConfig, 
    'selectedShippingRate' | 'handlingTime' | 'sku' | 'duration' | 'durationType' | 
    'returnPolicyId' | 'selectedResponsibleProducerId' | 'selectedResponsiblePersonId' | 
    'safetyInformation' | 'invoiceType' | 'selectedTaxRates' | 'selectedTaxSubject' | 'selectedTaxExemption'
  >>>({})
  
  // Shared settings (loaded once per account)
  const [categoryParameters, setCategoryParameters] = useState<CategoryParameter[]>([])
  const [shippingRates, setShippingRates] = useState<ShippingRate[]>([])
  const [returnPolicies, setReturnPolicies] = useState<Array<{ id: string; name: string }>>([])
  const [responsibleProducers, setResponsibleProducers] = useState<Array<{ id: string; name: string }>>([])
  const [responsiblePersons, setResponsiblePersons] = useState<Array<{ id: string; name: string }>>([])
  const [taxSettings, setTaxSettings] = useState<{ subjects: Array<{ label: string; value: string }>, rates: Array<{ countryCode: string; values: Array<{ label: string; value: string; exemptionRequired: boolean }> }>, exemptions: Array<{ label: string; value: string }> } | null>(null)
  
  // Logs
  const [logs, setLogs] = useState<LogEntry[]>([])
  
  const addLog = (level: LogEntry['level'], message: string) => {
    const entry: LogEntry = {
      timestamp: new Date().toLocaleTimeString('pl-PL'),
      level,
      message
    }
    setLogs(prev => [...prev, entry])
  }
  
  // Helper function to clean up parameters that are no longer displayed
  const cleanupHiddenParameters = (updatedParams: Record<string, any>, updatedOfferParams: Record<string, any>, offerCategoryParams: CategoryParameter[]) => {
    // Clean up product parameters
    const cleanedProductParams: Record<string, any> = {}
    Object.entries(updatedParams).forEach(([paramId, value]) => {
      const param = offerCategoryParams.find(p => p.id === paramId)
      if (param && isParameterDisplayed(param, updatedParams, updatedOfferParams)) {
        cleanedProductParams[paramId] = value
      } else if (!param) {
        // Keep if not in category parameters (might be from product)
        cleanedProductParams[paramId] = value
      }
      // Otherwise, skip (parameter is hidden)
    })
    
    // Clean up offer parameters
    const cleanedOfferParams: Record<string, any> = {}
    Object.entries(updatedOfferParams).forEach(([paramId, value]) => {
      const param = offerCategoryParams.find(p => p.id === paramId)
      if (param && isParameterDisplayed(param, updatedParams, updatedOfferParams)) {
        cleanedOfferParams[paramId] = value
      } else if (!param) {
        // Keep if not in category parameters
        cleanedOfferParams[paramId] = value
      }
      // Otherwise, skip (parameter is hidden)
    })
    
    return { cleanedProductParams, cleanedOfferParams }
  }
  
  const handleSearch = async () => {
    if (!current?.id) {
      addToast('Wybierz konto', 'error')
      return
    }
    
    if (!ean.trim()) {
      addToast('Wprowadź kod EAN', 'error')
      return
    }
    
    // Parse EAN codes from textarea (one per line)
    const allEanCodes = ean
      .split('\n')
      .map(e => e.trim())
      .filter(e => e.length > 0)
    
    if (allEanCodes.length === 0) {
      addToast('Wprowadź kod EAN', 'error')
      return
    }
    
    // Remove duplicates - keep only first occurrence of each EAN
    const uniqueEanCodes: string[] = []
    const seenEans = new Set<string>()
    const duplicates: string[] = []
    
    allEanCodes.forEach(eanCode => {
      if (!seenEans.has(eanCode)) {
        seenEans.add(eanCode)
        uniqueEanCodes.push(eanCode)
      } else {
        duplicates.push(eanCode)
      }
    })
    
    const duplicatesCount = duplicates.length
    
    if (duplicatesCount > 0) {
      addLog('info', `Wykryto ${duplicatesCount} duplikat(ów) EAN - wykluczono z przetwarzania`)
    }
    
    // Limit to MAX_EAN_CODES to prevent performance issues
    const MAX_EAN_CODES = 200
    const eanCodes = uniqueEanCodes.slice(0, MAX_EAN_CODES)
    const skippedCount = uniqueEanCodes.length - eanCodes.length
    
    if (skippedCount > 0) {
      addLog('warning', `Przetwarzam tylko pierwsze ${MAX_EAN_CODES} unikalnych kodów EAN. Pominięto ${skippedCount} kod(ów).`)
    }
    
    setIsSearching(true)
    setSearchProgress({ current: 0, total: eanCodes.length })
    setCurrentPage(1)  // Reset to first page
    addLog('info', `Wyszukiwanie produktów dla ${eanCodes.length} kodów EAN${duplicatesCount > 0 ? ` (wykluczono ${duplicatesCount} duplikatów)` : ''}${skippedCount > 0 ? ` (pominięto ${skippedCount} kodów)` : ''}`)
    
    const newOffers: OfferConfig[] = []
    const newExpandedParams: Record<string, boolean> = {}
    const newExpandedData: Record<string, boolean> = {}
    
    try {
      // Process EAN codes in batches of 50
      const BATCH_SIZE = 50
      const totalBatches = Math.ceil(eanCodes.length / BATCH_SIZE)
      
      for (let batchIndex = 0; batchIndex < totalBatches; batchIndex++) {
        const batchStart = batchIndex * BATCH_SIZE
        const batchEnd = Math.min(batchStart + BATCH_SIZE, eanCodes.length)
        const batch = eanCodes.slice(batchStart, batchEnd)
        
        // Process batch sequentially
        for (let i = 0; i < batch.length; i++) {
          const eanCode = batch[i]
          const globalIndex = batchStart + i + 1
          setSearchProgress({ current: globalIndex, total: eanCodes.length })
          
          try {
          const response = await api.post('/allegro/offer-creation/search-product', {
            account_id: current.id,
            ean: eanCode
          })
          
          if (response.data.success) {
            const foundProducts = response.data.products || []
            
            if (foundProducts.length === 0) {
              // Still create an offer entry but with empty products
              const offerIndex = newOffers.length
              const offerId = `offer-${offerIndex}`
              
              // Get CSV data for this EAN if available
              const csvDataForEan = csvData[eanCode] || {}
              
              const newOffer: OfferConfig = {
                ean: eanCode,
                products: [],
                selectedProductId: null,
                selectedProductDetails: null,
                categoryParameters: [],
                offerName: csvDataForEan.title || '',
                price: csvDataForEan.price || '',
                stock: csvDataForEan.stock || '1',
                selectedParameters: {},
                selectedOfferParameters: {},
                selectedShippingRate: csvDataForEan.selectedShippingRate || '',
                handlingTime: csvDataForEan.handlingTime || 'PT24H',
                sku: csvDataForEan.sku || '',
                duration: csvDataForEan.duration || 'PT720H',
                durationType: csvDataForEan.durationType || 'fixed',
                returnPolicyId: csvDataForEan.returnPolicyId || '',
                selectedResponsibleProducerId: csvDataForEan.selectedResponsibleProducerId || '',
                selectedResponsiblePersonId: csvDataForEan.selectedResponsiblePersonId || '',
                safetyInformation: csvDataForEan.safetyInformation || '',
                invoiceType: csvDataForEan.invoiceType || 'NO_INVOICE',
                selectedTaxRates: csvDataForEan.selectedTaxRates || {},
                selectedTaxSubject: csvDataForEan.selectedTaxSubject || '',
                selectedTaxExemption: csvDataForEan.selectedTaxExemption || ''
              }
              
              newOffers.push(newOffer)
              newExpandedParams[offerId] = false
              newExpandedData[offerId] = false
            } else {
              // Automatically select first product and create offer config
              const firstProduct = foundProducts[0]
              const offerIndex = newOffers.length
              const offerId = `offer-${offerIndex}`
              
              // Get CSV data for this EAN if available
              const csvDataForEan = csvData[eanCode] || {}
              
              const newOffer: OfferConfig = {
                ean: eanCode,
                products: foundProducts,
                selectedProductId: firstProduct.id,
                selectedProductDetails: null,  // Will be loaded
                categoryParameters: [],
                // Use CSV title if provided, otherwise use product name
                offerName: csvDataForEan.title || firstProduct.name,
                price: csvDataForEan.price || '',
                stock: csvDataForEan.stock || '1',
                selectedParameters: {},
                selectedOfferParameters: {},
                selectedShippingRate: csvDataForEan.selectedShippingRate || '',
                handlingTime: csvDataForEan.handlingTime || 'PT24H',
                sku: csvDataForEan.sku || '',
                duration: csvDataForEan.duration || 'PT720H',
                durationType: csvDataForEan.durationType || 'fixed',
                returnPolicyId: csvDataForEan.returnPolicyId || '',
                selectedResponsibleProducerId: csvDataForEan.selectedResponsibleProducerId || '',
                selectedResponsiblePersonId: csvDataForEan.selectedResponsiblePersonId || '',
                safetyInformation: csvDataForEan.safetyInformation || '',
                invoiceType: csvDataForEan.invoiceType || 'NO_INVOICE',
                selectedTaxRates: csvDataForEan.selectedTaxRates || {},
                selectedTaxSubject: csvDataForEan.selectedTaxSubject || '',
                selectedTaxExemption: csvDataForEan.selectedTaxExemption || ''
              }
              
              newOffers.push(newOffer)
              newExpandedParams[offerId] = false
              newExpandedData[offerId] = false
            }
          } else {
            // Still create an offer entry but with empty products
            const offerIndex = newOffers.length
            const offerId = `offer-${offerIndex}`
            
            const newOffer: OfferConfig = {
              ean: eanCode,
              products: [],
              selectedProductId: null,
              selectedProductDetails: null,
              offerName: '',
              price: '',
              stock: '1',
              selectedParameters: {},
              selectedOfferParameters: {},
              selectedShippingRate: '',
              handlingTime: 'PT24H',
              sku: '',
              duration: 'PT720H',
              durationType: 'fixed',
              returnPolicyId: '',
              selectedResponsibleProducerId: '',
              selectedResponsiblePersonId: '',
              safetyInformation: '',
              invoiceType: 'NO_INVOICE',
              selectedTaxRates: {},
              selectedTaxSubject: '',
              selectedTaxExemption: ''
            }
            
            newOffers.push(newOffer)
            newExpandedParams[offerId] = false
            newExpandedData[offerId] = false
          }
        } catch (error: any) {
          // Still create an offer entry but with empty products
          const offerIndex = newOffers.length
          const offerId = `offer-${offerIndex}`
          
          const newOffer: OfferConfig = {
            ean: eanCode,
            products: [],
            selectedProductId: null,
            selectedProductDetails: null,
            offerName: '',
            price: '',
            stock: '1',
            selectedParameters: {},
            selectedOfferParameters: {},
            selectedShippingRate: '',
            handlingTime: 'PT24H',
            sku: '',
            duration: 'PT720H',
            durationType: 'fixed',
            returnPolicyId: '',
            selectedResponsibleProducerId: '',
            selectedResponsiblePersonId: '',
            safetyInformation: '',
            invoiceType: 'NO_INVOICE',
            selectedTaxRates: {},
            selectedTaxSubject: '',
            selectedTaxExemption: ''
          }
          
          newOffers.push(newOffer)
          newExpandedParams[offerId] = false
          newExpandedData[offerId] = false
        }
        }  // Close inner for loop (batch items)
      }  // Close outer for loop (batches)
      
      // Set all offers at once first (without loading details)
      setOffers(newOffers)
      setExpandedParams(newExpandedParams)
      setExpandedData(newExpandedData)
      
      // Load product details only for current page (first page after search)
      await loadProductDetailsForPage(newOffers, 1, pageSize)
      
      if (newOffers.length > 0) {
        const foundCount = newOffers.filter(o => o.products.length > 0).length
        let summaryMessage = `Znaleziono produkty dla ${foundCount}/${newOffers.length} EAN(ów)`
        if (duplicatesCount > 0) {
          summaryMessage += ` (wykluczono ${duplicatesCount} duplikat${duplicatesCount === 1 ? '' : duplicatesCount < 5 ? 'y' : 'ów'})`
        }
        addLog('success', `Znaleziono produkty dla ${foundCount}/${newOffers.length} kodów EAN`)
        addToast(summaryMessage, foundCount === newOffers.length ? 'success' : 'info')
      } else {
        addLog('error', 'Nie znaleziono produktów dla żadnego z podanych kodów EAN')
        addToast('Nie znaleziono produktów dla żadnego z podanych kodów EAN', 'error')
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Błąd podczas wyszukiwania'
      addLog('error', `Błąd: ${errorMessage}`)
      addToast(errorMessage, 'error')
      setOffers([])
    } finally {
      setIsSearching(false)
    }
  }
  
  // Load product details only for offers on current page
  const loadProductDetailsForPage = async (offersList: OfferConfig[], page: number, size: number) => {
    const startIndex = (page - 1) * size
    const endIndex = startIndex + size
    const pageOffers = offersList.slice(startIndex, endIndex)
    
    const offersToLoad = pageOffers.filter((o, idx) => {
      const globalIndex = startIndex + idx
      const offer = offersList[globalIndex]
      return offer && offer.products.length > 0 && offer.selectedProductId && !offer.selectedProductDetails
    })
    const totalToLoad = offersToLoad.length
    
    if (totalToLoad === 0) {
      return
    }
    
    setLoadingProgress({ current: 0, total: totalToLoad })
    
    let loadedCount = 0
    for (let i = 0; i < pageOffers.length; i++) {
      const offer = pageOffers[i]
      const globalIndex = startIndex + i
      
      if (offer.products.length > 0 && offer.selectedProductId && !offer.selectedProductDetails) {
        const offerId = `offer-${globalIndex}`
        const product = offer.products.find(p => p.id === offer.selectedProductId) || offer.products[0]
        
        if (product) {
          try {
            setLoadingOffers(prev => new Set(prev).add(offerId))
            await handleSelectProduct(product, offerId)
            loadedCount++
            setLoadingProgress({ current: loadedCount, total: totalToLoad })
            } catch (error: any) {
              // Silently handle errors - details will be loaded when user views the page
            } finally {
            setLoadingOffers(prev => {
              const next = new Set(prev)
              next.delete(offerId)
              return next
            })
          }
          
          // Small delay between each
          if (i < pageOffers.length - 1) {
            await new Promise(resolve => setTimeout(resolve, 150))
          }
        }
      }
    }
    
    setLoadingProgress(null)
  }
  
  // Load details when page changes
  useEffect(() => {
    if (offers.length > 0 && !isSearching) {
      loadProductDetailsForPage(offers, currentPage, pageSize)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage])  // Only depend on page changes, not offers (to avoid infinite loop)
  
  // Handle opening product selector modal
  const handleOpenProductSelector = (ean: string) => {
    setCurrentEanForModal(ean)
    setShowProductSelectorModal(true)
  }
  
  // Handle selecting product from modal
  const handleSelectProductFromModal = async (product: Product) => {
    const offer = offers.find(o => o.ean === currentEanForModal)
    if (!offer) return
    
    const offerId = `offer-${offers.indexOf(offer)}`
    await handleSelectProduct(product, offerId)
    setShowProductSelectorModal(false)
  }
  
  // Download template (CSV or XLSX)
  const handleDownloadTemplate = async (format: 'csv' | 'xlsx' = 'xlsx') => {
    try {
      const response = await api.get(`/allegro/offer-creation/template?format=${format}`, {
        responseType: 'blob'
      })
      
      const blob = new Blob([response.data])
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = format === 'csv' ? 'szablon_ofert.csv' : 'szablon_ofert.xlsx'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      addToast(`Szablon ${format.toUpperCase()} pobrany`, 'success')
      addLog('info', `Pobrano szablon ${format.toUpperCase()}`)
    } catch (error: any) {
      addToast(`Błąd podczas pobierania szablonu: ${error.message}`, 'error')
      addLog('error', `Błąd podczas pobierania szablonu: ${error.message}`)
    }
  }
  
  // Handle file import (CSV or XLSX)
  const handleFileImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    
    try {
      const parsed = await parseFile(file)
      const data = parsed.data
      const headers = parsed.headers || (data.length > 0 ? data[0] : [])
      
      if (!headers || headers.length === 0) {
        addToast('Plik musi zawierać nagłówki', 'error')
        return
      }
      
      // Find EAN column index
      const eanIndex = headers.findIndex((h: string) => h.toLowerCase() === 'ean')
      
      if (eanIndex === -1) {
        addToast('Plik musi zawierać kolumnę "EAN"', 'error')
        return
      }
      
      // Parse data rows
      const newCsvData: typeof csvData = {}
      const eans: string[] = []
      
      const startRow = parsed.headers ? 0 : 1  // Skip header row if not already parsed
      
      for (let i = startRow; i < data.length; i++) {
        const row = data[i]
        if (!row || row.length === 0) continue
        
        const ean = String(row[eanIndex] || '').trim()
        if (!ean) continue
        
        eans.push(ean)
        
        // Extract data from row
        const getValue = (headerName: string | string[]) => {
          const names = Array.isArray(headerName) ? headerName : [headerName]
          for (const name of names) {
            const idx = headers.findIndex((h: string) => h.toLowerCase() === name.toLowerCase())
            if (idx !== -1 && row[idx]) {
              return String(row[idx]).trim()
            }
          }
          return ''
        }
        
        newCsvData[ean] = {}
        
        const title = getValue(['tytuł', 'tytul'])
        if (title) newCsvData[ean].title = title
        
        const price = getValue('cena')
        if (price) newCsvData[ean].price = price
        
        const sku = getValue('sku')
        if (sku) newCsvData[ean].sku = sku
        
        const stock = getValue(['ilość', 'ilosc'])
        if (stock) newCsvData[ean].stock = stock
        
        const shippingRate = getValue('cennik dostawy')
        if (shippingRate) newCsvData[ean].selectedShippingRate = shippingRate
        
        const handlingTime = getValue('czas dostawy')
        if (handlingTime) newCsvData[ean].handlingTime = handlingTime
        
        const durationType = getValue('typ trwania')
        if (durationType) newCsvData[ean].durationType = durationType as 'fixed' | 'unlimited'
        
        const duration = getValue('okres trwania')
        if (duration) newCsvData[ean].duration = duration
        
        const returnPolicy = getValue(['warunki zwrotów', 'warunki zwrotow'])
        if (returnPolicy) newCsvData[ean].returnPolicyId = returnPolicy
        
        const responsibleProducer = getValue('producent odpowiedzialny')
        if (responsibleProducer) newCsvData[ean].selectedResponsibleProducerId = responsibleProducer
        
        const responsiblePerson = getValue('osoba odpowiedzialna')
        if (responsiblePerson) newCsvData[ean].selectedResponsiblePersonId = responsiblePerson
        
        const safetyInfo = getValue(['informacje o bezpieczeństwie', 'informacje o bezpieczenstwie'])
        if (safetyInfo) newCsvData[ean].safetyInformation = safetyInfo
        
        const invoiceType = getValue('typ faktury')
        if (invoiceType) newCsvData[ean].invoiceType = invoiceType
        
        const taxSubject = getValue('przedmiot opodatkowania')
        if (taxSubject) newCsvData[ean].selectedTaxSubject = taxSubject
        
        const taxRatePl = getValue('stawka vat pl')
        if (taxRatePl) newCsvData[ean].selectedTaxRates = { 'PL': taxRatePl }
        
        const taxExemption = getValue('zwolnienie z vat')
        if (taxExemption) newCsvData[ean].selectedTaxExemption = taxExemption
      }
      
      setCsvData(newCsvData)
      setEan(eans.join('\n'))
      
      const fileType = file.name.endsWith('.xlsx') ? 'XLSX' : 'CSV'
      addToast(`Zaimportowano ${eans.length} ofert z ${fileType}`, 'success')
      addLog('success', `Zaimportowano ${eans.length} ofert z ${fileType}`)
    } catch (error: any) {
      addToast(`Błąd podczas importu pliku: ${error.message}`, 'error')
      addLog('error', `Błąd podczas importu pliku: ${error.message}`)
    } finally {
      // Reset input
      event.target.value = ''
    }
  }
  
  // Handle applying bulk settings to selected offers
  const handleApplyBulkSettings = (offerIndices: number[]) => {
    if (offerIndices.length === 0) {
      addToast('Wybierz przynajmniej jedną ofertę', 'error')
      return
    }
    
    // Check if any settings are configured
    const hasSettings = Object.keys(bulkSettings).some(key => {
      const value = bulkSettings[key as keyof typeof bulkSettings]
      if (key === 'selectedTaxRates') {
        return value && Object.keys(value as Record<string, string>).length > 0
      }
      return value !== undefined && value !== null && value !== ''
    })
    
    if (!hasSettings) {
      addToast('Skonfiguruj przynajmniej jedno ustawienie', 'error')
      return
    }
    
    setOffers(prevOffers => {
      const updatedOffers = [...prevOffers]
      offerIndices.forEach(index => {
        if (updatedOffers[index]) {
          const updatedOffer = { ...updatedOffers[index] }
          
          // Apply each setting if it's configured
          if (bulkSettings.selectedShippingRate !== undefined && bulkSettings.selectedShippingRate !== '') {
            updatedOffer.selectedShippingRate = bulkSettings.selectedShippingRate
          }
          if (bulkSettings.handlingTime !== undefined && bulkSettings.handlingTime !== '') {
            updatedOffer.handlingTime = bulkSettings.handlingTime
          }
          if (bulkSettings.sku !== undefined && bulkSettings.sku !== '') {
            updatedOffer.sku = bulkSettings.sku
          }
          if (bulkSettings.durationType !== undefined && bulkSettings.durationType !== '') {
            updatedOffer.durationType = bulkSettings.durationType as 'fixed' | 'unlimited'
          }
          if (bulkSettings.duration !== undefined && bulkSettings.duration !== '') {
            updatedOffer.duration = bulkSettings.duration
          }
          if (bulkSettings.returnPolicyId !== undefined && bulkSettings.returnPolicyId !== '') {
            updatedOffer.returnPolicyId = bulkSettings.returnPolicyId
          }
          if (bulkSettings.selectedResponsibleProducerId !== undefined && bulkSettings.selectedResponsibleProducerId !== '') {
            updatedOffer.selectedResponsibleProducerId = bulkSettings.selectedResponsibleProducerId
          }
          if (bulkSettings.selectedResponsiblePersonId !== undefined && bulkSettings.selectedResponsiblePersonId !== '') {
            updatedOffer.selectedResponsiblePersonId = bulkSettings.selectedResponsiblePersonId
          }
          if (bulkSettings.safetyInformation !== undefined && bulkSettings.safetyInformation !== '') {
            updatedOffer.safetyInformation = bulkSettings.safetyInformation
          }
          if (bulkSettings.invoiceType !== undefined && bulkSettings.invoiceType !== '') {
            updatedOffer.invoiceType = bulkSettings.invoiceType
          }
          if (bulkSettings.selectedTaxSubject !== undefined && bulkSettings.selectedTaxSubject !== '') {
            updatedOffer.selectedTaxSubject = bulkSettings.selectedTaxSubject
          }
          if (bulkSettings.selectedTaxRates !== undefined && Object.keys(bulkSettings.selectedTaxRates || {}).length > 0) {
            updatedOffer.selectedTaxRates = {
              ...updatedOffer.selectedTaxRates,
              ...bulkSettings.selectedTaxRates
            }
          }
          if (bulkSettings.selectedTaxExemption !== undefined && bulkSettings.selectedTaxExemption !== '') {
            updatedOffer.selectedTaxExemption = bulkSettings.selectedTaxExemption
          }
          
          updatedOffers[index] = updatedOffer
        }
      })
      return updatedOffers
    })
    
    addToast(`Zastosowano ustawienia do ${offerIndices.length} ofert`, 'success')
    addLog('success', `Zastosowano masowe ustawienia do ${offerIndices.length} ofert`)
  }
  
  // Function to check if a parameter should be displayed based on displayedIf conditions
  const isParameterDisplayed = (param: CategoryParameter, selectedParams: Record<string, any>, selectedOfferParams: Record<string, any>): boolean => {
    // If parameter has displayedIf, check conditions
    if (param.displayedIf) {
      const displayedIf = param.displayedIf
      
      // Check parametersWithValue conditions
      if (displayedIf.parametersWithValue && displayedIf.parametersWithValue.length > 0) {
        const allConditionsMet = displayedIf.parametersWithValue.every(condition => {
          // Check if parameter has one of the required values
          const paramValue = selectedParams[condition.id] || selectedOfferParams[condition.id]
          if (!paramValue) return false
          
          if (condition.oneOfValueIds && condition.oneOfValueIds.length > 0) {
            // Check if paramValue matches one of the required value IDs
            return condition.oneOfValueIds.includes(paramValue)
          }
          return false
        })
        
        if (!allConditionsMet) {
          return false // Not displayed if conditions not met
        }
      }
      
      // Check parametersWithoutValue conditions
      if (displayedIf.parametersWithoutValue && displayedIf.parametersWithoutValue.length > 0) {
        const allConditionsMet = displayedIf.parametersWithoutValue.every(paramId => {
          // Parameter should NOT have a value
          return !selectedParams[paramId] && !selectedOfferParams[paramId]
        })
        
        if (!allConditionsMet) {
          return false // Not displayed if conditions not met
        }
      }
    }
    
    // If no displayedIf or conditions are met, parameter should be displayed
    return true
  }
  
  // Function to sort and group parameters
  const getSortedAndGroupedParameters = (offer: OfferConfig) => {
    // Use category parameters from this specific offer
    const offerCategoryParams = offer.categoryParameters || []
    // Filter visible parameters
    const visibleParams = offerCategoryParams.filter(p => 
      isParameterDisplayed(p, offer.selectedParameters, offer.selectedOfferParameters)
    )
    
    // Separate product and offer parameters
    const productParams = visibleParams.filter(p => 
      p.options?.describesProduct || p.options?.identifiesProduct
    )
    const offerParams = visibleParams.filter(p => 
      !p.options?.describesProduct && !p.options?.identifiesProduct
    )
    
    // Sort function: required first, then by name
    const sortParams = (params: CategoryParameter[]) => {
      return [...params].sort((a, b) => {
        const aRequired = isParameterRequired(a, offer.selectedParameters, offer.selectedOfferParameters)
        const bRequired = isParameterRequired(b, offer.selectedParameters, offer.selectedOfferParameters)
        
        // Required parameters first
        if (aRequired && !bRequired) return -1
        if (!aRequired && bRequired) return 1
        
        // Then sort by name
        return a.name.localeCompare(b.name)
      })
    }
    
    // Group dependent parameters together - improved algorithm
    const groupDependentParams = (params: CategoryParameter[]) => {
      const processed = new Set<string>()
      const result: CategoryParameter[] = []
      
      // Build dependency graph
      const dependsOn = new Map<string, Set<string>>() // paramId -> set of paramIds it depends on
      const dependedBy = new Map<string, Set<string>>() // paramId -> set of paramIds that depend on it
      
      params.forEach(param => {
        dependsOn.set(param.id, new Set())
        dependedBy.set(param.id, new Set())
      })
      
      // Build dependency relationships
      params.forEach(param => {
        // Check requiredIf dependencies
        if (param.requiredIf?.parametersWithValue) {
          param.requiredIf.parametersWithValue.forEach(cond => {
            if (params.some(p => p.id === cond.id)) {
              dependsOn.get(param.id)?.add(cond.id)
              dependedBy.get(cond.id)?.add(param.id)
            }
          })
        }
        
        // Check displayedIf dependencies
        if (param.displayedIf?.parametersWithValue) {
          param.displayedIf.parametersWithValue.forEach(cond => {
            if (params.some(p => p.id === cond.id)) {
              dependsOn.get(param.id)?.add(cond.id)
              dependedBy.get(cond.id)?.add(param.id)
            }
          })
        }
      })
      
      // Function to get all related parameters (transitive closure)
      const getRelatedGroup = (paramId: string, visited: Set<string>): string[] => {
        if (visited.has(paramId)) return []
        visited.add(paramId)
        
        const group = [paramId]
        
        // Add all parameters this one depends on
        dependsOn.get(paramId)?.forEach(depId => {
          if (!visited.has(depId)) {
            group.push(...getRelatedGroup(depId, visited))
          }
        })
        
        // Add all parameters that depend on this one
        dependedBy.get(paramId)?.forEach(depId => {
          if (!visited.has(depId)) {
            group.push(...getRelatedGroup(depId, visited))
          }
        })
        
        return group
      }
      
      // Group parameters by dependencies
      params.forEach(param => {
        if (processed.has(param.id)) return
        
        const relatedGroup = getRelatedGroup(param.id, new Set())
        const relatedParams = relatedGroup
          .map(id => params.find(p => p.id === id))
          .filter((p): p is CategoryParameter => p !== undefined)
          .sort((a, b) => {
            // Within group, required first, then by name
            const aRequired = isParameterRequired(a, offer.selectedParameters, offer.selectedOfferParameters)
            const bRequired = isParameterRequired(b, offer.selectedParameters, offer.selectedOfferParameters)
            if (aRequired && !bRequired) return -1
            if (!aRequired && bRequired) return 1
            return a.name.localeCompare(b.name)
          })
        
        relatedParams.forEach(p => {
          if (!processed.has(p.id)) {
            result.push(p)
            processed.add(p.id)
          }
        })
      })
      
      // Add any remaining unprocessed parameters
      params.forEach(param => {
        if (!processed.has(param.id)) {
          result.push(param)
        }
      })
      
      return result
    }
    
    return {
      product: groupDependentParams(sortParams(productParams)),
      offer: groupDependentParams(sortParams(offerParams))
    }
  }
  
  // Function to get parameter color class based on required status
  const getParameterColorClass = (param: CategoryParameter, value: any, offer: OfferConfig) => {
    const isRequired = isParameterRequired(param, offer.selectedParameters, offer.selectedOfferParameters)
    if (!isRequired) return 'border-gray-200 bg-white'
    
    const isFilled = value !== '' && value !== null && value !== undefined
    if (isFilled) {
      return 'border-green-300 bg-green-50'
    } else {
      return 'border-red-300 bg-red-50'
    }
  }
  
  // Helper function to get border color class for DANE fields
  const getDaneFieldBorderClass = (isRequired: boolean, isFilled: boolean): string => {
    if (!isRequired) return 'border-gray-300'
    if (isFilled) return 'border-green-300'
    return 'border-red-300'
  }
  
  // Helper function to get background color class for DANE fields
  const getDaneFieldBgClass = (isRequired: boolean, isFilled: boolean): string => {
    if (!isRequired) return 'bg-white'
    if (isFilled) return 'bg-green-50'
    return 'bg-red-50'
  }
  
  // Function to check if a parameter is truly required based on requiredIf conditions
  const isParameterRequired = (param: CategoryParameter, selectedParams: Record<string, any>, selectedOfferParams: Record<string, any>): boolean => {
    // If parameter has requiredIf, check conditions
    if (param.requiredIf) {
      const requiredIf = param.requiredIf
      
      // Check parametersWithValue conditions
      if (requiredIf.parametersWithValue && requiredIf.parametersWithValue.length > 0) {
        const allConditionsMet = requiredIf.parametersWithValue.every(condition => {
          // Check if parameter has one of the required values
          const paramValue = selectedParams[condition.id] || selectedOfferParams[condition.id]
          if (!paramValue) return false
          
          if (condition.oneOfValueIds && condition.oneOfValueIds.length > 0) {
            // Check if paramValue matches one of the required value IDs
            return condition.oneOfValueIds.includes(paramValue)
          }
          return false
        })
        
        if (!allConditionsMet) {
          return false // Not required if conditions not met
        }
      }
      
      // Check parametersWithoutValue conditions
      if (requiredIf.parametersWithoutValue && requiredIf.parametersWithoutValue.length > 0) {
        const allConditionsMet = requiredIf.parametersWithoutValue.every(paramId => {
          // Parameter should NOT have a value
          return !selectedParams[paramId] && !selectedOfferParams[paramId]
        })
        
        if (!allConditionsMet) {
          return false // Not required if conditions not met
        }
      }
    }
    
    // If no requiredIf or conditions are met, use the basic required flag
    return param.required
  }
  
  const handleSelectProduct = async (product: Product, offerId?: string) => {
    if (!current?.id) return
    
    try {
      const response = await api.post('/allegro/offer-creation/product-details', {
        account_id: current.id,
        product_id: product.id,
        category_id: product.category?.id
      })
      
      if (response.data.success) {
        const productDetails: ProductDetails = response.data.product
        
        // Update offer with selected product details
        // Use functional update to ensure we have the latest state
        setOffers(prevOffers => {
          if (prevOffers.length === 0) {
            return prevOffers
          }
          
          const offerIndex = offerId ? parseInt(offerId.replace('offer-', '')) : 0
          if (offerIndex >= prevOffers.length) {
            return prevOffers
          }
          
          const updatedOffers = [...prevOffers]
          if (updatedOffers[offerIndex]) {
            // Preserve offerName from CSV if it was set, otherwise use product name
            const currentOffer = updatedOffers[offerIndex]
            const csvDataForEan = csvData[currentOffer.ean]
            // If CSV has title, use it; otherwise use product name
            const finalOfferName = csvDataForEan?.title || productDetails.name
            
            updatedOffers[offerIndex] = {
              ...updatedOffers[offerIndex],
              selectedProductId: product.id,
              selectedProductDetails: productDetails,
              offerName: finalOfferName
            }
          }
          return updatedOffers
        })
        
        // Store category parameters for this specific offer (not global)
        if (response.data.categoryParameters?.parameters) {
          const categoryParams = response.data.categoryParameters.parameters
          
          // Update offer with category parameters
          setOffers(prevOffers => {
            if (prevOffers.length === 0) return prevOffers
            const offerIndex = offerId ? parseInt(offerId.replace('offer-', '')) : 0
            if (offerIndex >= prevOffers.length) return prevOffers
            const updatedOffers = [...prevOffers]
            if (updatedOffers[offerIndex]) {
              updatedOffers[offerIndex] = {
                ...updatedOffers[offerIndex],
                categoryParameters: categoryParams
              }
            }
            return updatedOffers
          })
          
        }
        
            if (response.data.shippingRates?.shippingRates) {
              setShippingRates(response.data.shippingRates.shippingRates)
            }
            
            if (response.data.afterSalesServices?.returns) {
              setReturnPolicies(response.data.afterSalesServices.returns)
            }
            
            // Get responsible producers
            if (response.data.responsibleProducers?.responsibleProducers) {
              setResponsibleProducers(response.data.responsibleProducers.responsibleProducers.map((rp: any) => ({
                id: rp.id,
                name: rp.name
              })))
            }
            
            // Get responsible persons
            if (response.data.responsiblePersons?.responsiblePersons) {
              setResponsiblePersons(response.data.responsiblePersons.responsiblePersons.map((rp: any) => ({
                id: rp.id,
                name: rp.name
              })))
            }
            
            // Get tax settings for category
            if (response.data.taxSettings) {
              setTaxSettings(response.data.taxSettings)
            }
        
        // Get list of truly required parameters from offerRequirements (if available)
        const requiredParamIds = new Set<string>()
        if (productDetails.offerRequirements?.parameters) {
          productDetails.offerRequirements.parameters.forEach((req: any) => {
            if (req.required) {
              requiredParamIds.add(req.id)
            }
          })
        }
        
        // Initialize product parameters from product details
        // IMPORTANT: Only set values that come from the product itself, don't set defaults
        const productParams: Record<string, any> = {}
        if (productDetails.parameters) {
          productDetails.parameters.forEach(param => {
            // Parse valuesIds if it's a string (JSON)
            let valuesIds: string[] = []
            if (param.valuesIds) {
              if (typeof param.valuesIds === 'string') {
                try {
                  valuesIds = JSON.parse(param.valuesIds)
                } catch {
                  valuesIds = []
                }
              } else {
                valuesIds = param.valuesIds
              }
            }
            
            // Parse values if it's a string (JSON)
            let values: any[] = []
            if (param.values) {
              if (typeof param.values === 'string') {
                try {
                  values = JSON.parse(param.values)
                } catch {
                  values = []
                }
              } else {
                values = Array.isArray(param.values) ? param.values : [param.values]
              }
            }
            
            // Only set value if product actually has it - don't set defaults
            if (valuesIds.length > 0 || values.length > 0) {
              // Check if this parameter is dictionary type or has valuesLabels/valuesIds in category parameters
              const categoryParam = response.data.categoryParameters?.parameters?.find((p: any) => p.id === param.id)
              if (categoryParam) {
                // Check dictionary directly on param first, then fallback to options.dictionary
                const categoryParamDictionary = categoryParam.dictionary || categoryParam.options?.dictionary
                // PRIORITY 1: Check if parameter has dictionary options (highest priority)
                if (categoryParam.type === 'dictionary' && categoryParamDictionary && Array.isArray(categoryParamDictionary) && categoryParamDictionary.length > 0) {
                  // For dictionary, check if product's valuesIds[0] matches any dictionary item id
                  if (valuesIds.length > 0) {
                    const matchingDictItem = categoryParamDictionary.find((item: any) => item.id === valuesIds[0])
                    if (matchingDictItem) {
                      productParams[param.id] = matchingDictItem.id
                    }
                  }
                } else if (categoryParam.valuesLabels && categoryParam.valuesIds && Array.isArray(categoryParam.valuesLabels) && Array.isArray(categoryParam.valuesIds) && categoryParam.valuesIds.length > 0) {
                  // PRIORITY 2: Check if parameter has valuesLabels/valuesIds format
                  if (valuesIds.length > 0) {
                    // Check if product's valuesIds[0] is in category's valuesIds
                    const matchingId = categoryParam.valuesIds.find((id: string) => id === valuesIds[0])
                    if (matchingId) {
                      productParams[param.id] = matchingId
                    }
                  }
                } else {
                  // PRIORITY 3: For other types, use valuesIds or values
                  if (valuesIds.length > 0) {
                    productParams[param.id] = String(valuesIds[0])
                  } else if (values.length > 0) {
                    // Convert to string (important for EAN and other numeric values)
                    productParams[param.id] = String(values[0])
                  }
                }
              } else {
                // No category param found, use valuesIds or values
                if (valuesIds.length > 0) {
                  productParams[param.id] = String(valuesIds[0])
                } else if (values.length > 0) {
                  // Convert to string (important for EAN and other numeric values)
                  productParams[param.id] = String(values[0])
                }
              }
            }
          })
        }
        
        // Initialize offer parameters (these go in main payload.parameters)
        // Only parameters that are NOT product parameters (describesProduct/identifiesProduct = false)
        // IMPORTANT: Only set defaults for parameters that are truly required (check requiredIf conditions)
        const initialOfferParams: Record<string, any> = {}
        if (response.data.categoryParameters?.parameters) {
          response.data.categoryParameters.parameters.forEach((param: any) => {
            // Only offer parameters (not product parameters)
            const isOfferParam = !param.options?.describesProduct && !param.options?.identifiesProduct
            
            if (isOfferParam) {
              // Check if parameter is truly required (considering requiredIf)
              const isRequired = isParameterRequired(param, productParams, {})
              
              if (isRequired) {
                // Check dictionary directly on param first, then fallback to options.dictionary
                const paramDictionary = param.dictionary || param.options?.dictionary
                // Check if parameter is dictionary type
                if (param.type === 'dictionary' && paramDictionary && Array.isArray(paramDictionary) && paramDictionary.length > 0) {
                  // For dictionary, use the id of first item
                  initialOfferParams[param.id] = paramDictionary[0].id
                } else if (param.valuesIds && Array.isArray(param.valuesIds) && param.valuesIds.length > 0) {
                  // For valuesLabels/valuesIds format, use first ID
                  initialOfferParams[param.id] = param.valuesIds[0]
                } else if (param.values && Array.isArray(param.values) && param.values.length > 0) {
                  // If values is array of objects with 'value' property
                  if (typeof param.values[0] === 'object' && param.values[0].value) {
                    initialOfferParams[param.id] = param.values[0].value
                  } else if (typeof param.values[0] === 'string') {
                    initialOfferParams[param.id] = param.values[0]
                  }
                }
              }
            }
          })
        }
        
        // Update offer with parameters - use functional update to ensure we have latest state
        setOffers(prevOffers => {
          if (prevOffers.length === 0) return prevOffers
          const offerIndex = offerId ? parseInt(offerId.replace('offer-', '')) : 0
          const updatedOffers = [...prevOffers]
          if (updatedOffers[offerIndex]) {
            updatedOffers[offerIndex] = {
              ...updatedOffers[offerIndex],
              selectedParameters: productParams,
              selectedOfferParameters: initialOfferParams
            }
          }
          return updatedOffers
        })
        
        // Don't show toast here - we show progress notification instead
      } else {
        addLog('error', 'Błąd podczas pobierania szczegółów produktu')
        addToast('Błąd podczas pobierania szczegółów produktu', 'error')
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Błąd podczas pobierania szczegółów'
      addLog('error', `Błąd: ${errorMessage}`)
      addToast(errorMessage, 'error')
    }
  }
  
  // Function to check what's missing and return list of missing fields
  const getMissingFields = (offer: OfferConfig): string[] => {
    const missing: string[] = []
    
    if (!offer.offerName.trim()) {
      missing.push('Nazwa oferty')
    }
    
    if (!offer.price.trim()) {
      missing.push('Cena')
    }
    
    if (!offer.stock.trim()) {
      missing.push('Stan magazynowy')
    }
    
    if (shippingRates.length > 0 && !offer.selectedShippingRate) {
      missing.push('Cennik dostawy')
    }
    
    if (!offer.handlingTime) {
      missing.push('Czas dostawy')
    }
    
    // Check return policy (required for active offers)
    if (returnPolicies.length > 0 && !offer.returnPolicyId) {
      missing.push('Warunki zwrotów')
    }
    
    // Check responsible producer/person (required for active offers)
    if (!offer.selectedResponsibleProducerId && !offer.selectedResponsiblePersonId) {
      missing.push('Producent odpowiedzialny LUB osoba odpowiedzialna')
    }
    
    // Check duration (required when fixed duration is selected)
    if (offer.durationType === 'fixed' && !offer.duration) {
      missing.push('Okres trwania oferty')
    }
    
    // Check invoice and tax settings (required when invoice is VAT)
    if (offer.invoiceType === 'VAT' || offer.invoiceType === 'VAT_MARGIN') {
      if (!offer.selectedTaxSubject) {
        missing.push('Przedmiot opodatkowania')
      }
      if (taxSettings?.rates) {
        // Only Poland (PL) is required, other countries are optional
        const plRate = taxSettings.rates.find((cr: any) => cr.countryCode === 'PL')
        if (plRate && !offer.selectedTaxRates['PL']) {
          missing.push('Stawka VAT dla Polski (PL)')
        }
        // Other countries are optional, so we don't require them
      }
    }
    
    // Check safety information (required for active offers)
    if (!offer.safetyInformation.trim()) {
      missing.push('Informacje o bezpieczeństwie')
    }
    
    // Check required offer parameters (considering requiredIf)
    const offerCategoryParams = offer.categoryParameters || []
    const missingOfferParams = offerCategoryParams
      .filter(p => {
        const isOfferParam = !p.options || (!p.options.describesProduct && !p.options.identifiesProduct)
        if (!isOfferParam) return false
        const isRequired = isParameterRequired(p, offer.selectedParameters, offer.selectedOfferParameters)
        if (!isRequired) return false
        
        const paramValue = offer.selectedOfferParameters[p.id]
        // Check if value is empty (null, undefined, empty string, or empty array)
        const isEmpty = paramValue === null || paramValue === undefined || paramValue === '' || 
                       (Array.isArray(paramValue) && paramValue.length === 0)
        return isEmpty
      })
      .map(p => p.name)
    
    if (missingOfferParams.length > 0) {
      missing.push(...missingOfferParams.map(name => `Parametr oferty: ${name}`))
    }
    
    // Check required product parameters (considering requiredIf)
    const missingProductParams = offerCategoryParams
      .filter(p => {
        const isProductParam = p.options?.describesProduct || p.options?.identifiesProduct
        if (!isProductParam) return false
        const isRequired = isParameterRequired(p, offer.selectedParameters, offer.selectedOfferParameters)
        if (!isRequired) return false
        
        const paramValue = offer.selectedParameters[p.id]
        // Check if value is empty (null, undefined, empty string, or empty array)
        const isEmpty = paramValue === null || paramValue === undefined || paramValue === '' || 
                       (Array.isArray(paramValue) && paramValue.length === 0)
        return isEmpty
      })
      .map(p => p.name)
    
    if (missingProductParams.length > 0) {
      missing.push(...missingProductParams.map(name => `Parametr produktu: ${name}`))
    }
    
    return missing
  }
  
  // Helper function to prepare offer payload
  const prepareOfferPayload = (offer: OfferConfig) => {
    // Prepare parameters array (product parameters)
    const parameters: Array<{ id: string; valuesIds?: string[]; values?: string[] }> = []
    
    const offerCategoryParams = offer.categoryParameters || []
    Object.entries(offer.selectedParameters).forEach(([paramId, value]) => {
      if (value) {
        const categoryParam = offerCategoryParams.find(p => p.id === paramId)
        const productParam = offer.selectedProductDetails?.parameters?.find(p => p.id === paramId)
        const param = categoryParam || productParam
        
        // Only include parameter if it's currently displayed (check displayedIf conditions)
        if (param && categoryParam && !isParameterDisplayed(categoryParam, offer.selectedParameters, offer.selectedOfferParameters)) {
          return // Skip this parameter if it's not displayed
        }
        
        if (param) {
          // Check dictionary directly on param first, then fallback to options.dictionary
          const categoryParamDictionary = categoryParam ? (categoryParam.dictionary || categoryParam.options?.dictionary) : null
          // Check if parameter is dictionary type or has valuesIds
          if (categoryParam && categoryParam.type === 'dictionary' && categoryParamDictionary) {
            // For dictionary type, value is already the id from dictionary
            parameters.push({
              id: paramId,
              valuesIds: Array.isArray(value) ? value : [value]
            })
          } else if (categoryParam && categoryParam.valuesIds && Array.isArray(categoryParam.valuesIds) && categoryParam.valuesIds.length > 0) {
            // For valuesLabels/valuesIds format, value is already the id
            parameters.push({
              id: paramId,
              valuesIds: Array.isArray(value) ? value : [value]
            })
          } else if (productParam?.valuesIds) {
            parameters.push({
              id: paramId,
              valuesIds: Array.isArray(value) ? value : [value]
            })
          } else {
            parameters.push({
              id: paramId,
              values: Array.isArray(value) ? value : [value]
            })
          }
        }
      }
    })
    
    // Prepare offer parameters (not product parameters) - these go in main payload.parameters
    const offerParams: Array<{ id: string; valuesIds?: string[]; values?: string[] }> = []
    
    Object.entries(offer.selectedOfferParameters).forEach(([paramId, value]) => {
      if (value !== '' && value !== null && value !== undefined) {
        const param = offerCategoryParams.find(p => p.id === paramId)
        
        // Only include parameter if it's currently displayed (check displayedIf conditions)
        if (param && !isParameterDisplayed(param, offer.selectedParameters, offer.selectedOfferParameters)) {
          return // Skip this parameter if it's not displayed
        }
        
        if (param) {
          // Check dictionary directly on param first, then fallback to options.dictionary
          const paramDictionary = param.dictionary || param.options?.dictionary
          // Check if parameter is dictionary type
          if (param.type === 'dictionary' && paramDictionary && Array.isArray(paramDictionary)) {
            // For dictionary type, value is already the id from dictionary
            offerParams.push({
              id: paramId,
              valuesIds: [String(value)]
            })
          } else if (param.valuesIds && Array.isArray(param.valuesIds) && param.valuesIds.length > 0) {
            // For valuesLabels/valuesIds format, value is already the id
            offerParams.push({
              id: paramId,
              valuesIds: [String(value)]
            })
          } else if (param.values && Array.isArray(param.values) && param.values.length > 0) {
            // Find matching value - values can be objects or strings
            let matchedValue: string | undefined
            for (const val of param.values) {
              const valValue = typeof val === 'object' ? val.value : val
              const valName = typeof val === 'object' ? val.name : val
              if (valValue === String(value) || valName === String(value)) {
                matchedValue = valValue
                break
              }
            }
            
            if (matchedValue) {
              offerParams.push({
                id: paramId,
                valuesIds: [matchedValue]
              })
            } else {
              // Use provided value as-is
              offerParams.push({
                id: paramId,
                valuesIds: [String(value)]
              })
            }
          } else {
            // No predefined values, use as string
            offerParams.push({
              id: paramId,
              values: [String(value)]
            })
          }
        }
      }
    })
    
    // Prepare delivery settings
    const deliverySettings: any = {}
    if (offer.selectedShippingRate) {
      deliverySettings.shippingRates = { id: offer.selectedShippingRate }
    }
    
    // Prepare after-sales services (return policy is required for active offers)
    const afterSalesServices: any = {}
    if (!offer.returnPolicyId) {
      throw new Error('Warunki zwrotów są wymagane dla aktywnych ofert')
    }
    afterSalesServices.returnPolicy = { id: offer.returnPolicyId }
    
    // Prepare responsible producer/person (GPSR requirement for active offers)
    // Use IDs from account list, not free text input
    const responsibleProducerId = offer.selectedResponsibleProducerId || undefined
    const responsiblePersonId = offer.selectedResponsiblePersonId || undefined
    
    // Get responsible person name if person is selected
    let responsiblePersonName: string | undefined = undefined
    if (responsiblePersonId) {
      const selectedPerson = responsiblePersons.find(p => p.id === responsiblePersonId)
      responsiblePersonName = selectedPerson?.name
    }
    
    // Prepare safety information
    const safetyInfo = offer.safetyInformation.trim() ? {
      type: "TEXT",
      description: offer.safetyInformation.trim()
    } : null
    
    // Prepare tax settings (only when invoice is VAT or VAT_MARGIN)
    let taxSettingsPayload: any = undefined
    if ((offer.invoiceType === 'VAT' || offer.invoiceType === 'VAT_MARGIN') && taxSettings) {
      const rates: Array<{ rate: string; countryCode: string }> = []
      
      // Add rate for each country that has a selected rate
      Object.entries(offer.selectedTaxRates).forEach(([countryCode, rate]) => {
        if (rate) {
          rates.push({
            rate: rate,
            countryCode: countryCode
          })
        }
      })
      
      if (rates.length > 0 && offer.selectedTaxSubject) {
        taxSettingsPayload = {
          rates: rates,
          subject: offer.selectedTaxSubject
        }
        
        // Add exemption if selected
        if (offer.selectedTaxExemption) {
          taxSettingsPayload.exemption = offer.selectedTaxExemption
        }
      }
    }
    
    return {
      account_id: current?.id!,
      product_id: offer.selectedProductDetails!.id,
      name: offer.offerName.trim(),
      category_id: offer.selectedProductDetails!.category.id,
      price: offer.price.trim(),
      stock: parseInt(offer.stock),
      quantity: 1,
      duration: offer.durationType === 'fixed' ? offer.duration : undefined,
      images: offer.selectedProductDetails!.images?.map(img => img.url) || [],
      product_parameters: parameters.length > 0 ? parameters : undefined,
      parameters: offerParams.length > 0 ? offerParams : undefined,
      delivery: Object.keys(deliverySettings).length > 0 ? deliverySettings : undefined,
      handling_time: offer.handlingTime,
      invoice_type: offer.invoiceType,
      tax_settings: taxSettingsPayload,
      external_id: offer.sku.trim() || undefined,
      afterSalesServices: Object.keys(afterSalesServices).length > 0 ? afterSalesServices : undefined,
      responsible_producer_id: responsibleProducerId,
      responsible_person_id: responsiblePersonId,
      responsible_person_name: responsiblePersonName,
      safety_information: safetyInfo,
      publication_status: publicationStatus
    }
  }
  
  const handleCreateOffer = async (offerIndex: number = 0) => {
    if (!current?.id || !currentOffer || !currentOffer.selectedProductDetails) {
      addToast('Wybierz produkt', 'error')
      return
    }
    
    const offer = currentOffer
    
    if (!offer.offerName.trim()) {
      addToast('Wprowadź nazwę oferty', 'error')
      return
    }
    
    if (offer.offerName.length > 75) {
      addToast(`Tytuł przekracza 75 znaków (${offer.offerName.length} znaków). Skróć tytuł przed wystawieniem oferty.`, 'error')
      return
    }
    
    if (!offer.price.trim() || parseFloat(offer.price) <= 0) {
      addToast('Wprowadź poprawną cenę', 'error')
      return
    }
    
    if (!offer.stock.trim() || parseInt(offer.stock) <= 0) {
      addToast('Wprowadź poprawną ilość', 'error')
      return
    }
    
    setIsCreating(true)
    addLog('info', 'Tworzenie oferty...')
    
    try {
      const payload = prepareOfferPayload(offer)
      const response = await api.post('/allegro/offer-creation/create', payload)
      
      if (response.data.success) {
        addLog('success', `Oferta została utworzona pomyślnie! ID: ${response.data.offer_id}`)
        addToast(`Oferta została utworzona pomyślnie! ID: ${response.data.offer_id}`, 'success')
        
        // Reset form
        setEan('')
        setOffers([])
        setExpandedParams({})
        setExpandedData({})
      } else {
        addLog('error', 'Błąd podczas tworzenia oferty')
        addToast('Błąd podczas tworzenia oferty', 'error')
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Błąd podczas tworzenia oferty'
      addLog('error', `Błąd: ${errorMessage}`)
      addToast(errorMessage, 'error')
    } finally {
      setIsCreating(false)
    }
  }
  
  // Handle creating multiple offers
  const handleCreateMultipleOffers = async (offerIndices: number[]) => {
    if (!current?.id) {
      addToast('Wybierz konto', 'error')
      return
    }
    
    if (offerIndices.length === 0) {
      addToast('Wybierz przynajmniej jedną ofertę', 'error')
      return
    }
    
    // Validate all offers before starting
    const invalidOffers: string[] = []
    offerIndices.forEach(index => {
      const offer = offers[index]
      if (!offer) {
        invalidOffers.push(`Oferta ${index + 1}`)
        return
      }
      if (!offer.selectedProductDetails) {
        invalidOffers.push(`Oferta ${index + 1}: brak produktu`)
        return
      }
      if (!offer.offerName.trim()) {
        invalidOffers.push(`Oferta ${index + 1}: brak tytułu`)
        return
      }
      if (offer.offerName.length > 75) {
        invalidOffers.push(`Oferta ${index + 1}: tytuł przekracza 75 znaków (${offer.offerName.length} znaków)`)
        return
      }
      if (!offer.price.trim() || parseFloat(offer.price) <= 0) {
        invalidOffers.push(`Oferta ${index + 1}: nieprawidłowa cena`)
        return
      }
      if (!offer.stock.trim() || parseInt(offer.stock) <= 0) {
        invalidOffers.push(`Oferta ${index + 1}: nieprawidłowa ilość`)
        return
      }
    })
    
    if (invalidOffers.length > 0) {
      addToast(`Nieprawidłowe oferty: ${invalidOffers.join(', ')}`, 'error')
      return
    }
    
    setIsCreating(true)
    addLog('info', `Rozpoczynam tworzenie ${offerIndices.length} ofert...`)
    
    const toastId = addToast(`Tworzenie ofert: 0/${offerIndices.length}`, 'info', 999999)
    const createdOffers: string[] = []
    const failedOffers: Array<{ index: number; error: string }> = []
    
    try {
      for (let i = 0; i < offerIndices.length; i++) {
        const offerIndex = offerIndices[i]
        const offer = offers[offerIndex]
        
        if (!offer || !offer.selectedProductDetails) continue
        
        try {
          updateToast(toastId, `Tworzenie ofert: ${i + 1}/${offerIndices.length}`, 'info')
          
          const payload = prepareOfferPayload(offer)
          const response = await api.post('/allegro/offer-creation/create', payload)
          
          if (response.data.success) {
            createdOffers.push(response.data.offer_id)
          } else {
            failedOffers.push({ index: offerIndex, error: 'Błąd podczas tworzenia oferty' })
          }
          
          // Small delay between requests to avoid overwhelming the API
          if (i < offerIndices.length - 1) {
            await new Promise(resolve => setTimeout(resolve, 500))
          }
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || error.message || 'Błąd podczas tworzenia oferty'
          failedOffers.push({ index: offerIndex, error: errorMessage })
        }
      }
      
      // Remove progress toast
      removeToast(toastId)
      
      // Show summary
      if (createdOffers.length > 0) {
        addToast(`Utworzono ${createdOffers.length}/${offerIndices.length} ofert pomyślnie`, 'success')
        addLog('success', `Wystawiono ${createdOffers.length} ofert:`)
        // Log EAN and offer ID for each created offer
        offerIndices.forEach((offerIndex, idx) => {
          const offer = offers[offerIndex]
          if (offer && createdOffers[idx]) {
            addLog('success', `  • EAN: ${offer.ean} → Aukcja: ${createdOffers[idx]}`)
          }
        })
      }
      
      if (failedOffers.length > 0) {
        addToast(`Nie udało się utworzyć ${failedOffers.length} ofert`, 'error')
        addLog('error', `Nie udało się utworzyć ${failedOffers.length} ofert`)
        failedOffers.forEach(({ index, error }) => {
          const offer = offers[index]
          const eanInfo = offer ? ` (EAN: ${offer.ean})` : ''
          addLog('error', `  • Oferta ${index + 1}${eanInfo}: ${error}`)
        })
      }
      
      // Reset form if all offers were created successfully
      if (failedOffers.length === 0 && createdOffers.length === offerIndices.length) {
        setEan('')
        setOffers([])
        setExpandedParams({})
        setExpandedData({})
        setSelectedOffers(new Set())
        setCsvData({})
      }
    } catch (error: any) {
      removeToast(toastId)
      const errorMessage = error.response?.data?.detail || error.message || 'Błąd podczas tworzenia ofert'
      addLog('error', `Błąd: ${errorMessage}`)
      addToast(errorMessage, 'error')
    } finally {
      setIsCreating(false)
    }
  }
  
  const handleParameterChange = (paramId: string, value: any, offerIndex: number = 0) => {
    if (offers.length === 0) return
    const updatedOffers = [...offers]
    const offer = updatedOffers[offerIndex]
    if (!offer) return
    
    const updated = { ...offer.selectedParameters, [paramId]: value }
    // Clean up parameters that are no longer displayed after this change
    const { cleanedProductParams, cleanedOfferParams } = cleanupHiddenParameters(updated, offer.selectedOfferParameters, offer.categoryParameters || [])
    
    updatedOffers[offerIndex] = {
      ...offer,
      selectedParameters: cleanedProductParams,
      selectedOfferParameters: cleanedOfferParams
    }
    setOffers(updatedOffers)
  }
  
  const handleOfferParameterChange = (paramId: string, value: any, offerIndex: number = 0) => {
    if (offers.length === 0) return
    const updatedOffers = [...offers]
    const offer = updatedOffers[offerIndex]
    if (!offer) return
    
    const updated = { ...offer.selectedOfferParameters, [paramId]: value }
    // Clean up parameters that are no longer displayed after this change
    const { cleanedProductParams, cleanedOfferParams } = cleanupHiddenParameters(offer.selectedParameters, updated, offer.categoryParameters || [])
    
    updatedOffers[offerIndex] = {
      ...offer,
      selectedParameters: cleanedProductParams,
      selectedOfferParameters: cleanedOfferParams
    }
    setOffers(updatedOffers)
  }
  
  // Helper functions to update offer fields
  const updateOfferField = <K extends keyof OfferConfig>(field: K, value: OfferConfig[K], offerIndex: number = 0) => {
    setOffers(prevOffers => {
      if (prevOffers.length === 0 || !prevOffers[offerIndex]) return prevOffers
      const updatedOffers = [...prevOffers]
      updatedOffers[offerIndex] = {
        ...updatedOffers[offerIndex],
        [field]: value
      }
      return updatedOffers
    })
  }
  
  // Helper function to format category path (shorten if too long)
  // Skip "Allegro" and show second and last category
  const formatCategoryPath = (categoryPath: Array<{ id: string; name: string }> | undefined): string => {
    if (!categoryPath || categoryPath.length === 0) return ''
    
    // Filter out "Allegro" from the path
    const filteredPath = categoryPath.filter(c => c.name !== 'Allegro')
    
    if (filteredPath.length === 0) return ''
    
    // If path is short enough, return as is (without Allegro)
    const fullPath = filteredPath.map(c => c.name).join(' / ')
    if (fullPath.length <= 50) return fullPath
    
    // If path is too long, show second + ... + last
    if (filteredPath.length >= 2) {
      const second = filteredPath[0].name  // First after filtering Allegro
      const last = filteredPath[filteredPath.length - 1].name
      return `${second} / ... / ${last}`
    }
    
    // If only one element, truncate it
    return fullPath.length > 50 ? fullPath.substring(0, 47) + '...' : fullPath
  }
  
  if (!current) {
    return (
      <div className="space-y-6 w-full flex flex-col">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-semibold">Wystawianie Ofert</h1>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Konto:</span>
            <AccountSelector />
          </div>
        </div>
        <div className="bg-white shadow rounded-lg p-8 text-center">
          <div className="text-gray-500 space-y-2">
            <div className="text-lg">Wybierz konto</div>
            <div className="text-sm">Aby wystawić ofertę, wybierz konto powyżej</div>
          </div>
        </div>
      </div>
    )
  }
  
  return (
    <div className="space-y-6 w-full flex flex-col">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-semibold">Wystawianie Ofert</h1>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">Konto:</span>
          <AccountSelector />
        </div>
      </div>
      
      {/* Search Section */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Wyszukaj produkt po kodzie EAN</h2>
          <span className="text-sm text-gray-500">
            {ean.trim() ? ean.trim().split('\n').filter(e => e.trim()).length : 0} EAN(ów)
          </span>
        </div>
        <div className="space-y-3">
          {/* Publication Status Selection */}
          <div className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
            <span className="text-sm font-medium text-gray-700">Status publikacji:</span>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="publicationStatus"
                checked={publicationStatus === 'ACTIVE'}
                onChange={() => setPublicationStatus('ACTIVE')}
                className="w-4 h-4 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">Wystaw jako oferta</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="publicationStatus"
                checked={publicationStatus === 'INACTIVE'}
                onChange={() => setPublicationStatus('INACTIVE')}
                className="w-4 h-4 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">Zapisz jako szkic</span>
            </label>
          </div>
          
          <div className="flex space-x-2">
            <textarea
              placeholder="Wprowadź kody EAN, jeden na linię&#10;7622201386160&#10;1234567890123"
              value={ean}
              onChange={(e) => setEan(e.target.value)}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
              rows={4}
              disabled={isSearching}
            />
            <div className="flex flex-col space-y-2">
              <button
                onClick={handleSearch}
                disabled={isSearching || !ean.trim()}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed whitespace-nowrap"
              >
                {isSearching ? 'Szukam...' : 'Szukaj'}
              </button>
              <button
                onClick={() => setEan('')}
                disabled={isSearching || !ean.trim()}
                className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed whitespace-nowrap"
              >
                Wyczyść
              </button>
            </div>
          </div>
          
          {/* Search Progress Bar */}
          {isSearching && searchProgress && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm text-gray-600">
                <span>Wyszukiwanie produktów...</span>
                <span className="font-medium">{searchProgress.current}/{searchProgress.total}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                  style={{ width: `${(searchProgress.current / searchProgress.total) * 100}%` }}
                ></div>
              </div>
            </div>
          )}
          
          {/* Loading Details Progress Bar */}
          {loadingProgress && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm text-gray-600">
                <span>Ładowanie szczegółów produktów...</span>
                <span className="font-medium">{loadingProgress.current}/{loadingProgress.total}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-green-600 h-2.5 rounded-full transition-all duration-300"
                  style={{ width: `${(loadingProgress.current / loadingProgress.total) * 100}%` }}
                ></div>
              </div>
            </div>
          )}
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleDownloadTemplate('xlsx')}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm whitespace-nowrap"
            >
              📥 Pobierz szablon Excel
            </button>
            <button
              onClick={() => handleDownloadTemplate('csv')}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm whitespace-nowrap"
            >
              📥 Pobierz szablon CSV
            </button>
            <label className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm cursor-pointer whitespace-nowrap">
              📤 Importuj z pliku
              <input
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleFileImport}
                className="hidden"
              />
            </label>
            {Object.keys(csvData).length > 0 && (
              <span className="text-xs text-gray-600">
                ✓ Załadowano dane dla {Object.keys(csvData).length} EAN(ów)
              </span>
            )}
          </div>
          <div className="text-xs text-gray-500">
            💡 Wprowadź kody EAN, jeden na linię. Dla każdego EAN zostanie utworzona osobna oferta. Możesz też zaimportować oferty z pliku CSV.
            {(() => {
              // Check for duplicates in current EAN input
              const eanLines = ean.split('\n').map(e => e.trim()).filter(e => e.length > 0)
              const seen = new Set<string>()
              const duplicates = new Set<string>()
              eanLines.forEach(eanCode => {
                if (seen.has(eanCode)) {
                  duplicates.add(eanCode)
                } else {
                  seen.add(eanCode)
                }
              })
              if (duplicates.size > 0) {
                return (
                  <div className="mt-2 text-orange-600 font-medium">
                    ⚠️ Wykryto {duplicates.size} duplikat(ów) EAN - zostaną wykluczone podczas wyszukiwania
                  </div>
                )
              }
              return null
            })()}
          </div>
        </div>
      </div>
      
      {/* Offers Table View */}
      {offers.length > 0 && (
        <div className="bg-white shadow rounded-lg">
          {/* Table Header */}
          <div className="bg-gray-800 text-white px-4 py-3 grid grid-cols-12 gap-2 font-semibold text-sm">
            <div className="col-span-1">
              <input
                type="checkbox"
                checked={selectedOffers.size === offers.length && offers.length > 0}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedOffers(new Set(offers.map((_, i) => i)))
                  } else {
                    setSelectedOffers(new Set())
                  }
                }}
                className="w-4 h-4 cursor-pointer"
              />
            </div>
            <div className="col-span-5">NAZWA AUKCJI</div>
            <div className="col-span-2">KATEGORIA</div>
            <div className="col-span-1">ILOŚĆ</div>
            <div className="col-span-1">KUP TERAZ</div>
            <div className="col-span-2">OPCJE</div>
          </div>
          
          {/* Bulk Settings Section */}
          {selectedOffers.size > 0 && (
            <div className="bg-blue-50 border-b border-blue-200 px-6 py-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-800">
                  Masowe ustawienia ({selectedOffers.size} wybranych)
                </h3>
                <div className="flex gap-2">
                  {selectedOffers.size > 0 && (
                    <>
                      <button
                        onClick={() => handleApplyBulkSettings(Array.from(selectedOffers))}
                        className="px-4 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                      >
                        Zastosuj do wybranych ({selectedOffers.size})
                      </button>
                      <button
                        onClick={() => handleApplyBulkSettings(offers.map((_, i) => i))}
                        className="px-4 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
                      >
                        Zastosuj do wszystkich ({offers.length})
                      </button>
                      <button
                        onClick={() => handleCreateMultipleOffers(Array.from(selectedOffers))}
                        disabled={isCreating}
                        className="px-4 py-1 text-xs bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                      >
                        {isCreating ? 'Tworzenie...' : `Wystaw zaznaczone (${selectedOffers.size})`}
                      </button>
                      <button
                        onClick={() => handleCreateMultipleOffers(offers.map((_, i) => i))}
                        disabled={isCreating}
                        className="px-4 py-1 text-xs bg-orange-600 text-white rounded hover:bg-orange-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                      >
                        {isCreating ? 'Tworzenie...' : `Wystaw wszystkie (${offers.length})`}
                      </button>
                    </>
                  )}
                </div>
              </div>
              
              {/* Bulk Settings Sections */}
              <div className="space-y-3">
                {/* Parametry podstawowe */}
                <div className="border border-gray-300 rounded-lg bg-white">
                  <button
                    onClick={() => {
                      const newExpanded = new Set(expandedBulkSections)
                      if (newExpanded.has('basic')) {
                        newExpanded.delete('basic')
                      } else {
                        newExpanded.add('basic')
                      }
                      setExpandedBulkSections(newExpanded)
                    }}
                    className="w-full px-4 py-2 flex items-center justify-between text-left hover:bg-gray-50 rounded-t-lg"
                  >
                    <span className="text-sm font-medium text-gray-800">Parametry podstawowe</span>
                    <svg
                      className={`w-4 h-4 transition-transform ${expandedBulkSections.has('basic') ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  
                  {expandedBulkSections.has('basic') && (
                <div className="grid grid-cols-6 gap-3 mt-3">
                  {/* Delivery Settings */}
                  {shippingRates.length > 0 && (
                    <div className="border rounded p-2 bg-white">
                      <label className="block text-xs font-medium mb-1 text-gray-700">
                        Cennik dostawy
                      </label>
                      <select
                        value={bulkSettings.selectedShippingRate || ''}
                        onChange={(e) => setBulkSettings({ ...bulkSettings, selectedShippingRate: e.target.value })}
                        className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="">-- Nie zmieniaj --</option>
                        {shippingRates.map((rate) => (
                          <option key={rate.id} value={rate.id}>
                            {rate.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                  
                  {/* Handling Time */}
                  <div className="border rounded p-2 bg-white">
                    <label className="block text-xs font-medium mb-1 text-gray-700">
                      Czas dostawy
                    </label>
                    <select
                      value={bulkSettings.handlingTime || ''}
                      onChange={(e) => setBulkSettings({ ...bulkSettings, handlingTime: e.target.value })}
                      className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">-- Nie zmieniaj --</option>
                      <option value="PT0S">Natychmiast</option>
                      <option value="PT24H">24 godziny</option>
                      <option value="PT48H">48 godzin</option>
                      <option value="PT72H">72 godziny</option>
                      <option value="PT96H">96 godzin</option>
                      <option value="PT120H">120 godzin</option>
                    </select>
                  </div>
                  
                  {/* SKU */}
                  <div className="border rounded p-2 bg-white">
                    <label className="block text-xs font-medium mb-1 text-gray-700">
                      SKU
                    </label>
                    <input
                      type="text"
                      value={bulkSettings.sku || ''}
                      onChange={(e) => setBulkSettings({ ...bulkSettings, sku: e.target.value })}
                      className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="-- Nie zmieniaj --"
                    />
                  </div>
                  
                  {/* Duration Type */}
                  <div className="border rounded p-2 bg-white">
                    <label className="block text-xs font-medium mb-1 text-gray-700">
                      Typ trwania
                    </label>
                    <select
                      value={bulkSettings.durationType || ''}
                      onChange={(e) => {
                        const newType = e.target.value as 'fixed' | 'unlimited' | ''
                        setBulkSettings({ 
                          ...bulkSettings, 
                          durationType: newType || undefined,
                          duration: newType === 'unlimited' ? '' : (bulkSettings.duration || 'PT720H')
                        })
                      }}
                      className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">-- Nie zmieniaj --</option>
                      <option value="fixed">Na określony okres</option>
                      <option value="unlimited">Do wyczerpania zapasów</option>
                    </select>
                  </div>
                  
                  {/* Duration (only if fixed) */}
                  {bulkSettings.durationType === 'fixed' && (
                    <div className="border rounded p-2 bg-white">
                      <label className="block text-xs font-medium mb-1 text-gray-700">
                        Okres trwania
                      </label>
                      <select
                        value={bulkSettings.duration || ''}
                        onChange={(e) => setBulkSettings({ ...bulkSettings, duration: e.target.value })}
                        className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="">-- Nie zmieniaj --</option>
                        <option value="PT720H">30 dni</option>
                        <option value="PT1440H">60 dni</option>
                        <option value="PT2160H">90 dni</option>
                        <option value="PT2880H">120 dni</option>
                      </select>
                    </div>
                  )}
                  
                  {/* Return Policy */}
                  {returnPolicies.length > 0 && (
                    <div className="border rounded p-2 bg-white">
                      <label className="block text-xs font-medium mb-1 text-gray-700">
                        Warunki zwrotów
                      </label>
                      <select
                        value={bulkSettings.returnPolicyId || ''}
                        onChange={(e) => setBulkSettings({ ...bulkSettings, returnPolicyId: e.target.value })}
                        className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="">-- Nie zmieniaj --</option>
                        {returnPolicies.map((policy) => (
                          <option key={policy.id} value={policy.id}>
                            {policy.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                  
                  {/* Responsible Producer */}
                  {responsibleProducers.length > 0 && (
                    <div className="border rounded p-2 bg-white">
                      <label className="block text-xs font-medium mb-1 text-gray-700">
                        Producent odpowiedzialny
                      </label>
                      <select
                        value={bulkSettings.selectedResponsibleProducerId || ''}
                        onChange={(e) => setBulkSettings({ ...bulkSettings, selectedResponsibleProducerId: e.target.value })}
                        className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="">-- Nie zmieniaj --</option>
                        {responsibleProducers.map((producer) => (
                          <option key={producer.id} value={producer.id}>
                            {producer.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                  
                  {/* Responsible Person */}
                  {responsiblePersons.length > 0 && (
                    <div className="border rounded p-2 bg-white">
                      <label className="block text-xs font-medium mb-1 text-gray-700">
                        Osoba odpowiedzialna
                      </label>
                      <select
                        value={bulkSettings.selectedResponsiblePersonId || ''}
                        onChange={(e) => setBulkSettings({ ...bulkSettings, selectedResponsiblePersonId: e.target.value })}
                        className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="">-- Nie zmieniaj --</option>
                        {responsiblePersons.map((person) => (
                          <option key={person.id} value={person.id}>
                            {person.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                  
                  {/* Safety Information */}
                  <div className="border rounded p-2 bg-white col-span-2">
                    <label className="block text-xs font-medium mb-1 text-gray-700">
                      Informacje o bezpieczeństwie
                    </label>
                    <textarea
                      value={bulkSettings.safetyInformation || ''}
                      onChange={(e) => setBulkSettings({ ...bulkSettings, safetyInformation: e.target.value })}
                      className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                      rows={2}
                      placeholder="-- Nie zmieniaj --"
                    />
                  </div>
                  
                  {/* Invoice Type */}
                  <div className="border rounded p-2 bg-white">
                    <label className="block text-xs font-medium mb-1 text-gray-700">
                      Typ faktury
                    </label>
                    <select
                      value={bulkSettings.invoiceType || ''}
                      onChange={(e) => setBulkSettings({ ...bulkSettings, invoiceType: e.target.value })}
                      className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">-- Nie zmieniaj --</option>
                      <option value="NO_INVOICE">Bez faktury</option>
                      <option value="VAT">Faktura VAT</option>
                      <option value="VAT_MARGIN">Faktura VAT marża</option>
                      <option value="WITHOUT_VAT">Faktura bez VAT</option>
                    </select>
                  </div>
                  
                  {/* Tax Subject (only if invoice type is VAT) */}
                  {bulkSettings.invoiceType === 'VAT' || bulkSettings.invoiceType === 'VAT_MARGIN' ? (
                    <>
                      {taxSettings?.subjects && (
                        <div className="border rounded p-2 bg-white">
                          <label className="block text-xs font-medium mb-1 text-gray-700">
                            Przedmiot opodatkowania
                          </label>
                          <select
                            value={bulkSettings.selectedTaxSubject || ''}
                            onChange={(e) => setBulkSettings({ ...bulkSettings, selectedTaxSubject: e.target.value })}
                            className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                          >
                            <option value="">-- Nie zmieniaj --</option>
                            {taxSettings.subjects.map((subject) => (
                              <option key={subject.value} value={subject.value}>
                                {subject.label}
                              </option>
                            ))}
                          </select>
                        </div>
                      )}
                      
                      {/* Tax Rates for PL */}
                      {taxSettings?.rates && (
                        <div className="border rounded p-2 bg-white">
                          <label className="block text-xs font-medium mb-1 text-gray-700">
                            Stawka VAT PL
                          </label>
                          <select
                            value={bulkSettings.selectedTaxRates?.['PL'] || ''}
                            onChange={(e) => setBulkSettings({ 
                              ...bulkSettings, 
                              selectedTaxRates: { ...bulkSettings.selectedTaxRates, 'PL': e.target.value }
                            })}
                            className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                          >
                            <option value="">-- Nie zmieniaj --</option>
                            {taxSettings.rates.find((r: any) => r.countryCode === 'PL')?.values.map((rate: any) => (
                              <option key={rate.value} value={rate.value}>
                                {rate.label}
                              </option>
                            ))}
                          </select>
                        </div>
                      )}
                      
                      {/* Tax Exemption */}
                      {taxSettings?.exemptions && (
                        <div className="border rounded p-2 bg-white">
                          <label className="block text-xs font-medium mb-1 text-gray-700">
                            Zwolnienie z VAT
                          </label>
                          <select
                            value={bulkSettings.selectedTaxExemption || ''}
                            onChange={(e) => setBulkSettings({ ...bulkSettings, selectedTaxExemption: e.target.value })}
                            className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                          >
                            <option value="">-- Nie zmieniaj --</option>
                            {taxSettings.exemptions.map((exemption) => (
                              <option key={exemption.value} value={exemption.value}>
                                {exemption.label}
                              </option>
                            ))}
                          </select>
                        </div>
                      )}
                    </>
                  ) : null}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
          
          {/* Pagination Controls */}
          {offers.length > pageSize && (
            <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-200">
              <div className="text-sm text-gray-600">
                Strona {currentPage} z {Math.ceil(offers.length / pageSize)} ({offers.length} ofert)
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed"
                >
                  Poprzednia
                </button>
                <span className="text-sm text-gray-600">
                  {((currentPage - 1) * pageSize) + 1}-{Math.min(currentPage * pageSize, offers.length)} z {offers.length}
                </span>
                <button
                  onClick={() => setCurrentPage(prev => Math.min(Math.ceil(offers.length / pageSize), prev + 1))}
                  disabled={currentPage >= Math.ceil(offers.length / pageSize)}
                  className="px-3 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed"
                >
                  Następna
                </button>
              </div>
            </div>
          )}
          
          {/* Offer Row */}
          {(() => {
            // Get offers for current page
            const startIndex = (currentPage - 1) * pageSize
            const endIndex = startIndex + pageSize
            const paginatedOffers = offers.slice(startIndex, endIndex)
            
            return paginatedOffers.map((offer, pageIndex) => {
              const offerIndex = startIndex + pageIndex  // Global index for offer
              const offerId = `offer-${offerIndex}`
              const selectedProduct = offer.products.find(p => p.id === offer.selectedProductId) || offer.products[0]
              const isParamsExpanded = expandedParams[offerId] || false
              const isDataExpanded = expandedData[offerId] || false
              const isLoading = loadingOffers.has(offerId)
            
            return (
              <div key={offerId} className="border-b border-gray-200 relative">
                {/* Loading overlay for this specific offer */}
                {isLoading && (
                  <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
                    <div className="text-sm text-gray-600 flex items-center gap-2">
                      <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      {loadingProgress && (
                        <span>Ładowanie szczegółów... ({loadingProgress.current}/{loadingProgress.total})</span>
                      )}
                      {!loadingProgress && <span>Ładowanie szczegółów...</span>}
                    </div>
                  </div>
                )}
                {/* Main Row */}
                <div className={`px-4 py-4 grid grid-cols-12 gap-2 items-center ${isLoading ? 'opacity-50' : 'bg-gray-50'}`}>
                  {/* Checkbox */}
                  <div className="col-span-1 flex items-center justify-center">
                    <input
                      type="checkbox"
                      checked={selectedOffers.has(offerIndex)}
                      onChange={(e) => {
                        const newSelected = new Set(selectedOffers)
                        if (e.target.checked) {
                          newSelected.add(offerIndex)
                        } else {
                          newSelected.delete(offerIndex)
                        }
                        setSelectedOffers(newSelected)
                      }}
                      className="w-4 h-4 cursor-pointer"
                    />
                  </div>
                  {/* NAZWA AUKCJI */}
                  <div className="col-span-5">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 relative">
                        <input
                          type="text"
                          maxLength={75}
                          value={offer.offerName}
                          onChange={(e) => updateOfferField('offerName', e.target.value, offerIndex)}
                          className={`w-full px-2 py-2 pr-16 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm min-w-0 ${
                            offer.offerName.length > 75 ? 'border-red-500' : 'border-gray-300'
                          }`}
                          placeholder="Nazwa aukcji (max 75 znaków)"
                        />
                        <div className={`absolute right-2 top-1/2 -translate-y-1/2 text-xs font-medium ${
                          offer.offerName.length > 75 ? 'text-red-600' : 'text-gray-500'
                        }`}>
                          {offer.offerName.length}/75
                        </div>
                      </div>
                      {/* WYBRANO Button - in the same line */}
                      {selectedProduct && (
                        <button
                          onClick={() => handleOpenProductSelector(offer.ean)}
                          className="px-2 py-2 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 flex items-center gap-1 whitespace-nowrap flex-shrink-0"
                          title={selectedProduct.name}
                        >
                          <span>✓</span>
                          <span className="truncate max-w-[120px]">{selectedProduct.name}</span>
                          {offer.products.length > 0 && (
                            <span className="ml-1 px-1.5 py-0.5 bg-blue-600 rounded text-[10px] font-semibold flex-shrink-0">
                              {(() => {
                                const selectedIndex = offer.products.findIndex(p => p.id === offer.selectedProductId)
                                const position = selectedIndex !== -1 ? selectedIndex + 1 : 1
                                return offer.products.length === 1 ? '1' : `${position}/${offer.products.length}`
                              })()}
                            </span>
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                  
                  {/* KATEGORIA */}
                  <div className="col-span-2">
                    <div className="px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm text-gray-700 truncate" title={offer.selectedProductDetails?.category?.path?.map(c => c.name).join(' / ') || ''}>
                      {offer.selectedProductDetails?.category?.path ? formatCategoryPath(offer.selectedProductDetails.category.path) : '-'}
                    </div>
                  </div>
                  
                  {/* ILOŚĆ */}
                  <div className="col-span-1">
                    <input
                      type="number"
                      min="1"
                      value={offer.stock}
                      onChange={(e) => updateOfferField('stock', e.target.value, offerIndex)}
                      className="w-full px-2 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm"
                      placeholder="1"
                    />
                  </div>
                  
                  {/* KUP TERAZ */}
                  <div className="col-span-1">
                    <div className="flex">
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        value={offer.price}
                        onChange={(e) => updateOfferField('price', e.target.value, offerIndex)}
                        className="flex-1 px-1.5 py-2 border border-gray-300 rounded-l-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-xs w-16"
                        placeholder="0.00"
                      />
                      <span className="px-1.5 py-2 bg-gray-100 border border-l-0 border-gray-300 rounded-r-lg flex items-center text-xs whitespace-nowrap">PLN</span>
                    </div>
                  </div>
                  
                  {/* OPCJE */}
                  <div className="col-span-2 flex items-center gap-2">
                    <button
                      onClick={() => setExpandedParams({ ...expandedParams, [offerId]: !isParamsExpanded })}
                      className={`px-3 py-2 text-xs rounded font-medium ${
                        isParamsExpanded 
                          ? 'bg-blue-500 text-white' 
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      PARAM.
                    </button>
                    <button
                      onClick={() => setExpandedData({ ...expandedData, [offerId]: !isDataExpanded })}
                      className={`px-3 py-2 text-xs rounded font-medium ${
                        isDataExpanded 
                          ? 'bg-blue-500 text-white' 
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      DANE
                    </button>
                    <button
                      onClick={() => handleCreateOffer(offerIndex)}
                      disabled={isCreating}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-semibold text-xs whitespace-nowrap"
                    >
                      {isCreating ? 'Tworzenie...' : 'Wystaw ofertę'}
                    </button>
                  </div>
                </div>
                
                {/* Expanded PARAM. Section */}
                {isParamsExpanded && (
                  <div className="px-6 py-4 bg-white border-t border-gray-200">
                    <div className="mb-4">
                      <h3 className="text-sm font-semibold text-gray-700 mb-2">Parametry kategorii</h3>
                      {!offer.selectedProductDetails ? (
                        <p className="text-gray-500 text-sm">Wybierz produkt, aby zobaczyć parametry</p>
                      ) : (offer.categoryParameters || []).length === 0 ? (
                        <p className="text-gray-500 text-sm">Ładowanie parametrów kategorii...</p>
                      ) : (() => {
                        const { product, offer: offerParams } = getSortedAndGroupedParameters(offer)
                        const allParams = [...product, ...offerParams]
                        
                        if (allParams.length === 0) {
                          return <p className="text-gray-500 text-sm">Brak parametrów do wyświetlenia</p>
                        }
                        
                        return (
                          <div className="grid grid-cols-6 gap-3">
                            {allParams.map((param) => {
                              const isProductParam = param.options?.describesProduct || param.options?.identifiesProduct
                              const currentValue = isProductParam 
                                ? (offer.selectedParameters[param.id] || '')
                                : (offer.selectedOfferParameters[param.id] || '')
                              
                              const productParam = offer.selectedProductDetails?.parameters?.find(p => p.id === param.id)
                              
                              // Check dictionary
                              const paramDictionary = param.dictionary || param.options?.dictionary
                              const hasDictionary = param.type === 'dictionary' && paramDictionary && Array.isArray(paramDictionary) && paramDictionary.length > 0
                              const hasValuesLabels = !hasDictionary && param.valuesLabels && param.valuesIds && Array.isArray(param.valuesLabels) && Array.isArray(param.valuesIds) && param.valuesLabels.length > 0
                              const hasValues = !hasDictionary && !hasValuesLabels && param.values && Array.isArray(param.values) && param.values.length > 0
                              const shouldShowDropdown = hasDictionary || hasValuesLabels || hasValues
                              
                              // Determine value for product params
                              let displayValue = currentValue
                              if (!displayValue && productParam && isProductParam) {
                                let valuesIds: string[] = []
                                if (productParam.valuesIds) {
                                  if (typeof productParam.valuesIds === 'string') {
                                    try {
                                      valuesIds = JSON.parse(productParam.valuesIds)
                                    } catch {
                                      valuesIds = []
                                    }
                                  } else {
                                    valuesIds = Array.isArray(productParam.valuesIds) ? productParam.valuesIds : [productParam.valuesIds]
                                  }
                                }
                                
                                if (hasDictionary && paramDictionary && valuesIds.length > 0) {
                                  const matchingDictItem = paramDictionary.find((item: any) => item.id === valuesIds[0])
                                  if (matchingDictItem) {
                                    displayValue = matchingDictItem.id
                                  }
                                } else if (valuesIds.length > 0) {
                                  displayValue = valuesIds[0]
                                }
                              }
                              
                              const isRequired = isParameterRequired(param, offer.selectedParameters, offer.selectedOfferParameters)
                              const isFilled = displayValue !== '' && displayValue !== null && displayValue !== undefined
                              const colorClass = getParameterColorClass(param, displayValue, offer)
                              
                              return (
                                <div key={param.id} className={`border rounded p-2 ${colorClass}`}>
                                  <label className={`block text-xs font-medium mb-1 ${isRequired && !isFilled ? 'text-red-700' : isRequired && isFilled ? 'text-green-700' : 'text-gray-700'}`}>
                                    {param.name}{param.unit && ` [${param.unit}]`}
                                    {isRequired && <span className="text-red-500 ml-1">*</span>}
                                  </label>
                                  {shouldShowDropdown ? (
                                    <select
                                      value={displayValue}
                                      onChange={(e) => {
                                        if (isProductParam) {
                                          handleParameterChange(param.id, e.target.value, offerIndex)
                                        } else {
                                          handleOfferParameterChange(param.id, e.target.value, offerIndex)
                                        }
                                      }}
                                      className={`w-full px-2 py-1 text-xs border rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${
                                        isRequired && !isFilled ? 'border-red-300' : isRequired && isFilled ? 'border-green-300' : 'border-gray-300'
                                      }`}
                                    >
                                      <option value="">Wybierz</option>
                                      {hasDictionary ? (
                                        paramDictionary.map((item: any) => (
                                          <option key={item.id} value={item.id}>
                                            {item.value}
                                          </option>
                                        ))
                                      ) : hasValuesLabels ? (
                                        param.valuesIds.map((id: string, idx: number) => (
                                          <option key={id} value={id}>
                                            {param.valuesLabels[idx] || id}
                                          </option>
                                        ))
                                      ) : (
                                        param.values.map((val: any, idx: number) => {
                                          const value = typeof val === 'object' ? val.value : val
                                          const name = typeof val === 'object' ? (val.name || val.value) : val
                                          return (
                                            <option key={value || idx} value={value}>
                                              {name}
                                            </option>
                                          )
                                        })
                                      )}
                                    </select>
                                  ) : (
                                    <input
                                      type={param.type === 'integer' || param.type === 'float' ? 'number' : 'text'}
                                      value={displayValue}
                                      onChange={(e) => {
                                        if (isProductParam) {
                                          handleParameterChange(param.id, e.target.value, offerIndex)
                                        } else {
                                          handleOfferParameterChange(param.id, e.target.value, offerIndex)
                                        }
                                      }}
                                      className={`w-full px-2 py-1 text-xs border rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${
                                        isRequired && !isFilled ? 'border-red-300' : isRequired && isFilled ? 'border-green-300' : 'border-gray-300'
                                      }`}
                                      placeholder={param.unit ? `${param.name} [${param.unit}]` : param.name}
                                      min={param.restrictions?.min}
                                      max={param.restrictions?.max}
                                    />
                                  )}
                                </div>
                              )
                            })}
                          </div>
                        )
                      })()}
                    </div>
                  </div>
                )}
                
                {/* Expanded DANE Section */}
                {isDataExpanded && (
                  <div className="px-6 py-4 bg-white border-t border-gray-200">
                    <div className="grid grid-cols-6 gap-3">
                      {/* Delivery Settings */}
                      {shippingRates.length > 0 && (() => {
                        const isRequired = true
                        const isFilled = !!offer.selectedShippingRate
                        const borderClass = getDaneFieldBorderClass(isRequired, isFilled)
                        const bgClass = getDaneFieldBgClass(isRequired, isFilled)
                        return (
                          <div className={`border rounded p-2 ${bgClass}`}>
                            <label className={`block text-xs font-medium mb-1 ${isRequired && !isFilled ? 'text-red-700' : isRequired && isFilled ? 'text-green-700' : 'text-gray-700'}`}>
                              Cennik dostawy *
                            </label>
                            <select
                              value={offer.selectedShippingRate}
                              onChange={(e) => updateOfferField('selectedShippingRate', e.target.value, offerIndex)}
                              className={`w-full px-2 py-1 text-xs border rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${borderClass}`}
                            >
                              <option value="">Wybierz</option>
                              {shippingRates.map((rate) => (
                                <option key={rate.id} value={rate.id}>
                                  {rate.name}
                                </option>
                              ))}
                            </select>
                          </div>
                        )
                      })()}
                      
                      {(() => {
                        const isRequired = true
                        const isFilled = !!offer.handlingTime
                        const borderClass = getDaneFieldBorderClass(isRequired, isFilled)
                        const bgClass = getDaneFieldBgClass(isRequired, isFilled)
                        return (
                          <div className={`border rounded p-2 ${bgClass}`}>
                            <label className={`block text-xs font-medium mb-1 ${isRequired && !isFilled ? 'text-red-700' : isRequired && isFilled ? 'text-green-700' : 'text-gray-700'}`}>
                              Czas dostawy *
                            </label>
                            <select
                              value={offer.handlingTime}
                              onChange={(e) => updateOfferField('handlingTime', e.target.value, offerIndex)}
                              className={`w-full px-2 py-1 text-xs border rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${borderClass}`}
                            >
                          <option value="PT0S">Natychmiast</option>
                          <option value="PT24H">24 godziny</option>
                          <option value="P2D">2 dni</option>
                          <option value="P3D">3 dni</option>
                          <option value="P4D">4 dni</option>
                          <option value="P5D">5 dni</option>
                          <option value="P7D">7 dni</option>
                          <option value="P10D">10 dni</option>
                          <option value="P14D">14 dni</option>
                          <option value="P21D">21 dni</option>
                          <option value="P30D">30 dni</option>
                          <option value="P60D">60 dni</option>
                            </select>
                          </div>
                        )
                      })()}
                      
                      {/* Responsible Producer/Person */}
                      {responsibleProducers.length > 0 && (() => {
                        const isRequired = true
                        const isFilled = !!offer.selectedResponsibleProducerId
                        const borderClass = getDaneFieldBorderClass(isRequired, isFilled)
                        const bgClass = getDaneFieldBgClass(isRequired, isFilled)
                        return (
                          <div className={`border rounded p-2 ${bgClass}`}>
                            <label className={`block text-xs font-medium mb-1 ${isRequired && !isFilled ? 'text-red-700' : isRequired && isFilled ? 'text-green-700' : 'text-gray-700'}`}>
                              Producent odpowiedzialny *
                            </label>
                            <select
                              value={offer.selectedResponsibleProducerId}
                              onChange={(e) => updateOfferField('selectedResponsibleProducerId', e.target.value, offerIndex)}
                              className={`w-full px-2 py-1 text-xs border rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${borderClass}`}
                            >
                              <option value="">Wybierz</option>
                              {responsibleProducers.map((producer) => (
                                <option key={producer.id} value={producer.id}>
                                  {producer.name}
                                </option>
                              ))}
                            </select>
                          </div>
                        )
                      })()}
                      
                      {responsiblePersons.length > 0 && (() => {
                        const isRequired = !offer.selectedResponsibleProducerId
                        const isFilled = !!offer.selectedResponsiblePersonId
                        const borderClass = getDaneFieldBorderClass(isRequired, isFilled)
                        const bgClass = getDaneFieldBgClass(isRequired, isFilled)
                        return (
                          <div className={`border rounded p-2 ${bgClass}`}>
                            <label className={`block text-xs font-medium mb-1 ${isRequired && !isFilled ? 'text-red-700' : isRequired && isFilled ? 'text-green-700' : 'text-gray-700'}`}>
                              Osoba odpowiedzialna * {offer.selectedResponsibleProducerId ? '(opc.)' : ''}
                            </label>
                            <select
                              value={offer.selectedResponsiblePersonId}
                              onChange={(e) => updateOfferField('selectedResponsiblePersonId', e.target.value, offerIndex)}
                              className={`w-full px-2 py-1 text-xs border rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${borderClass}`}
                              disabled={!!offer.selectedResponsibleProducerId}
                            >
                              <option value="">Wybierz</option>
                              {responsiblePersons.map((person) => (
                                <option key={person.id} value={person.id}>
                                  {person.name}
                                </option>
                              ))}
                            </select>
                          </div>
                        )
                      })()}
                      
                      {(() => {
                        const isRequired = true
                        const isFilled = !!offer.safetyInformation.trim()
                        const borderClass = getDaneFieldBorderClass(isRequired, isFilled)
                        const bgClass = getDaneFieldBgClass(isRequired, isFilled)
                        return (
                          <div className={`border rounded p-2 col-span-2 ${bgClass}`}>
                            <label className={`block text-xs font-medium mb-1 ${isRequired && !isFilled ? 'text-red-700' : isRequired && isFilled ? 'text-green-700' : 'text-gray-700'}`}>
                              Informacje o bezpieczeństwie *
                            </label>
                            <textarea
                              value={offer.safetyInformation}
                              onChange={(e) => updateOfferField('safetyInformation', e.target.value, offerIndex)}
                              className={`w-full px-2 py-1 text-xs border rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${borderClass}`}
                              rows={2}
                              placeholder="Wprowadź informacje o bezpieczeństwie"
                            />
                          </div>
                        )
                      })()}
                      
                      {/* Offer Duration */}
                      {(() => {
                        const isRequired = true
                        const isFilled = !!offer.durationType
                        const borderClass = getDaneFieldBorderClass(isRequired, isFilled)
                        const bgClass = getDaneFieldBgClass(isRequired, isFilled)
                        return (
                          <div className={`border rounded p-2 ${bgClass}`}>
                            <label className={`block text-xs font-medium mb-1 ${isRequired && !isFilled ? 'text-red-700' : isRequired && isFilled ? 'text-green-700' : 'text-gray-700'}`}>
                              Typ trwania *
                            </label>
                            <select
                              value={offer.durationType || 'fixed'}
                              onChange={(e) => {
                                const newDurationType = e.target.value as 'fixed' | 'unlimited'
                                // Use functional update to ensure we have the latest state
                                setOffers(prevOffers => {
                                  if (prevOffers.length === 0 || !prevOffers[offerIndex]) return prevOffers
                                  const updatedOffers = [...prevOffers]
                                  const currentOffer = updatedOffers[offerIndex]
                                  updatedOffers[offerIndex] = {
                                    ...currentOffer,
                                    durationType: newDurationType,
                                    duration: newDurationType === 'unlimited' ? '' : (currentOffer.duration || 'PT720H')
                                  }
                                  return updatedOffers
                                })
                              }}
                              className={`w-full px-2 py-1 text-xs border rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${borderClass}`}
                            >
                              <option value="fixed">Określony czas</option>
                              <option value="unlimited">Do wyczerpania zapasów</option>
                            </select>
                          </div>
                        )
                      })()}
                      
                      {offer.durationType === 'fixed' && (() => {
                        const isRequired = true
                        const isFilled = !!offer.duration
                        const borderClass = getDaneFieldBorderClass(isRequired, isFilled)
                        const bgClass = getDaneFieldBgClass(isRequired, isFilled)
                        return (
                          <div className={`border rounded p-2 ${bgClass}`}>
                            <label className={`block text-xs font-medium mb-1 ${isRequired && !isFilled ? 'text-red-700' : isRequired && isFilled ? 'text-green-700' : 'text-gray-700'}`}>
                              Okres trwania *
                            </label>
                            <select
                              value={offer.duration}
                              onChange={(e) => updateOfferField('duration', e.target.value, offerIndex)}
                              className={`w-full px-2 py-1 text-xs border rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${borderClass}`}
                            >
                              <option value="PT168H">7 dni</option>
                              <option value="PT336H">14 dni</option>
                              <option value="PT720H">30 dni</option>
                              <option value="PT1440H">60 dni</option>
                            </select>
                          </div>
                        )
                      })()}
                      
                      {/* Returns */}
                      {returnPolicies.length > 0 && (() => {
                        const isRequired = true
                        const isFilled = !!offer.returnPolicyId
                        const borderClass = getDaneFieldBorderClass(isRequired, isFilled)
                        const bgClass = getDaneFieldBgClass(isRequired, isFilled)
                        return (
                          <div className={`border rounded p-2 ${bgClass}`}>
                            <label className={`block text-xs font-medium mb-1 ${isRequired && !isFilled ? 'text-red-700' : isRequired && isFilled ? 'text-green-700' : 'text-gray-700'}`}>
                              Warunki zwrotów *
                            </label>
                            <select
                              value={offer.returnPolicyId}
                              onChange={(e) => updateOfferField('returnPolicyId', e.target.value, offerIndex)}
                              className={`w-full px-2 py-1 text-xs border rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${borderClass}`}
                            >
                              <option value="">Wybierz</option>
                              {returnPolicies.map((policy) => (
                                <option key={policy.id} value={policy.id}>
                                  {policy.name}
                                </option>
                              ))}
                            </select>
                          </div>
                        )
                      })()}
                      
                      {/* Invoice and Tax Settings */}
                      <div className="border rounded p-2">
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Wystawianie faktury
                        </label>
                        <select
                          value={offer.invoiceType}
                          onChange={(e) => {
                            updateOfferField('invoiceType', e.target.value, offerIndex)
                            if (e.target.value === 'NO_INVOICE' || e.target.value === 'WITHOUT_VAT') {
                              updateOfferField('selectedTaxRates', {}, offerIndex)
                              updateOfferField('selectedTaxSubject', '', offerIndex)
                              updateOfferField('selectedTaxExemption', '', offerIndex)
                            }
                          }}
                          className="w-full px-2 py-1 text-xs border rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                        >
                          <option value="NO_INVOICE">Nie wystawiam faktury</option>
                          <option value="VAT">Wystawiam fakturę VAT</option>
                          <option value="VAT_MARGIN">Faktura VAT marża</option>
                          <option value="WITHOUT_VAT">Bez VAT</option>
                        </select>
                      </div>
                      
                      {/* Tax Settings - only show when invoice is VAT */}
                      {(offer.invoiceType === 'VAT' || offer.invoiceType === 'VAT_MARGIN') && taxSettings && (
                        <>
                          {taxSettings.subjects && taxSettings.subjects.length > 0 && (() => {
                            const isRequired = true
                            const isFilled = !!offer.selectedTaxSubject
                            const borderClass = getDaneFieldBorderClass(isRequired, isFilled)
                            const bgClass = getDaneFieldBgClass(isRequired, isFilled)
                            return (
                              <div className={`border rounded p-2 ${bgClass}`}>
                                <label className={`block text-xs font-medium mb-1 ${isRequired && !isFilled ? 'text-red-700' : isRequired && isFilled ? 'text-green-700' : 'text-gray-700'}`}>
                                  Przedmiot opodatkowania *
                                </label>
                                <select
                                  value={offer.selectedTaxSubject}
                                  onChange={(e) => updateOfferField('selectedTaxSubject', e.target.value, offerIndex)}
                                  className={`w-full px-2 py-1 text-xs border rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${borderClass}`}
                                >
                                  <option value="">Wybierz</option>
                                  {taxSettings.subjects.map((subject) => (
                                    <option key={subject.value} value={subject.value}>
                                      {subject.label}
                                    </option>
                                  ))}
                                </select>
                              </div>
                            )
                          })()}
                          
                          {taxSettings.rates && taxSettings.rates.length > 0 && (
                            <>
                              {taxSettings.rates.map((countryRate) => {
                                const isRequired = countryRate.countryCode === 'PL'
                                const isFilled = !!offer.selectedTaxRates[countryRate.countryCode]
                                const borderClass = getDaneFieldBorderClass(isRequired, isFilled)
                                const bgClass = getDaneFieldBgClass(isRequired, isFilled)
                                return (
                                  <div key={countryRate.countryCode} className={`border rounded p-2 ${bgClass}`}>
                                    <label className={`block text-xs font-medium mb-1 ${isRequired && !isFilled ? 'text-red-700' : isRequired && isFilled ? 'text-green-700' : 'text-gray-700'}`}>
                                      {countryRate.countryCode === 'PL' ? 'Polska' : 
                                       countryRate.countryCode === 'CZ' ? 'Czechy' :
                                       countryRate.countryCode === 'SK' ? 'Słowacja' :
                                       countryRate.countryCode === 'HU' ? 'Węgry' : countryRate.countryCode}
                                      {countryRate.countryCode === 'PL' && ' *'}
                                    </label>
                                    <select
                                      value={offer.selectedTaxRates[countryRate.countryCode] || ''}
                                      onChange={(e) => {
                                        updateOfferField('selectedTaxRates', {
                                          ...offer.selectedTaxRates,
                                          [countryRate.countryCode]: e.target.value
                                        }, offerIndex)
                                      }}
                                      className={`w-full px-2 py-1 text-xs border rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${borderClass}`}
                                    >
                                      <option value="">Wybierz</option>
                                      {countryRate.values.map((rate) => (
                                        <option key={rate.value} value={rate.value}>
                                          {rate.label} ({rate.value}%)
                                        </option>
                                      ))}
                                    </select>
                                  </div>
                                )
                              })}
                            </>
                          )}
                          
                          {taxSettings.exemptions && taxSettings.exemptions.length > 0 && (
                            <div className="border rounded p-2">
                              <label className="block text-xs font-medium text-gray-700 mb-1">
                                Zwolnienie z VAT (opc.)
                              </label>
                              <select
                                value={offer.selectedTaxExemption}
                                onChange={(e) => updateOfferField('selectedTaxExemption', e.target.value, offerIndex)}
                                className="w-full px-2 py-1 text-xs border rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                              >
                                <option value="">Brak zwolnienia</option>
                                {taxSettings.exemptions.map((exemption) => (
                                  <option key={exemption.value} value={exemption.value}>
                                    {exemption.label}
                                  </option>
                                ))}
                              </select>
                            </div>
                          )}
                        </>
                      )}
                      
                      {/* SKU */}
                      <div className="border rounded p-2">
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          SKU (opcjonalnie)
                        </label>
                        <input
                          type="text"
                          value={offer.sku}
                          onChange={(e) => updateOfferField('sku', e.target.value, offerIndex)}
                          className="w-full px-2 py-1 text-xs border rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                          placeholder="Wprowadź SKU"
                        />
                      </div>
                      
                      {/* Missing Fields Info */}
                      {(() => {
                        const missingFields = getMissingFields(offer)
                        if (missingFields.length > 0) {
                          return (
                            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                              <p className="text-sm font-medium text-yellow-800 mb-1">
                                Aby wystawić ofertę, wypełnij jeszcze:
                              </p>
                              <ul className="text-sm text-yellow-700 list-disc list-inside space-y-1">
                                {missingFields.map((field, idx) => (
                                  <li key={idx}>{field}</li>
                                ))}
                              </ul>
                            </div>
                          )
                        }
                        return null
                      })()}
                    </div>
                  </div>
                )}
              </div>
            )
            })
          })()}
        </div>
      )}
      
      {/* Product Selector Modal */}
      <Modal
        isOpen={showProductSelectorModal}
        onClose={() => setShowProductSelectorModal(false)}
        title="Wybierz produkt z katalogu"
        className="max-w-5xl"
      >
        {(() => {
          // Find the offer that matches the EAN for the modal
          const offerForModal = offers.find(o => o.ean === currentEanForModal)
          if (!offerForModal) return null
          
          return (
            <div className="space-y-3">
              {offerForModal.products.map((product) => {
                // Extract brand from parameters
                const brandParam = product.parameters?.find(p => 
                  p.name?.toLowerCase().includes('marka') || 
                  p.name?.toLowerCase().includes('brand') ||
                  p.id === '11323' // Common brand parameter ID in Allegro
                )
                
                // Get brand name - try to map ID to name using category parameters dictionary
                let brand = null
                if (brandParam) {
                  // Find category parameter for brand to access dictionary
                  const categoryBrandParam = offerForModal.categoryParameters?.find(p => 
                    p.id === brandParam.id || 
                    p.name?.toLowerCase().includes('marka') ||
                    p.name?.toLowerCase().includes('brand')
                  )
                  
                  // Get brand ID (from valuesIds or from values if it looks like an ID)
                  let brandId: string | null = null
                  if (Array.isArray(brandParam.valuesIds) && brandParam.valuesIds.length > 0) {
                    brandId = brandParam.valuesIds[0]
                  } else if (Array.isArray(brandParam.values) && brandParam.values.length > 0) {
                    const firstValue = brandParam.values[0]
                    // Check if it looks like an ID (contains underscore or is numeric)
                    if (typeof firstValue === 'string' && (firstValue.includes('_') || /^\d+$/.test(firstValue))) {
                      brandId = firstValue
                    } else {
                      // It's probably a name, use it directly
                      brand = firstValue
                    }
                  } else if (typeof brandParam.values === 'string') {
                    const value = brandParam.values
                    if (value.includes('_') || /^\d+$/.test(value)) {
                      brandId = value
                    } else {
                      brand = value
                    }
                  }
                  
                  // If we have an ID, try to map it to name using dictionary
                  if (brandId && categoryBrandParam) {
                    // Try dictionary directly on parameter
                    if (categoryBrandParam.dictionary) {
                      const brandDictItem = categoryBrandParam.dictionary.find((item: any) => item.id === brandId)
                      brand = brandDictItem?.value || brandId
                    } else if (categoryBrandParam.options?.dictionary) {
                      // Try nested dictionary
                      const brandDictItem = categoryBrandParam.options.dictionary.find((item: any) => item.id === brandId)
                      brand = brandDictItem?.value || brandId
                    } else {
                      // Fallback to ID if no dictionary available
                      brand = brandId
                    }
                  } else if (brandId && !brand) {
                    // ID but no dictionary available
                    brand = brandId
                  }
                }
                
                // Get category path
                const categoryPath = product.category?.path?.map(c => c.name).join(' / ') || 'Brak kategorii'
                
                return (
                  <div
                    key={product.id}
                    className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
                  >
                    <div className="flex items-start gap-4">
                      {/* Image - fixed width */}
                      <div className="flex-shrink-0 w-20 h-20">
                        {product.images && product.images.length > 0 ? (
                          <img
                            src={product.images[0].url}
                            alt={product.name}
                            className="w-20 h-20 object-cover rounded"
                          />
                        ) : (
                          <div className="w-20 h-20 bg-gray-100 rounded flex items-center justify-center">
                            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                          </div>
                        )}
                      </div>
                      
                      {/* Content - flexible, with min-width 0 for truncate to work */}
                      <div className="flex-1 min-w-0">
                        {/* Title - always in same place, with truncate */}
                        <h3 className="font-semibold text-lg truncate pr-2" title={product.name}>
                          {product.name}
                        </h3>
                        
                        {/* Brand - separate line */}
                        {brand && (
                          <div className="text-sm text-gray-600 mt-1">
                            Marka: <span className="font-medium">{brand}</span>
                          </div>
                        )}
                        
                        {/* Category - separate line */}
                        <div className="text-sm text-gray-600 mt-1">
                          <span>Kategoria: <span className="font-medium truncate" title={categoryPath}>{categoryPath}</span></span>
                        </div>
                      </div>
                      
                      {/* Buttons - fixed width, always in same place */}
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            window.open(`https://allegro.pl/oferty-produktu/${product.id}`, '_blank')
                          }}
                          className="px-3 py-1.5 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors flex items-center gap-1 whitespace-nowrap"
                        >
                          <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                          <span>Pokaż</span>
                        </button>
                        <button
                          onClick={() => handleSelectProductFromModal(product)}
                          className={`px-3 py-1.5 text-sm rounded transition-colors whitespace-nowrap ${
                            offerForModal.selectedProductId === product.id
                              ? 'bg-green-500 text-white hover:bg-green-600'
                              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                          }`}
                        >
                          {offerForModal.selectedProductId === product.id ? '✓ Wybrany' : 'Wybierz'}
                        </button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )
        })()}
      </Modal>
      
      {/* Logs Section */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Logi</h2>
          <button
            onClick={() => setLogs([])}
            className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
          >
            Wyczyść logi
          </button>
        </div>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {logs.length === 0 ? (
            <div className="text-sm text-gray-500 text-center py-4">Brak logów</div>
          ) : (
            logs.map((log, idx) => (
              <div 
                key={idx} 
                className={`p-3 rounded-lg border-l-4 ${
                  log.level === 'error' 
                    ? 'bg-red-50 border-red-400 text-red-800' 
                    : log.level === 'success'
                    ? 'bg-green-50 border-green-400 text-green-800'
                    : 'bg-blue-50 border-blue-400 text-blue-800'
                }`}
              >
                <div className="text-sm font-medium">{log.message}</div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
