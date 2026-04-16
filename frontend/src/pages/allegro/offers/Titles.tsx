import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { useAccountStore } from '../../../store/accountStore'
import { useBulkEditTitles } from '../../../hooks/shared/offers/bulk'
import { usePullTitles } from '../../../hooks/shared/offers/bulk'
import { useDuplicateOffers } from '../../../hooks/shared/offers'
import { useTaskStatus } from '../../../hooks/shared/tasks'
import { useMultipleTaskStatus } from '../../../hooks/shared/tasks'
import { useOptimizeTitlesAI, useAIOptimizationTaskStatus, type TitleToOptimize, type OptimizedTitleResult, type AIOptimizationTaskStatus } from '../../../hooks/shared/ai'
import { useAIConfigStatus } from '../../../hooks/shared/ai'
import { useToastStore } from '../../../store/toastStore'
import { useSharedAccounts } from '../../../hooks/marketplaces/allegro/accounts'
import AccountSelector from '../../../components/ui/AccountSelector'
import FileImportButton from '../../../components/ui/FileImportButton'
import AIOptimizationPanel from '../../../components/titles/AIOptimizationPanel'
import TitleComparisonView from '../../../components/titles/TitleComparisonView'
import { FileImportResult } from '../../../hooks/shared/pricing'
import { AlertTriangle, Copy, Info } from 'lucide-react'
import OfferSelectorButton from '../../../components/ui/OfferSelectorButton'
import { Link } from 'react-router-dom'

interface TaskResponse {
  task_id: string
  offer_id: string
}

interface TaskStatus {
  task_id: string
  offer_id: string
  status: 'PENDING' | 'PROGRESS' | 'SUCCESS' | 'FAILURE'
  result?: any
  meta?: any
}

interface PullTaskStatus {
  status: 'PENDING' | 'PROGRESS' | 'SUCCESS' | 'FAILURE'
  result?: {
    download_url?: string
    fetched_titles?: number
    total_offers?: number
    status?: string
    progress?: number
    exc_message?: string
    error?: string
  }
}

