import * as XLSX from 'xlsx'

export interface ParsedData {
  data: string[][]
  headers?: string[]
  format: 'csv' | 'excel' | 'text'
  separator?: string
}

export interface ParseOptions {
  expectedColumns?: number
  autoDetectHeaders?: boolean
  autoDetectSeparator?: boolean
}

/**
 * Detects if the first row contains headers by analyzing the data
 * Simple logic: if the first cell contains only numbers, it's data, not headers
 */
function detectHeaders(data: string[][]): boolean {
  if (data.length < 1) return false
  
  const firstRow = data[0]
  if (firstRow.length === 0) return false
  
  const firstCell = firstRow[0]
  const firstCellStr = firstCell !== null && firstCell !== undefined ? firstCell.toString().trim() : ''
  
  // If first cell is empty, assume no headers
  if (firstCellStr === '') return false
  
  // If first cell contains only numbers, it's data, not headers
  if (/^\d+$/.test(firstCellStr)) return false
  
  // Otherwise, assume it's headers
  return true
}

/**
 * Detects the separator used in CSV data
 */
function detectSeparator(text: string): string {
  const lines = text.split('\n').filter(line => line.trim())
  if (lines.length === 0) return ','
  
  const separators = [',', ';', '\t', '|']
  const scores: Record<string, number> = {}
  
  // Test each separator
  for (const sep of separators) {
    let score = 0
    let consistentColumns = true
    let columnCount = -1
    
    // Check consistency across first few lines
    for (let i = 0; i < Math.min(5, lines.length); i++) {
      const columns = lines[i].split(sep).length
      if (columnCount === -1) {
        columnCount = columns
      } else if (columns !== columnCount) {
        consistentColumns = false
        break
      }
      
      // Bonus for having more than 1 column
      if (columns > 1) score += 10
    }
    
    if (consistentColumns && columnCount > 1) {
      scores[sep] = score
    }
  }
  
  // Return the separator with highest score, default to comma
  let bestSeparator = ','
  let bestScore = -1
  
  for (const [sep, score] of Object.entries(scores)) {
    if (score > bestScore) {
      bestScore = score
      bestSeparator = sep
    }
  }
  
  return bestSeparator
}

/**
 * Parses text content as CSV with automatic separator detection
 */
function parseCSV(text: string, options: ParseOptions = {}): ParsedData {
  const { autoDetectSeparator = true, autoDetectHeaders = true } = options
  
  const lines = text.split('\n').filter(line => line.trim())
  if (lines.length === 0) {
    return { data: [], format: 'csv' }
  }
  
  const separator = autoDetectSeparator ? detectSeparator(text) : ','
  
  const data = lines.map(line => {
    // Simple CSV parsing - handles quoted fields
    const result: string[] = []
    let current = ''
    let inQuotes = false
    
    for (let i = 0; i < line.length; i++) {
      const char = line[i]
      
      if (char === '"' && !inQuotes) {
        inQuotes = true
      } else if (char === '"' && inQuotes) {
        inQuotes = false
      } else if (char === separator && !inQuotes) {
        result.push(current.trim())
        current = ''
      } else {
        current += char
      }
    }
    
    result.push(current.trim())
    return result
  })
  
  let headers: string[] | undefined
  let processedData = data
  
  if (autoDetectHeaders && detectHeaders(data)) {
    headers = data[0]
    processedData = data.slice(1)
  }
  
  return {
    data: processedData,
    headers,
    format: 'csv',
    separator
  }
}

/**
 * Parses Excel file content
 */
function parseExcel(file: File): Promise<ParsedData> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    
    reader.onload = (e) => {
      try {
        const data = e.target?.result as ArrayBuffer
        const workbook = XLSX.read(data, { type: 'array' })
        
        // Use first sheet
        const firstSheetName = workbook.SheetNames[0]
        const worksheet = workbook.Sheets[firstSheetName]
        
        // Convert to array of arrays
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { 
          header: 1, 
          defval: '',
          blankrows: false
        }) as any[][]
        
        // Convert all cells to strings and filter out empty rows
        const filteredData = jsonData
          .map(row => 
            row.map(cell => cell !== null && cell !== undefined ? cell.toString() : '')
          )
          .filter(row => 
            row.some(cell => cell && cell.trim() !== '')
          )
        
        let headers: string[] | undefined
        let processedData = filteredData
        
        if (detectHeaders(filteredData)) {
          headers = filteredData[0]
          processedData = filteredData.slice(1)
        }
        
        resolve({
          data: processedData,
          headers,
          format: 'excel'
        })
      } catch (error) {
        console.error('Excel parsing error:', error)
        reject(new Error(`Błąd podczas przetwarzania pliku Excel: ${error instanceof Error ? error.message : 'Nieznany błąd'}`))
      }
    }
    
    reader.onerror = () => reject(new Error('Błąd podczas odczytu pliku'))
    reader.readAsArrayBuffer(file)
  })
}

