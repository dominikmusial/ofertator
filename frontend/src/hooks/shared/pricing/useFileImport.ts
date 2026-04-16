import { useState } from 'react'
import { parseFile, ParsedData } from '../../../utils/fileParser'

export interface FileImportConfig {
  acceptedTypes?: string
  extractOfferIds?: boolean
  extractTitles?: boolean
  extractCustomData?: (data: ParsedData) => any
  validateData?: (data: any) => string | null
  validateOfferIds?: boolean
}

export interface FileImportResult {
  offerIds?: string[]
  titlesData?: string
  customData?: any
  rawData?: ParsedData
}

export interface FileImportState {
  isLoading: boolean
  error: string | null
  lastResult: FileImportResult | null
}

export function useFileImport(config: FileImportConfig = {}) {
  const [state, setState] = useState<FileImportState>({
    isLoading: false,
    error: null,
    lastResult: null
  })

  const {
    acceptedTypes = '.txt,.xlsx,.xls,.csv',
    extractOfferIds = true,
    extractTitles = false,
    extractCustomData,
    validateData,
    validateOfferIds = true
  } = config

  const clearError = () => {
    setState(prev => ({ ...prev, error: null }))
  }

  const clearResult = () => {
    setState(prev => ({ ...prev, lastResult: null }))
  }

  const importFile = async (): Promise<FileImportResult | null> => {
    return new Promise((resolve, reject) => {
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = acceptedTypes
      
      input.onchange = async (e) => {
        const file = (e.target as HTMLInputElement).files?.[0]
        if (!file) {
          resolve(null)
          return
        }

        setState(prev => ({ ...prev, isLoading: true, error: null }))

        try {
          // Parse the file
          const parsedData = await parseFile(file)
          
          // Extract data based on configuration
          const result: FileImportResult = {
            rawData: parsedData
          }

          // Extract offer IDs if requested
          if (extractOfferIds) {
            result.offerIds = extractOfferIdsFromData(parsedData)
            
            // Validate offer IDs if requested
            if (validateOfferIds && result.offerIds) {
              const validationError = validateOfferIdsArray(result.offerIds)
              if (validationError) {
                throw new Error(validationError)
              }
            }
          }

          // Extract titles format if requested
          if (extractTitles) {
            result.titlesData = extractTitlesFromData(parsedData)
          }

          // Extract custom data if function provided
          if (extractCustomData) {
            result.customData = extractCustomData(parsedData)
          }

          // Validate the result if validator provided
          if (validateData) {
            const validationError = validateData(result)
            if (validationError) {
              throw new Error(validationError)
            }
          }

          setState(prev => ({ 
            ...prev, 
            isLoading: false, 
            lastResult: result 
          }))
          
          resolve(result)
        } catch (error: any) {
          const errorMessage = error.message || 'Błąd podczas przetwarzania pliku'
          setState(prev => ({ 
            ...prev, 
            isLoading: false, 
            error: errorMessage 
          }))
          reject(error)
        }
      }
      
      input.click()
    })
  }

  return {
    ...state,
    importFile,
    clearError,
    clearResult
  }
}

// Helper functions for data extraction
function extractOfferIdsFromData(parsedData: ParsedData): string[] {
  const { data, headers } = parsedData
  
  if (!data || data.length === 0) return []

  // If headers exist, try to find ID column
  if (headers && headers.length > 0) {
    const idColumnIndex = headers.findIndex(header => {
      const headerStr = header?.toString().trim().toLowerCase() || ''
      return ['id', 'offer_id', 'offer', 'oferta'].includes(headerStr)
    })
    
    if (idColumnIndex !== -1) {
      return data
        .map(row => row[idColumnIndex]?.toString().trim())
        .filter(id => id && id.length > 0)
    }
  }

  // Fallback: assume first column contains IDs
  return data
    .map(row => row[0]?.toString().trim())
    .filter(id => id && id.length > 0)
}

function extractTitlesFromData(parsedData: ParsedData): string {
  const { data, headers } = parsedData
  
  if (!data || data.length === 0) return ''

  // If headers exist, try to find ID and Title columns
  if (headers && headers.length > 0) {
    const idColumnIndex = headers.findIndex(header => {
      const headerStr = header?.toString().trim().toLowerCase() || ''
      return ['id', 'offer_id', 'offer', 'oferta'].includes(headerStr)
    })
    
    const titleColumnIndex = headers.findIndex(header => {
      const headerStr = header?.toString().trim() || ''
      return /^(tytuł|tytuły|title|titles|nazwa|name)$/i.test(headerStr)
    })
    
    if (idColumnIndex !== -1 && titleColumnIndex !== -1) {
      // Perfect match - use the identified columns
      return data
        .filter(row => row[idColumnIndex] && row[titleColumnIndex])
        .map(row => {
          const id = row[idColumnIndex]?.toString().trim() || ''
          const title = row[titleColumnIndex]?.toString().trim() || ''
          return `${id},${title}`
        })
        .join('\n')
    } else if (headers.length >= 2) {
      // Headers detected but regex didn't match perfectly - assume first column is ID, second is Title
      // This handles cases with encoding issues like "Tytu�y" instead of "Tytuły"
      return data
        .filter(row => row[0] && row[1])
        .map(row => {
          const id = row[0]?.toString().trim() || ''
          const title = row[1]?.toString().trim() || ''
          return `${id},${title}`
        })
        .join('\n')
    } else if (idColumnIndex !== -1) {
      // Only ID column found - format for pulling titles
      return data
        .filter(row => row[idColumnIndex])
        .map(row => `${row[idColumnIndex]?.toString().trim()},`)
        .join('\n')
    }
  }

  // Fallback: auto-detect based on column count
  if (data.length > 0) {
    const firstRow = data[0]
    
    if (firstRow.length === 1) {
      // Single column - assume IDs for pulling
      return data
        .map(row => `${row[0]?.toString().trim()},`)
        .join('\n')
    } else if (firstRow.length >= 2) {
      // Multiple columns - assume first is ID, second is Title
      return data
        .filter(row => row[0] && row[1])
        .map(row => {
          const id = row[0]?.toString().trim() || ''
          const title = row[1]?.toString().trim() || ''
          return `${id},${title}`
        })
        .join('\n')
    }
  }

  return ''
}

// Validation function for offer IDs
function validateOfferIdsArray(offerIds: string[]): string | null {
  if (!offerIds || offerIds.length === 0) {
    return 'Nie znaleziono ID ofert w pliku'
  }

  // Validate offer IDs format
  const invalidIds = offerIds.filter(id => !/^\d+$/.test(id))
  if (invalidIds.length > 0) {
    return `Nieprawidłowe ID ofert: ${invalidIds.slice(0, 5).join(', ')}${invalidIds.length > 5 ? ` i ${invalidIds.length - 5} więcej` : ''}. ID oferty powinno składać się tylko z cyfr.`
  }

  // Validate reasonable ID length (Allegro IDs are typically 11 digits)
  const suspiciousIds = offerIds.filter(id => id.length < 10 || id.length > 15)
  if (suspiciousIds.length > 0) {
    return `Podejrzane ID ofert (nietypowa długość): ${suspiciousIds.slice(0, 5).join(', ')}${suspiciousIds.length > 5 ? ` i ${suspiciousIds.length - 5} więcej` : ''}. Sprawdź czy ID są prawidłowe.`
  }

  return null
} 