export default function Titles() {
  const { current } = useAccountStore()
  const { accounts, isLoading: accountsLoading } = useSharedAccounts()
  const { addToast } = useToastStore()
  
  // State for two sections with localStorage persistence
  const [pullOfferIds, setPullOfferIds] = useState(() => {
    return localStorage.getItem('titles-pull-offer-ids') || ''
  })
  const [updateTitlesData, setUpdateTitlesData] = useState(() => {
    return localStorage.getItem('titles-update-data') || ''
  })
  
  // Error states
  const [pullError, setPullError] = useState<string | null>(null)
  const [updateError, setUpdateError] = useState<string | null>(null)
  
  // AI Optimization state
  const [aiOptimizationResults, setAiOptimizationResults] = useState<OptimizedTitleResult[] | null>(null)
  const [acceptedOfferIds, setAcceptedOfferIds] = useState<Set<string>>(new Set())
  const [includeOfferParameters, setIncludeOfferParameters] = useState(false)
  
  
  // Account change handling
  const [previousAccountId, setPreviousAccountId] = useState<number | null>(null)
  const [showAccountChangeModal, setShowAccountChangeModal] = useState(false)
  
  // Mutations
  const pullTitlesMutation = usePullTitles()
  const bulkEditTitlesMutation = useBulkEditTitles()
  const duplicateOffersMutation = useDuplicateOffers()
  const optimizeTitlesAIMutation = useOptimizeTitlesAI()
  const { data: aiStatus } = useAIConfigStatus()
  
  // Task tracking
  const [pullTaskId, setPullTaskId] = useState<string | undefined>(undefined)
  const [updateTaskId, setUpdateTaskId] = useState<string | undefined>(undefined)
  const [duplicateTaskId, setDuplicateTaskId] = useState<string | undefined>(undefined)
  const [aiOptimizationTaskId, setAiOptimizationTaskId] = useState<string | undefined>(undefined)
  
  const { data: pullTaskStatus } = useTaskStatus(pullTaskId)
  const { data: updateTaskStatus } = useTaskStatus(updateTaskId)
  const { data: duplicateTaskStatus } = useTaskStatus(duplicateTaskId)
  const { data: aiOptimizationTaskStatus } = useAIOptimizationTaskStatus(aiOptimizationTaskId)
  
  // Duplicate functionality state
  const [showDuplicateConfirmModal, setShowDuplicateConfirmModal] = useState(false)
  const [showDuplicateModal, setShowDuplicateModal] = useState(false)

  // Save pullOfferIds to localStorage
  useEffect(() => {
    localStorage.setItem('titles-pull-offer-ids', pullOfferIds)
  }, [pullOfferIds])

  // Save updateTitlesData to localStorage
  useEffect(() => {
    localStorage.setItem('titles-update-data', updateTitlesData)
  }, [updateTitlesData])

  // Save AI optimization results to localStorage
  useEffect(() => {
    if (aiOptimizationResults && aiOptimizationResults.length > 0) {
      localStorage.setItem('titles-ai-optimization-results', JSON.stringify(aiOptimizationResults))
    }
  }, [aiOptimizationResults])

  // Save accepted offer IDs to localStorage
  useEffect(() => {
    if (acceptedOfferIds.size > 0) {
      localStorage.setItem('titles-ai-accepted-ids', JSON.stringify(Array.from(acceptedOfferIds)))
    }
  }, [acceptedOfferIds])

  // Load AI optimization results from localStorage on mount
  useEffect(() => {
    const savedResults = localStorage.getItem('titles-ai-optimization-results')
    const savedAccepted = localStorage.getItem('titles-ai-accepted-ids')
    
    if (savedResults) {
      try {
        const results = JSON.parse(savedResults)
        setAiOptimizationResults(results)
      } catch (e) {
        console.error('Failed to parse saved AI optimization results:', e)
      }
    }
    
    if (savedAccepted) {
      try {
        const accepted = JSON.parse(savedAccepted)
        setAcceptedOfferIds(new Set(accepted))
      } catch (e) {
        console.error('Failed to parse saved accepted IDs:', e)
      }
    }
  }, [])

  // Handle AI optimization task completion
  useEffect(() => {
    if (!aiOptimizationTaskStatus) return

    if (aiOptimizationTaskStatus.status === 'SUCCESS' && aiOptimizationTaskStatus.result) {
      const result = aiOptimizationTaskStatus.result as any
      if (result.results && Array.isArray(result.results)) {
        setAiOptimizationResults(result.results)
        
        // Auto-accept all successful results
        const successfulOfferIds: Set<string> = new Set(
          result.results.filter((r: OptimizedTitleResult) => r.success).map((r: OptimizedTitleResult) => r.offer_id)
        )
        setAcceptedOfferIds(successfulOfferIds)

        addToast(
          `Optymalizacja zakończona: ${result.successful} sukces, ${result.failed} błędów`,
          result.failed > 0 ? 'error' : 'success'
        )
        
        // Clear task ID
        setAiOptimizationTaskId(undefined)
      }
    } else if (aiOptimizationTaskStatus.status === 'FAILURE') {
      const result = aiOptimizationTaskStatus.result as any
      const errorMessage = result?.exc_message || 'Wystąpił błąd podczas optymalizacji z AI'
      setUpdateError(errorMessage)
      addToast('Błąd podczas optymalizacji z AI', 'error')
      setAiOptimizationTaskId(undefined)
    }
  }, [aiOptimizationTaskStatus, addToast])

  // Handle account changes and offer ID conflicts
  useEffect(() => {
    if (current && previousAccountId !== null && current.id !== previousAccountId) {
      // Account changed - check if there are offer IDs that might not belong to new account
      if (pullOfferIds.trim() && !showAccountChangeModal) {
        setShowAccountChangeModal(true)
      }
    }
    
    if (current) {
      setPreviousAccountId(current.id)
    }
  }, [current, previousAccountId, pullOfferIds, showAccountChangeModal])

  // Compute task summary for update tasks
  const getUpdateTaskSummary = () => {
    if (!updateTaskStatus) return null

    const isCompleted = updateTaskStatus.status === 'SUCCESS' || updateTaskStatus.status === 'FAILURE'
    
    // Extract counts from task result/meta if available
    const result: any = updateTaskStatus.result || {}
    const meta: any = updateTaskStatus.meta || {}
    const total = result.total_offers || meta.total_offers || 0
    const successCount = result.success_count || meta.successful || 0
    const failureCount = result.failure_count || meta.failed || 0
    
    // Extract failed offers for detailed error display
    const failedOffers = result.failed_offers || []

    return {
      total: total,
      successCount: successCount,
      failureCount: failureCount,
      pendingCount: isCompleted ? 0 : Math.max(0, total - successCount - failureCount),
      allCompleted: isCompleted,
      hasFailures: failureCount > 0,
      results: failedOffers // Failed offers with error details
    }
  }

  const updateTasksStatus = getUpdateTaskSummary()

  // Compute task summary for duplicate tasks
  const getDuplicateTaskSummary = () => {
    if (!duplicateTaskStatus) return null

    const isCompleted = duplicateTaskStatus.status === 'SUCCESS' || duplicateTaskStatus.status === 'FAILURE'
    
    // Extract counts from task result/meta if available
    const result: any = duplicateTaskStatus.result || {}
    const meta: any = duplicateTaskStatus.meta || {}
    const total = result.total_offers || meta.total_offers || 0
    const successCount = result.success_count || meta.successful || 0
    const failureCount = result.failure_count || meta.failed || 0
    
    // Extract duplicated offers mapping and failed offers
    const duplicatedOffers = result.duplicated_offers || []
    const failedOffers = result.failed_offers || []

    return {
      total: total,
      successCount: successCount,
      failureCount: failureCount,
      pendingCount: isCompleted ? 0 : Math.max(0, total - successCount - failureCount),
      allCompleted: isCompleted,
      hasFailures: failureCount > 0,
      duplicatedOffers: duplicatedOffers, // [{old_id, new_id, title}]
      failedOffers: failedOffers // [{offer_id, title, error}]
    }
  }

  const duplicateTasksStatus = getDuplicateTaskSummary()

  const handlePullTitles = () => {
    if (!current) return
    
    // Clear previous errors
    setPullError(null)
    
    const offerIds = pullOfferIds
      .split('\n')
      .map(id => id.trim())
      .filter(id => id.length > 0)
    
    if (offerIds.length === 0) {
      setPullError('Wprowadź ID ofert')
      return
    }

    // Validate offer IDs format
    const invalidIds = offerIds.filter(id => !/^\d+$/.test(id))
    if (invalidIds.length > 0) {
      setPullError(`Nieprawidłowe ID ofert: ${invalidIds.slice(0, 5).join(', ')}${invalidIds.length > 5 ? ` i ${invalidIds.length - 5} więcej` : ''}. ID oferty powinno składać się tylko z cyfr.`)
      return
    }

    // Validate reasonable ID length (Allegro IDs are typically 11 digits)
    const suspiciousIds = offerIds.filter(id => id.length < 10 || id.length > 15)
    if (suspiciousIds.length > 0) {
      setPullError(`Podejrzane ID ofert (nietypowa długość): ${suspiciousIds.slice(0, 5).join(', ')}${suspiciousIds.length > 5 ? ` i ${suspiciousIds.length - 5} więcej` : ''}. Sprawdź czy ID są prawidłowe.`)
      return
    }

    pullTitlesMutation.mutate(
      { account_id: current.id, offer_ids: offerIds },
      {
        onSuccess: (data) => {
          setPullTaskId(data.task_id)
          // Optionally clear the input after successful submission
          // setPullOfferIds('')
          // localStorage.removeItem('titles-pull-offer-ids')
        },
        onError: (error: any) => {
          if (isAccessDeniedError(error)) {
            setPullError('ACCESS_DENIED')
          } else {
            setPullError(error?.response?.data?.detail || error?.message || 'Wystąpił błąd podczas pobierania tytułów')
          }
        }
      }
    )
  }

  const handleUpdateTitles = () => {
    if (!current) return
    
    // Clear previous errors
    setUpdateError(null)
    
    const lines = updateTitlesData
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0)
    
    if (lines.length === 0) {
      setUpdateError('Wprowadź ID ofert i tytuły')
      return
    }

    try {
      const items = lines.map((line, index) => {
        // Auto-detect separator - try comma first, then semicolon
        let parts = line.split(',')
        if (parts.length < 2) {
          parts = line.split(';')
        }
        if (parts.length < 2) {
          parts = line.split('\t') // Try tab as well
        }
        if (parts.length < 2) {
          parts = line.split('|') // Try pipe as well
        }
        
        if (parts.length < 2) {
          throw new Error(`Nieprawidłowy format linii ${index + 1}: "${line}". Użyj formatu: ID,Tytuł (separatory: , ; | tab)`)
        }
        
        const offer_id = parts[0].trim()
        const title = parts.slice(1).join(',').trim()
        
        // Validate offer ID format
        if (!/^\d+$/.test(offer_id)) {
          throw new Error(`Nieprawidłowe ID oferty w linii ${index + 1}: "${offer_id}". ID powinno składać się tylko z cyfr.`)
        }
        
        // Validate reasonable ID length (Allegro IDs are typically 11 digits)
        if (offer_id.length < 10 || offer_id.length > 15) {
          throw new Error(`Podejrzane ID oferty w linii ${index + 1}: "${offer_id}" (nietypowa długość). Sprawdź czy ID jest prawidłowe.`)
        }
        
        // Validate title is not empty
        if (!title) {
          throw new Error(`Pusty tytuł w linii ${index + 1}: "${line}"`)
        }
        
        return { offer_id, title }
      })

      // Check for duplicates
      const seenIds = new Set()
      const duplicates = []
      for (const item of items) {
        if (seenIds.has(item.offer_id)) {
          duplicates.push(item.offer_id)
        } else {
          seenIds.add(item.offer_id)
        }
      }
      
      if (duplicates.length > 0) {
        throw new Error(`Znaleziono duplikaty ID ofert: ${[...new Set(duplicates)].join(', ')}. Każda oferta może być aktualizowana tylko raz.`)
      }

      // Remove duplicates (keep last occurrence)
      const uniqueItems = []
      const processedIds = new Set()
      for (let i = items.length - 1; i >= 0; i--) {
        const item = items[i]
        if (!processedIds.has(item.offer_id)) {
          uniqueItems.unshift(item)
          processedIds.add(item.offer_id)
        }
      }

      bulkEditTitlesMutation.mutate(
        { account_id: current.id, items: uniqueItems },
        {
          onSuccess: (response) => {
            // Store task ID for monitoring - response.data contains the single task
            setUpdateTaskId(response.data?.task_id)
          },
          onError: (error: any) => {
            if (isAccessDeniedError(error)) {
              setUpdateError('ACCESS_DENIED')
            } else {
              setUpdateError(error?.response?.data?.detail || error?.message || 'Wystąpił błąd podczas aktualizacji tytułów')
            }
          }
        }
      )
    } catch (error: any) {
      setUpdateError(error.message)
    }
  }

  const handleDuplicateOffers = (activate_immediately: boolean) => {
    if (!current) return
    
    // Clear previous errors
    setUpdateError(null)
    setShowDuplicateConfirmModal(false)
    
    const lines = updateTitlesData
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0)
    
    if (lines.length === 0) {
      setUpdateError('Wprowadź ID ofert i tytuły do duplikacji')
      return
    }

    try {
      const items = lines.map((line, index) => {
        // Auto-detect separator - try comma first, then semicolon, tab, pipe
        let parts = line.split(',')
        if (parts.length < 2) {
          parts = line.split(';')
        }
        if (parts.length < 2) {
          parts = line.split('\t')
        }
        if (parts.length < 2) {
          parts = line.split('|')
        }
        
        if (parts.length < 2) {
          throw new Error(`Nieprawidłowy format linii ${index + 1}: "${line}". Użyj formatu: ID,Tytuł (separatory: , ; | tab)`)
        }
        
        const offer_id = parts[0].trim()
        const new_title = parts.slice(1).join(',').trim()
        
        // Validate offer ID format
        if (!/^\d+$/.test(offer_id)) {
          throw new Error(`Nieprawidłowe ID oferty w linii ${index + 1}: "${offer_id}". ID powinno składać się tylko z cyfr.`)
        }
        
        // Validate reasonable ID length (Allegro IDs are typically 11 digits)
        if (offer_id.length < 10 || offer_id.length > 15) {
          throw new Error(`Podejrzane ID oferty w linii ${index + 1}: "${offer_id}" (nietypowa długość). Sprawdź czy ID jest prawidłowe.`)
        }
        
        // Validate title is not empty
        if (!new_title) {
          throw new Error(`Pusty tytuł w linii ${index + 1}: "${line}"`)
        }
        
        // Validate title length (Allegro limit is 75 characters)
        if (new_title.length > 75) {
          throw new Error(`Tytuł zbyt długi w linii ${index + 1} (${new_title.length} znaków, max 75): "${new_title}"`)
        }
        
        return { offer_id, new_title }
      })

      // Check for duplicates
      const seenIds = new Set()
      const duplicates = []
      for (const item of items) {
        if (seenIds.has(item.offer_id)) {
          duplicates.push(item.offer_id)
        } else {
          seenIds.add(item.offer_id)
        }
      }
      
      if (duplicates.length > 0) {
        throw new Error(`Znaleziono duplikaty ID ofert: ${[...new Set(duplicates)].join(', ')}. Każda oferta może być duplikowana tylko raz.`)
      }

      duplicateOffersMutation.mutate(
        { 
          account_id: current.id, 
          items: items,
          activate_immediately
        },
        {
          onSuccess: (response) => {
            setDuplicateTaskId(response.data?.task_id)
          },
          onError: (error: any) => {
            if (isAccessDeniedError(error)) {
              setUpdateError('ACCESS_DENIED')
            } else {
              setUpdateError(error?.response?.data?.detail || error?.message || 'Wystąpił błąd podczas duplikacji ofert')
            }
          }
        }
      )
    } catch (error: any) {
      setUpdateError(error.message)
    }
  }

  // AI Optimization handlers
  const handleOptimizeWithAI = async () => {
    if (!current) {
      addToast('Proszę wybrać konto', 'error')
      return
    }

    // Clear previous errors and results
    setUpdateError(null)
    setAiOptimizationResults(null)
    setAcceptedOfferIds(new Set())
    setAiOptimizationTaskId(undefined)

    // Parse titles from textarea
    const lines = updateTitlesData
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0)

    if (lines.length === 0) {
      setUpdateError('Wprowadź ID ofert i tytuły do optymalizacji')
      return
    }

    const titles: TitleToOptimize[] = []
    const errors: string[] = []

    lines.forEach((line, index) => {
      // Try different separators
      let parts = line.split(',')
      if (parts.length < 2) {
        parts = line.split(';')
      }
      if (parts.length < 2) {
        parts = line.split('\t')
      }
      if (parts.length < 2) {
        parts = line.split('|')
      }

      if (parts.length < 2) {
        errors.push(`Nieprawidłowy format linii ${index + 1}: "${line}"`)
        return
      }

      const offer_id = parts[0].trim()
      const current_title = parts.slice(1).join(',').trim()

      if (!/^\d+$/.test(offer_id)) {
        errors.push(`Nieprawidłowe ID oferty w linii ${index + 1}: "${offer_id}"`)
        return
      }

      if (!current_title) {
        errors.push(`Pusty tytuł w linii ${index + 1}`)
        return
      }

      titles.push({ offer_id, current_title })
    })

    if (errors.length > 0) {
      setUpdateError(errors.join('; '))
      return
    }

    if (titles.length === 0) {
      setUpdateError('Nie znaleziono prawidłowych tytułów do optymalizacji')
      return
    }

    const maxTitles = includeOfferParameters ? 20 : 100
    const limitText = includeOfferParameters ? '20 tytułów (z parametrami)' : '100 tytułów'
    if (titles.length > maxTitles) {
      setUpdateError(`Maksymalnie ${limitText} na raz`)
      return
    }

    try {
      addToast('Rozpoczynam optymalizację tytułów z AI...', 'info')
      const result = await optimizeTitlesAIMutation.mutateAsync({
        account_id: current.id,
        titles,
        include_offer_parameters: includeOfferParameters,
      })

      // Set task ID to start polling
      setAiOptimizationTaskId(result.task_id)
    } catch (error: any) {
      if (isAccessDeniedError(error)) {
        setUpdateError('ACCESS_DENIED')
      } else {
        setUpdateError(
          error?.response?.data?.detail || error?.message || 'Wystąpił błąd podczas optymalizacji z AI'
        )
      }
      addToast('Błąd podczas optymalizacji z AI', 'error')
    }
  }

  const handleAcceptAllOptimizations = () => {
    if (!aiOptimizationResults) return
    const successfulOfferIds = new Set(
      aiOptimizationResults.filter(r => r.success).map(r => r.offer_id)
    )
    setAcceptedOfferIds(successfulOfferIds)
  }

  const handleRejectAllOptimizations = () => {
    setAcceptedOfferIds(new Set())
  }

  const handleAcceptSingleOptimization = (offerId: string) => {
    setAcceptedOfferIds(prev => new Set([...prev, offerId]))
  }

  const handleRejectSingleOptimization = (offerId: string) => {
    setAcceptedOfferIds(prev => {
      const newSet = new Set(prev)
      newSet.delete(offerId)
      return newSet
    })
  }

  const handleApplyAcceptedOptimizations = () => {
    if (!aiOptimizationResults) return

    // Build new titles data from accepted optimizations
    const resultsMap = new Map(aiOptimizationResults.map(r => [r.offer_id, r]))
    
    const newLines = updateTitlesData
      .split('\n')
      .map(line => {
        const parts = line.split(/[,;\t|]/)
        if (parts.length < 2) return line
        
        const offerId = parts[0].trim()
        
        if (acceptedOfferIds.has(offerId)) {
          const result = resultsMap.get(offerId)
          if (result && result.success) {
            return `${offerId},${result.optimized_title}`
          }
        }
        
        return line
      })

    setUpdateTitlesData(newLines.join('\n'))
    setAiOptimizationResults(null)
    setAcceptedOfferIds(new Set())
    // Clear from localStorage
    localStorage.removeItem('titles-ai-optimization-results')
    localStorage.removeItem('titles-ai-accepted-ids')
    addToast(`Zastosowano ${acceptedOfferIds.size} zoptymalizowanych tytułów`, 'success')
  }

  const handleCancelAIOptimization = () => {
    setAiOptimizationResults(null)
    setAcceptedOfferIds(new Set())
    // Clear from localStorage
    localStorage.removeItem('titles-ai-optimization-results')
    localStorage.removeItem('titles-ai-accepted-ids')
    addToast('Anulowano optymalizację AI', 'info')
  }

  const handleCopyPulledTitlesToUpdate = async () => {
    if (!typedPullTaskStatus?.result?.download_url) {
      addToast('Brak danych do skopiowania', 'error')
      return
    }

    try {
      // Download CSV data
      const response = await fetch(typedPullTaskStatus.result.download_url)
      const csvText = await response.text()
      
      // Parse CSV and convert to format needed for update section
      const lines = csvText.split('\n').filter(line => line.trim())
      const titleLines: string[] = []
            
      // Check if first line looks like a header (contains "ID" or "offer" etc.)
      const firstLine = lines[0] || ''
      const hasHeader = /^(id|offer|tytuł|title)/i.test(firstLine) || 
                       !(/^\d+,/.test(firstLine)) // If first line doesn't start with number,comma it might be header
      
      const dataLines = hasHeader ? lines.slice(1) : lines // Only skip if there's actually a header
      
      for (let i = 0; i < dataLines.length; i++) {
        const line = dataLines[i]
        
        // More robust CSV parsing - handle various CSV formats
        let offerId = ''
        let title = ''
        
        // Try to parse as CSV with proper handling of quotes and commas
        if (line.includes(',')) {
          // Handle quoted CSV format: "12345","Title with, comma"
          const quotedMatch = line.match(/^"([^"]+)","([^"]*)"/)
          if (quotedMatch) {
            offerId = quotedMatch[1].trim()
            title = quotedMatch[2].trim()
          } else {
            // Handle simple CSV format: 12345,Title without quotes
            const parts = line.split(',')
            if (parts.length >= 2) {
              offerId = parts[0].replace(/"/g, '').trim()
              title = parts.slice(1).join(',').replace(/"/g, '').trim()
            }
          }
        } else {
          // Handle tab-separated or other formats
          const parts = line.split(/[\t;]/)
          if (parts.length >= 2) {
            offerId = parts[0].replace(/"/g, '').trim()
            title = parts.slice(1).join(' ').replace(/"/g, '').trim()
          }
        }
        
        if (offerId && title) {
          titleLines.push(`${offerId},${title}`)
        }
      }
      
      if (titleLines.length > 0) {
        setUpdateTitlesData(titleLines.join('\n'))
        addToast(`Skopiowano ${titleLines.length} tytułów do sekcji aktualizacji`, 'success')
        
        // Clear any previous AI results and errors
        setAiOptimizationResults(null)
        setAcceptedOfferIds(new Set())
        setUpdateError(null)
      } else {
        addToast('Nie znaleziono danych do skopiowania w pliku CSV', 'error')
      }
    } catch (error) {
      console.error('Error copying pulled titles:', error)
      addToast('Błąd podczas kopiowania tytułów', 'error')
    }
  }

  const handlePullFileImport = (result: FileImportResult) => {
    if (result.offerIds && result.offerIds.length > 0) {
      setPullOfferIds(result.offerIds.join('\n'))
      setPullError(null)
    } else {
      setPullError('Nie znaleziono ID ofert w pliku')
    }
  }

  const handleUpdateFileImport = (result: FileImportResult) => {
    if (result.titlesData) {
      setUpdateTitlesData(result.titlesData)
      setUpdateError(null)
    } else if (result.offerIds && result.offerIds.length > 0) {
      // If only IDs are found, user needs to add titles manually
      setUpdateTitlesData(result.offerIds.map(id => `${id},`).join('\n'))
      setUpdateError(null)
    } else {
      setUpdateError('Nie znaleziono danych do aktualizacji tytułów')
    }
  }

  // Type the pullTaskStatus properly
  const typedPullTaskStatus = pullTaskStatus as PullTaskStatus | undefined

  // Check if we should show warning icon (no current account OR no accounts available)
  const shouldShowWarningIcon = !current || (!accountsLoading && Array.isArray(accounts) && accounts.length === 0)

  // Helper function to check if error is 403 (access denied)
  const isAccessDeniedError = (error: any) => {
    return error?.response?.status === 403
  }

  // Helper function to create access denied error message
  const createAccessDeniedMessage = (operation: string) => (
    <div className="mt-4 p-4 bg-red-50 rounded-lg border border-red-200">
      <div className="flex items-start space-x-3">
        <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <h3 className="text-red-800 font-medium">Brak dostępu do konta</h3>
          <p className="text-red-700 text-sm mt-1">
            Nie masz dostępu do wybranego konta lub konto nie zostało poprawnie skonfigurowane. 
            Aby {operation}, musisz najpierw dodać i skonfigurować konto.
          </p>
          <Link
            to="/accounts"
            className="inline-flex items-center mt-3 px-4 py-2 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 transition-colors"
          >
            Przejdź do kont Allegro
          </Link>
        </div>
      </div>
    </div>
  )


  // Account change modal handlers
  const handleKeepOfferIds = () => {
    setShowAccountChangeModal(false)
    // Keep the current offer IDs - user wants to check if they're valid for new account
  }

  const handleClearOfferIds = () => {
    setPullOfferIds('')
    localStorage.removeItem('titles-pull-offer-ids')
    setPullError(null)
    setShowAccountChangeModal(false)
  }

  const handleReplaceIdsWithDuplicates = () => {
    if (!duplicateTasksStatus || !duplicateTasksStatus.duplicatedOffers) return

    // Build new textarea content with new IDs
    const lines = updateTitlesData.split('\n').map(line => line.trim()).filter(line => line.length > 0)
    const newLines: string[] = []

    lines.forEach(line => {
      // Parse the line to get the old offer_id
      let parts = line.split(',')
      if (parts.length < 2) parts = line.split(';')
      if (parts.length < 2) parts = line.split('\t')
      if (parts.length < 2) parts = line.split('|')

      if (parts.length >= 2) {
        const oldId = parts[0].trim()
        const title = parts.slice(1).join(',').trim()

        // Find the corresponding new ID
        const mapping = duplicateTasksStatus.duplicatedOffers.find((m: any) => m.old_id === oldId)
        if (mapping) {
          newLines.push(`${mapping.new_id},${title}`)
        }
      }
    })

    setUpdateTitlesData(newLines.join('\n'))
    setShowDuplicateModal(false)
    addToast('ID zostały podmienione na nowe', 'success')
  }

  const handleCopyNewIds = () => {
    if (!duplicateTasksStatus || !duplicateTasksStatus.duplicatedOffers) return

    const newIds = duplicateTasksStatus.duplicatedOffers.map((m: any) => m.new_id).join('\n')
    navigator.clipboard.writeText(newIds)
    addToast('Skopiowano nowe ID do schowka', 'success')
  }


  // No account selected
  if (!current) {
    return (
      <div className="space-y-6 w-full flex flex-col">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-semibold">Tytuły</h1>
          <div className="flex items-center space-x-2">
            {shouldShowWarningIcon && <AlertTriangle className="w-4 h-4 text-amber-500" />}
            <span className="text-sm text-gray-600">Konto:</span>
            <AccountSelector />
          </div>
        </div>
        <div className="bg-white shadow rounded-lg p-8 text-center">
          <div className="text-gray-500 space-y-2">
            <div className="text-lg">Wybierz konto</div>
            <div className="text-sm">Aby zarządzać tytułami ofert, wybierz konto powyżej</div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 w-full flex flex-col">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-semibold">Tytuły</h1>
        <div className="flex items-center space-x-2">
          {shouldShowWarningIcon && <AlertTriangle className="w-4 h-4 text-amber-500" />}
          <span className="text-sm text-gray-600">Konto:</span>
          <AccountSelector />
        </div>
      </div>

      {/* Pull Titles Section */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Pobierz tytuły</h2>
        </div>
        
        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">
                ID ofert (jedno na linię):
              </label>
              <div className="flex gap-2">
                <OfferSelectorButton
                  accountId={current.id}
                  offerIds={pullOfferIds}
                  setOfferIds={setPullOfferIds}
                  setError={setPullError}
                />
                <FileImportButton
                  label="Importuj z pliku"
                  onImport={handlePullFileImport}
                  onError={setPullError}
                  config={{ extractOfferIds: true, validateOfferIds: true }}
                />
                <button
                  onClick={() => {
                    setPullOfferIds('')
                    localStorage.removeItem('titles-pull-offer-ids')
                  }}
                  className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                >
                  Wyczyść
                </button>
              </div>
            </div>
            <textarea
              className="w-full h-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="17640753898&#10;17640753899&#10;17640753900"
              value={pullOfferIds}
              onChange={(e) => {
                setPullOfferIds(e.target.value)
                if (pullError) setPullError(null)
              }}
            />
            <div className="mt-2 text-xs text-gray-500">
              💡 Obsługiwane formaty plików: .csv, .xlsx, .xls, .txt | Automatyczne wykrywanie separatorów i nagłówków
            </div>
          </div>
          
          <button
            onClick={handlePullTitles}
            disabled={pullTitlesMutation.isPending || !pullOfferIds.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {pullTitlesMutation.isPending ? 'Pobieram...' : 'Pobierz tytuły'}
          </button>
          
          {/* Pull Error Display */}
          {pullError && (
            pullError === 'ACCESS_DENIED' ? 
              createAccessDeniedMessage('pobierać tytuły ofert') :
              <div className="mt-4 p-3 bg-red-50 rounded-lg border border-red-200">
                <div className="flex items-start">
                  <div className="text-red-600 text-sm">
                    <span className="font-medium">Błąd:</span> {pullError}
                  </div>
                  <button
                    onClick={() => setPullError(null)}
                    className="ml-auto text-red-400 hover:text-red-600"
                  >
                    ✕
                  </button>
                </div>
              </div>
          )}
          
          {/* Pull Progress Display */}
          {pullTaskId && typedPullTaskStatus && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-blue-800">Status pobierania:</span>
                  <span className={`text-sm px-2 py-1 rounded ${
                    typedPullTaskStatus.status === 'SUCCESS' ? 'bg-green-100 text-green-800' :
                    typedPullTaskStatus.status === 'FAILURE' ? 'bg-red-100 text-red-800' :
                    typedPullTaskStatus.status === 'PROGRESS' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {typedPullTaskStatus.status || 'PENDING'}
                  </span>
                </div>
                
                {typedPullTaskStatus.result && (
                  <div className="text-sm text-blue-700">
                    {typedPullTaskStatus.status === 'SUCCESS' && typedPullTaskStatus.result.download_url && (
                      <div className="space-y-2">
                        <div>✅ Pobrano {typedPullTaskStatus.result.fetched_titles} tytułów z {typedPullTaskStatus.result.total_offers} ofert</div>
                        <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                          <button
                            onClick={() => window.open(typedPullTaskStatus.result!.download_url, '_blank')}
                            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors text-sm sm:text-base"
                          >
                            Pobierz plik CSV
                          </button>
                          <button
                            onClick={handleCopyPulledTitlesToUpdate}
                            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm sm:text-base"
                          >
                            <span className="hidden sm:inline">Skopiuj do kolejnej sekcji</span>
                            <span className="sm:hidden">Skopiuj do aktualizacji</span>
                          </button>
                        </div>
                      </div>
                    )}
                    
                    {typedPullTaskStatus.status === 'PROGRESS' && (
                      <div>
                        <div className="mb-2">{typedPullTaskStatus.result.status}</div>
                        {typedPullTaskStatus.result.progress !== undefined && (
                          <div className="w-full bg-blue-200 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full transition-all"
                              style={{ width: `${typedPullTaskStatus.result.progress}%` }}
                            />
                          </div>
                        )}
                      </div>
                    )}
                    
                    {typedPullTaskStatus.status === 'FAILURE' && (
                      <div className="text-red-600">
                        ❌ Błąd: {typedPullTaskStatus.result?.exc_message || typedPullTaskStatus.result?.error || 'Nieznany błąd podczas pobierania tytułów'}
                      </div>
                    )}
                  </div>
                )}
                
                <div className="flex justify-end">
                  <button
                    onClick={() => setPullTaskId(undefined)}
                    className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                  >
                    Zamknij
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Update Titles Section */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-xl font-semibold mb-4">Aktualizuj tytuły</h2>
        
        <div className="space-y-4">
          {/* AI Optimization Panel */}
          <AIOptimizationPanel
            onOptimize={handleOptimizeWithAI}
            isProcessing={optimizeTitlesAIMutation.isPending || !!aiOptimizationTaskId}
            disabled={!updateTitlesData.trim() || (aiStatus ? (!aiStatus.can_use_default && !aiStatus.has_config) : false)}
            aiStatus={aiStatus}
            includeOfferParameters={includeOfferParameters}
            onIncludeOfferParametersChange={setIncludeOfferParameters}
            titleCount={updateTitlesData.split('\n').filter(line => line.trim().length > 0).length}
          />

          {/* AI Optimization Progress */}
          {aiOptimizationTaskId && aiOptimizationTaskStatus && (
            <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-purple-800">Optymalizacja AI:</span>
                  <span className={`text-sm px-2 py-1 rounded ${
                    aiOptimizationTaskStatus.status === 'SUCCESS' ? 'bg-green-100 text-green-800' :
                    aiOptimizationTaskStatus.status === 'FAILURE' ? 'bg-red-100 text-red-800' :
                    aiOptimizationTaskStatus.status === 'PROGRESS' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {aiOptimizationTaskStatus.status || 'PENDING'}
                  </span>
                </div>
                
                {aiOptimizationTaskStatus.result && aiOptimizationTaskStatus.status === 'PROGRESS' && (
                  <div className="space-y-2">
                    <div className="text-sm text-purple-700">
                      {(aiOptimizationTaskStatus.result as any).status || 'Przetwarzanie...'}
                    </div>
                    
                    {/* Progress bar */}
                    {(aiOptimizationTaskStatus.result as any).progress !== undefined && (
                      <div className="w-full bg-purple-200 rounded-full h-2">
                        <div 
                          className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${(aiOptimizationTaskStatus.result as any).progress}%` }}
                        />
                      </div>
                    )}
                    
                    {/* Stats */}
                    {((aiOptimizationTaskStatus.result as any).processed !== undefined || 
                      (aiOptimizationTaskStatus.result as any).successful !== undefined) && (
                      <div className="flex justify-between text-xs text-purple-600">
                        {(aiOptimizationTaskStatus.result as any).processed !== undefined && (
                          <span>
                            Przetworzono: {(aiOptimizationTaskStatus.result as any).processed}/{(aiOptimizationTaskStatus.result as any).total}
                          </span>
                        )}
                        {(aiOptimizationTaskStatus.result as any).successful !== undefined && (
                          <span>
                            ✅ {(aiOptimizationTaskStatus.result as any).successful} | 
                            ❌ {(aiOptimizationTaskStatus.result as any).failed}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                )}
                
                {aiOptimizationTaskStatus.status === 'PENDING' && (
                  <div className="text-sm text-purple-700">Przygotowywanie optymalizacji...</div>
                )}
              </div>
            </div>
          )}

          {/* AI Optimization Results */}
          {aiOptimizationResults && aiOptimizationResults.length > 0 && (
            <div>
              <TitleComparisonView
                results={aiOptimizationResults}
                onAcceptAll={handleAcceptAllOptimizations}
                onRejectAll={handleRejectAllOptimizations}
                onAcceptSingle={handleAcceptSingleOptimization}
                onRejectSingle={handleRejectSingleOptimization}
                onCancel={handleCancelAIOptimization}
                acceptedOfferIds={acceptedOfferIds}
              />
              <div className="mt-4 flex justify-center sm:justify-end space-x-3">
                {acceptedOfferIds.size > 0 ? (
                  <button
                    onClick={handleApplyAcceptedOptimizations}
                    className="w-full sm:w-auto px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm sm:text-base"
                  >
                    <span className="hidden sm:inline">Zastosuj zaakceptowane tytuły ({acceptedOfferIds.size})</span>
                    <span className="sm:hidden">Zastosuj ({acceptedOfferIds.size})</span>
                  </button>
                ) : (
                  <button
                    onClick={handleCancelAIOptimization}
                    className="w-full sm:w-auto px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors text-sm sm:text-base"
                  >
                    <span className="hidden sm:inline">Zamknij bez zmian</span>
                    <span className="sm:hidden">Zamknij</span>
                  </button>
                )}
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ID ofert i tytuły:
            </label>
            <textarea
              className="w-full h-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="17640753898,Nowy tytuł oferty 1&#10;17640753899,Nowy tytuł oferty 2&#10;17640753900,Nowy tytuł oferty 3"
              value={updateTitlesData}
              onChange={(e) => {
                setUpdateTitlesData(e.target.value)
                if (updateError) setUpdateError(null)
                if (bulkEditTitlesMutation.isSuccess) bulkEditTitlesMutation.reset()
                if (updateTaskId) {
                  setUpdateTaskId(undefined)
                }
              }}
            />
            <div className="mt-2 text-xs text-gray-500">
              💡 Obsługiwane formaty: CSV/Excel z kolumnami ID,Tytuł lub ID|Tytuł | Automatyczne wykrywanie nagłówków i separatorów
            </div>
          </div>
          
          <div className="flex justify-between items-center">
            <div className="flex space-x-2">
              <FileImportButton
                label="Importuj ID i tytuły"
                onImport={handleUpdateFileImport}
                onError={setUpdateError}
                config={{ extractOfferIds: true, extractTitles: true, validateOfferIds: true }}
              />
              <button
                onClick={() => {
                  setUpdateTitlesData('')
                  localStorage.removeItem('titles-update-data')
                }}
                className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
              >
                Wyczyść
              </button>
            </div>
            
            <div className="flex gap-2 items-center">
              <button
                onClick={handleUpdateTitles}
                disabled={bulkEditTitlesMutation.isPending || !updateTitlesData.trim()}
                className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {bulkEditTitlesMutation.isPending ? 'Aktualizuję...' : 'Aktualizuj tytuły'}
              </button>
              
              <div className="relative group">
                <button
                  onClick={() => setShowDuplicateConfirmModal(true)}
                  disabled={duplicateOffersMutation.isPending || !updateTitlesData.trim()}
                  className="px-6 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                >
                  <Copy className="w-4 h-4" />
                  {duplicateOffersMutation.isPending ? 'Duplikuję...' : 'Duplikuj'}
                </button>
                <div className="absolute hidden group-hover:block z-50 bottom-full right-0 mb-2 w-80 p-3 bg-gray-900 text-white text-xs rounded shadow-lg">
                  <div className="flex items-start gap-2">
                    <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
                    <div>
                      <div className="font-semibold mb-1">Duplikacja ofert z nowymi tytułami</div>
                      <div>Tworzy kopie wybranych ofert z nowymi tytułami na tym samym koncie. Wszystkie parametry (opis, parametry, cena, dostawa) są kopiowane. Obrazy nie są duplikowane - używane są te same URL. Przydatne do testów A/B.</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Update Error Display */}
          {updateError && (
            updateError === 'ACCESS_DENIED' ? 
              createAccessDeniedMessage('aktualizować tytuły ofert') :
              <div className="mt-4 p-3 bg-red-50 rounded-lg border border-red-200">
                <div className="flex items-start">
                  <div className="text-red-600 text-sm">
                    <span className="font-medium">Błąd:</span> {updateError}
                  </div>
                  <button
                    onClick={() => setUpdateError(null)}
                    className="ml-auto text-red-400 hover:text-red-600"
                  >
                    ✕
                  </button>
                </div>
              </div>
          )}
          
          {/* Update Tasks Status Display */}
          {updateTasksStatus && updateTaskId && (
            <div className="mt-4 space-y-2">
              {/* Progress Summary */}
              {!updateTasksStatus.allCompleted && (
                <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="text-blue-800 text-sm">
                    <span className="font-medium">Aktualizacja w toku:</span> {updateTasksStatus.successCount} sukces, {updateTasksStatus.failureCount} błąd, {updateTasksStatus.pendingCount} w toku
                  </div>
                  <div className="w-full bg-blue-200 rounded-full h-2 mt-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all"
                      style={{ width: updateTasksStatus.total > 0 ? `${((updateTasksStatus.successCount + updateTasksStatus.failureCount) / updateTasksStatus.total) * 100}%` : '0%' }}
                    />
                  </div>
                </div>
              )}
              
              {/* Final Results */}
              {updateTasksStatus.allCompleted && (
                <div className={`p-3 rounded-lg border ${
                  updateTasksStatus.hasFailures ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200'
                }`}>
                  <div className="flex items-start justify-between">
                    <div className={`text-sm ${updateTasksStatus.hasFailures ? 'text-yellow-800' : 'text-green-600'}`}>
                      <span className="font-medium">
                        {updateTasksStatus.hasFailures ? 'Aktualizacja zakończona z błędami:' : 'Sukces:'}
                      </span> {updateTasksStatus.successCount} zaktualizowane, {updateTasksStatus.failureCount} błędów
                      
                      {updateTasksStatus.hasFailures && (
                        <div className="mt-2 space-y-1">
                          {updateTasksStatus.results
                            .filter((r: any) => r.status === 'FAILURE')
                            .map((result: any, index: number) => (
                              <div key={result.offer_id || index} className="text-xs">
                                • Oferta {result.offer_id}: {result.error}
                              </div>
                            ))
                          }
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => {
                        setUpdateTaskId(undefined)
                        bulkEditTitlesMutation.reset()
                      }}
                      className={`ml-auto ${updateTasksStatus.hasFailures ? 'text-yellow-400 hover:text-yellow-600' : 'text-green-400 hover:text-green-600'}`}
                    >
                      ✕
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* Duplicate Tasks Status Display */}
          {duplicateTasksStatus && duplicateTaskId && (
            <div className="mt-4 space-y-2">
              {/* Progress Summary */}
              {!duplicateTasksStatus.allCompleted && (
                <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                  <div className="text-purple-800 text-sm">
                    <span className="font-medium">Duplikacja w toku:</span> {duplicateTasksStatus.successCount} sukces, {duplicateTasksStatus.failureCount} błąd, {duplicateTasksStatus.pendingCount} w toku
                  </div>
                  <div className="w-full bg-purple-200 rounded-full h-2 mt-2">
                    <div 
                      className="bg-purple-600 h-2 rounded-full transition-all"
                      style={{ width: duplicateTasksStatus.total > 0 ? `${((duplicateTasksStatus.successCount + duplicateTasksStatus.failureCount) / duplicateTasksStatus.total) * 100}%` : '0%' }}
                    />
                  </div>
                </div>
              )}
              
              {/* Final Results */}
              {duplicateTasksStatus.allCompleted && (
                <div className={`p-3 rounded-lg border ${
                  duplicateTasksStatus.hasFailures ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200'
                }`}>
                  <div className="flex items-start justify-between">
                    <div className={`text-sm ${duplicateTasksStatus.hasFailures ? 'text-yellow-800' : 'text-green-600'}`}>
                      <span className="font-medium">
                        {duplicateTasksStatus.hasFailures ? 'Duplikacja zakończona z błędami:' : 'Sukces:'}
                      </span> {duplicateTasksStatus.successCount} zduplikowane, {duplicateTasksStatus.failureCount} błędów
                      
                      {duplicateTasksStatus.hasFailures && (
                        <div className="mt-2 space-y-1">
                          {duplicateTasksStatus.failedOffers.map((result: any, index: number) => (
                            <div key={result.offer_id || index} className="text-xs">
                              • Oferta {result.offer_id} ({result.title}): {result.error}
                            </div>
                          ))}
                        </div>
                      )}
                      
                      {duplicateTasksStatus.successCount > 0 && (
                        <div className="mt-3">
                          <button
                            onClick={() => setShowDuplicateModal(true)}
                            className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors text-sm"
                          >
                            Zobacz mapowanie ID ({duplicateTasksStatus.successCount} ofert)
                          </button>
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => {
                        setDuplicateTaskId(undefined)
                        duplicateOffersMutation.reset()
                      }}
                      className={`ml-auto ${duplicateTasksStatus.hasFailures ? 'text-yellow-400 hover:text-yellow-600' : 'text-green-400 hover:text-green-600'}`}
                    >
                      ✕
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>


      {/* Account Change Confirmation Modal */}
      {showAccountChangeModal && createPortal(
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50" onClick={() => setShowAccountChangeModal(false)}>
          <div className="bg-white rounded-lg shadow-lg w-full max-w-md max-h-[90vh] overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="p-6">
              <div className="flex items-center mb-4">
                <div className="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center mr-3">
                  <AlertTriangle className="w-6 h-6 text-amber-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Zmiana konta
                </h3>
              </div>
              
              <div className="mb-6">
                <p className="text-gray-700 mb-2">
                  Zmieniłeś konto, ale masz wybrane ID ofert z poprzedniego konta.
                </p>
                <p className="text-sm text-gray-500">
                  Oferty: <span className="font-mono font-medium">{pullOfferIds.split('\n').map(id => id.trim()).filter(id => id.length > 0 && /^\d+$/.test(id)).length} wybranych</span>
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={handleClearOfferIds}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                >
                  Wyczyść oferty
                </button>
                <button
                  onClick={handleKeepOfferIds}
                  className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-200 transition-colors"
                >
                  Zachowaj oferty
                </button>
              </div>
              
              <p className="text-xs text-gray-500 mt-3">
                💡 Jeśli zachowasz oferty, sprawdź czy należą do aktualnego konta przed pobraniem tytułów.
              </p>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* Duplicate Confirmation Modal */}
      {showDuplicateConfirmModal && createPortal(
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50" onClick={() => setShowDuplicateConfirmModal(false)}>
          <div className="bg-white rounded-lg shadow-lg w-full max-w-lg max-h-[90vh] overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="p-6 border-b">
              <div className="flex items-center">
                <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center mr-3">
                  <Copy className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Potwierdź duplikację ofert
                  </h3>
                </div>
              </div>
            </div>

            <div className="p-6">
              <p className="text-gray-700 mb-4">
                Zamierzasz zduplikować <span className="font-semibold">{updateTitlesData.split('\n').filter(line => line.trim().length > 0).length} {updateTitlesData.split('\n').filter(line => line.trim().length > 0).length === 1 ? 'ofertę' : 'ofert'}</span> z nowymi tytułami.
              </p>
              <p className="text-gray-600 text-sm mb-4">
                Wszystkie parametry (opis, parametry, cena, dostawa, zwroty, gwarancja) zostaną skopiowane. Obrazy będą używać tych samych URL.
              </p>
              <p className="text-gray-900 font-medium mb-2">
                Wybierz status nowych ofert:
              </p>
            </div>

            <div className="p-6 border-t bg-gray-50 flex flex-col sm:flex-row gap-3">
              <button
                onClick={() => handleDuplicateOffers(true)}
                className="flex-1 px-4 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors font-medium"
              >
                ✓ Utwórz jako aktywne
              </button>
              <button
                onClick={() => handleDuplicateOffers(false)}
                className="flex-1 px-4 py-3 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors font-medium"
              >
                Utwórz jako nieaktywne
              </button>
              <button
                onClick={() => setShowDuplicateConfirmModal(false)}
                className="px-4 py-3 bg-white text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                Anuluj
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* Duplicate ID Mapping Modal */}
      {showDuplicateModal && duplicateTasksStatus && duplicateTasksStatus.duplicatedOffers && createPortal(
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50" onClick={() => setShowDuplicateModal(false)}>
          <div className="bg-white rounded-lg shadow-lg w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center mr-3">
                    <Copy className="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      Mapowanie ID zduplikowanych ofert
                    </h3>
                    <p className="text-sm text-gray-600">
                      {duplicateTasksStatus.duplicatedOffers.length} {duplicateTasksStatus.duplicatedOffers.length === 1 ? 'oferta została zduplikowana' : 'ofert zostało zduplikowanych'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowDuplicateModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>
            
            <div className="p-6 overflow-y-auto flex-1">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        ID bazowe
                      </th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        →
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        ID nowe
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Tytuł
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {duplicateTasksStatus.duplicatedOffers.map((mapping: any) => (
                      <tr key={mapping.old_id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-mono text-gray-900">
                          {mapping.old_id}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-center text-purple-600">
                          →
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-mono text-purple-600 font-semibold">
                          {mapping.new_id}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600 max-w-md truncate">
                          {mapping.title}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            
            <div className="p-6 border-t bg-gray-50">
              <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-sm text-blue-800">
                  <span className="font-medium">Chcesz podmienić ID w polu tekstowym?</span><br />
                  Możesz podmienić ID bazowe na nowe ID, aby móc dalej pracować z nowymi ofertami.
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={handleReplaceIdsWithDuplicates}
                  className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors font-medium"
                >
                  Tak, podmień ID
                </button>
                <button
                  onClick={handleCopyNewIds}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Skopiuj nowe ID
                </button>
                <button
                  onClick={() => setShowDuplicateModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-200 transition-colors"
                >
                  Nie, zostaw
                </button>
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}

    </div>
  )
} 