/**
 * Main function to parse various file formats
 */
export async function parseFile(file: File, options: ParseOptions = {}): Promise<ParsedData> {
  const fileName = file.name.toLowerCase()
  
  try {
    if (fileName.endsWith('.xlsx') || fileName.endsWith('.xls')) {
      return await parseExcel(file)
    } else if (fileName.endsWith('.csv') || fileName.endsWith('.txt')) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        
        reader.onload = (e) => {
          const text = e.target?.result as string
          try {
            const result = parseCSV(text, options)
            resolve(result)
          } catch (error) {
            // Try to detect encoding issues and provide helpful error message
            const hasEncodingIssues = text.includes('�') || text.includes('â€')
            if (hasEncodingIssues) {
              reject(new Error(`Błąd kodowania pliku CSV. Spróbuj zapisać plik w formacie UTF-8 lub użyj pliku Excel (.xlsx). Detale: ${error}`))
            } else {
              reject(new Error(`Błąd podczas przetwarzania pliku CSV: ${error}`))
            }
          }
        }
        
        reader.onerror = () => reject(new Error('Błąd podczas odczytu pliku'))
        reader.readAsText(file, 'utf-8')
      })
    } else {
      throw new Error('Nieobsługiwany format pliku. Obsługiwane formaty: .csv, .txt, .xlsx, .xls')
    }
  } catch (error) {
    throw error
  }
}

/**
 * Converts parsed data to the format expected by the titles functionality
 */
export function convertToTitlesFormat(parsedData: ParsedData): {
  pullIds: string
  updateTitles: string
} {
  const { data, headers } = parsedData
  
  // If we have headers, try to detect the column structure
  if (headers) {
    // Check if we have ID and Title columns
    const idColumnIndex = headers.findIndex(header => {
      const headerStr = header !== null && header !== undefined ? header.toString().trim() : ''
      return /^(id|offer_id|offer)$/i.test(headerStr)
    })
    const titleColumnIndex = headers.findIndex(header => {
      const headerStr = header !== null && header !== undefined ? header.toString().trim() : ''
      return /^(tytuł|tytuły|title|titles|nazwa|name)$/i.test(headerStr)
    })
    
              if (idColumnIndex !== -1 && titleColumnIndex !== -1) {
      // Format for updating titles (ID,Title)
      const updateTitles = data
        .filter(row => row[idColumnIndex] && row[titleColumnIndex])
        .map(row => {
          const id = row[idColumnIndex]?.toString().trim() || ''
          const title = row[titleColumnIndex]?.toString().trim() || ''
          return `${id},${title}`
        })
        .join('\n')
      
      return {
        pullIds: '',
        updateTitles
      }
    } else if (headers.length >= 2) {
      // Headers detected but regex didn't match perfectly - assume first column is ID, second is Title
      // This handles cases with encoding issues like "Tytu�y" instead of "Tytuły"
      const updateTitles = data
        .filter(row => row[0] && row[1])
        .map(row => {
          const id = row[0]?.toString().trim() || ''
          const title = row[1]?.toString().trim() || ''
          return `${id},${title}`
        })
        .join('\n')
      
      return {
        pullIds: '',
        updateTitles
      }
    } else if (idColumnIndex !== -1) {
      // Only ID column found - format for pulling titles
      const pullIds = data
        .filter(row => row[idColumnIndex])
        .map(row => row[idColumnIndex]?.toString().trim() || '')
        .join('\n')
      
      return {
        pullIds,
        updateTitles: ''
      }
    }
  }
  
  // Fallback: auto-detect based on column count and header presence
  if (data.length > 0) {
    const firstRow = data[0]
    
    if (firstRow.length === 1) {
      // Single column - assume IDs for pulling
      const pullIds = data
        .filter(row => row[0])
        .map(row => row[0]?.toString().trim() || '')
        .join('\n')
      
      return {
        pullIds,
        updateTitles: ''
      }
    } else if (firstRow.length >= 2) {
      // Multiple columns - assume first is ID, second is Title
      const updateTitles = data
        .filter(row => row[0] && row[1])
        .map(row => {
          const id = row[0]?.toString().trim() || ''
          const title = row[1]?.toString().trim() || ''
          return `${id},${title}`
        })
        .join('\n')
      
      return {
        pullIds: '',
        updateTitles
      }
    }
  }
  
  return {
    pullIds: '',
    updateTitles: ''
  }
} 