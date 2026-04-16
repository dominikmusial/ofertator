import { useState, useEffect } from 'react'
import { useTemplates } from '../../../hooks/shared/templates'
import { useCreateTemplate } from '../../../hooks/shared/templates'
import { useUpdateTemplate } from '../../../hooks/shared/templates'
import { useDeleteTemplate } from '../../../hooks/shared/templates'
import { useCopyTemplate } from '../../../hooks/shared/templates'
import { useDuplicateTemplate } from '../../../hooks/shared/templates'
import { useBulkUpdateOffers, useBulkRestoreOffers } from '../../../hooks/shared/offers/bulk'
import { useTaskStatus } from '../../../hooks/shared/tasks'
import { useMultipleTaskStatus, TaskStatus } from '../../../hooks/shared/tasks'
import { useSharedAccounts, AccountWithOwnership } from '../../../hooks/marketplaces/allegro/accounts'
import { useAccountImages } from '../../../hooks/shared/accounts'
import { useAccountStore } from '../../../store/accountStore'
import { useToastStore } from '../../../store/toastStore'
import { useAuthStore } from '../../../store/authStore'
import { useAIConfigStatus } from '../../../hooks/shared/ai'
import MarketplaceAccountSelector from '../../../components/ui/MarketplaceAccountSelector'
import TemplateSection from '../../../components/offers/TemplateSection'
import { Link } from 'react-router-dom'
import { AlertTriangle, Settings } from 'lucide-react'
import api from '../../../lib/api'
import Modal from '../../../components/ui/Modal'
import { Input, Label } from '../../../components/ui/input'
import { Button } from '../../../components/ui/button'
import FileImportButton from '../../../components/ui/FileImportButton'
import OfferSelectorButton from '../../../components/ui/OfferSelectorButton'
import { FileImportResult } from '../../../hooks/shared/pricing'
import { DndContext, closestCenter, DragEndEvent } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy, arrayMove } from '@dnd-kit/sortable'

interface Section {
  id: string
  type: 'TXT' | 'IMG' | 'IMG,TXT' | 'TXT,IMG' | 'IMG,IMG'
  values: Record<string, any>
}

export default function OfferEditor() {
  const { current } = useAccountStore()
  const { user } = useAuthStore()
  const { accounts } = useSharedAccounts()
  const { data: templates } = useTemplates(current?.id)
  const { data: accountImages } = useAccountImages(current?.id || 0)
  const { data: aiStatus } = useAIConfigStatus()
  const createTemplateMutation = useCreateTemplate()
  const updateTemplateMutation = useUpdateTemplate()
  const deleteTemplateMutation = useDeleteTemplate()
  const copyTemplateMutation = useCopyTemplate()
  const duplicateTemplateMutation = useDuplicateTemplate()
  const bulkUpdateMutation = useBulkUpdateOffers()
  const bulkRestoreMutation = useBulkRestoreOffers()
  
  // Task monitoring
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null)
  const taskStatus = useTaskStatus(currentTaskId || undefined, !!currentTaskId)
  const [completedTaskResult, setCompletedTaskResult] = useState<any>(null)
  const { addToast } = useToastStore()
  
  // Restore task tracking
  const [restoreTaskIds, setRestoreTaskIds] = useState<{task_id: string, offer_id: string}[]>([])
  const restoreTasksStatus = useMultipleTaskStatus(restoreTaskIds)

  // Template state
  const [sections, setSections] = useState<Section[]>([])
  const [prompt, setPrompt] = useState('')
  const [selectedTemplate, setSelectedTemplate] = useState('')
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | null>(null)
  const [templateName, setTemplateName] = useState('')
  const [selectedTargetAccountId, setSelectedTargetAccountId] = useState('')
  const [sectionsCollapsed, setSectionsCollapsed] = useState(false)
  const [isUpdatingTemplate, setIsUpdatingTemplate] = useState(false)
  const [showMyTemplatesOnly, setShowMyTemplatesOnly] = useState(false)
  
  // Name conflict modal state
  const [isNameConflictModalOpen, setIsNameConflictModalOpen] = useState(false)
  const [newTemplateName, setNewTemplateName] = useState('')
  const [conflictData, setConflictData] = useState<{original_name: string, suggested_name: string, template_id: number, target_account_id: number} | null>(null)
  
  // Duplicate modal state
  const [isDuplicateModalOpen, setIsDuplicateModalOpen] = useState(false)
  const [duplicateTemplateName, setDuplicateTemplateName] = useState('')

  // Offer processing state
  const [offerIds, setOfferIds] = useState('')
  const [imageProcessingMode, setImageProcessingMode] = useState('Oryginalny')
  const [frameScale, setFrameScale] = useState(2235)
  const [frameScaleEntry, setFrameScaleEntry] = useState('2235')
  const [fileImportError, setFileImportError] = useState<string | null>(null)
  
  // Processing options
  const [generatePdf, setGeneratePdf] = useState(false)
  const [autoFillImages, setAutoFillImages] = useState(false)
  const [saveOriginalImages, setSaveOriginalImages] = useState(false)
  const [saveProcessedImages, setSaveProcessedImages] = useState(false)
  const [saveImagesOnly, setSaveImagesOnly] = useState(false)
  // Save location and custom path are handled automatically by cloud storage

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false)
  const [sectionValidationErrors, setSectionValidationErrors] = useState<{[key: string]: string[]}>({})

  // Trigger validation whenever sections change
  useEffect(() => {
    console.log('Sections changed:', sections)
    const validationResult = validateSections()
    console.log('Validation result:', validationResult)
    setSectionValidationErrors(validationResult.sectionErrors)
  }, [sections])

  // Helper function to validate sections before processing
  const validateSections = () => {
    const errors: {[key: string]: string[]} = {}
    const generalErrors: string[] = []
    
    // Check if there are any sections at all
    if (sections.length === 0) {
      generalErrors.push('Brak sekcji w szablonie - dodaj co najmniej jedną sekcję')
      return { sectionErrors: errors, generalErrors }
    }
    
    sections.forEach((section, index) => {
      const sectionNumber = index + 1
      const sectionErrors: string[] = []
      
      switch (section.type) {
        case 'TXT':
          if (!section.values.text || section.values.text.trim() === '') {
            sectionErrors.push('Brak tekstu')
          }
          break
          
        case 'IMG':
          console.log(`IMG section validation - image value: "${section.values.image}"`)
          if (!section.values.image || section.values.image === '') {
            console.log('IMG section validation - FAILED: no image selected')
            sectionErrors.push('Nie wybrano obrazu')
          } else {
            console.log('IMG section validation - PASSED: image selected')
          }
          break
          
        case 'IMG,TXT':
          if (!section.values.image || section.values.image === '') {
            sectionErrors.push('Nie wybrano obrazu')
          }
          if (!section.values.text || section.values.text.trim() === '') {
            sectionErrors.push('Brak tekstu')
          }
          break
          
        case 'TXT,IMG':
          if (!section.values.text || section.values.text.trim() === '') {
            sectionErrors.push('Brak tekstu')
          }
          if (!section.values.image || section.values.image === '') {
            sectionErrors.push('Nie wybrano obrazu')
          }
          break
          
        case 'IMG,IMG':
          if (!section.values.image1 || section.values.image1 === '') {
            sectionErrors.push('Nie wybrano pierwszego obrazu')
          }
          if (!section.values.image2 || section.values.image2 === '') {
            sectionErrors.push('Nie wybrano drugiego obrazu')
          }
          break
      }
      
      if (sectionErrors.length > 0) {
        errors[section.id] = sectionErrors
      }
    })
    
    return { sectionErrors: errors, generalErrors }
  }

  // Helper function to convert technical errors to user-friendly messages
  const getUserFriendlyError = (error: string) => {
    // If error is already in Polish (user-friendly), return as is
    if (error.includes('Przekroczono limit') || 
        error.includes('Brak uprawnień') || 
        error.includes('nie istnieje') ||
        error.includes('Nieprawidłowe') ||
        error.includes('Zbyt wiele zapytań') ||
        error.includes('maksymalnie') ||
        error.includes('Błąd API') ||
        error.includes('Błąd kopiowania') ||
        error.includes('Rozmiar obrazu') ||
        error.includes('format obrazu') ||
        error.includes('Błąd walidacji')) {
      return error
    }
    
    // Legacy error code translations for backward compatibility
    if (error.includes('404') || error.includes('Not Found')) {
      return 'Oferta nie istnieje lub została usunięta'
    }
    if (error.includes('403') || error.includes('Forbidden')) {
      return 'Brak uprawnień do edycji tej oferty'
    }
    if (error.includes('401') || error.includes('Unauthorized')) {
      return 'Problem z autoryzacją - sprawdź połączenie z kontem'
    }
    if (error.includes('400') || error.includes('Bad Request')) {
      return 'Nieprawidłowe dane oferty'
    }
    if (error.includes('422') || error.includes('Unprocessable Entity')) {
      return 'Dane oferty są nieprawidłowe lub niekompletne'
    }
    if (error.includes('429') || error.includes('Too Many Requests')) {
      return 'Zbyt wiele zapytań - spróbuj ponownie za chwilę'
    }
    if (error.includes('500') || error.includes('Internal Server Error')) {
      return 'Błąd serwera Allegro - spróbuj ponownie później'
    }
    if (error.includes('timeout') || error.includes('Timeout')) {
      return 'Przekroczono limit czasu - spróbuj ponownie'
    }
    // Return original error if no pattern matches
    return error
  }

  // Section management
  const addSection = (type: Section['type']) => {
    if (sections.length >= 100) {
      addToast('Maksymalna liczba sekcji to 100', 'error')
      return
    }

    const newSection: Section = {
      id: `section-${Date.now()}-${Math.random()}`,
      type,
      values: getDefaultValues(type)
    }

    setSections(prev => [...prev, newSection])
  }

  const removeSection = (id: string) => {
    setSections(prev => prev.filter(section => section.id !== id))
    
    // Clear validation errors for this section when it's removed
    setSectionValidationErrors(prev => {
      const newErrors = { ...prev }
      delete newErrors[id]
      return newErrors
    })
  }

  const updateSection = (id: string, values: Record<string, any>) => {
    setSections(prev => prev.map(section => 
      section.id === id ? { ...section, values } : section
    ))
  }

  const clearSections = () => {
    setSections([])
    setPrompt('')
    setSelectedTemplate('Wybierz szablon')
    setSelectedTemplateId(null)
    setTemplateName('')
    setIsUpdatingTemplate(false)
    setSectionValidationErrors({})
  }

  const getDefaultValues = (type: Section['type']) => {
    switch (type) {
      case 'TXT':
        return { text: 'Sekcja opisująca produkt' }
      case 'IMG':
        return { image: '', frame: 'No frame' }
      case 'IMG,TXT':
        return { image: '', frame: 'No frame', text: 'Sekcja opisująca produkt' }
      case 'TXT,IMG':
        return { text: 'Sekcja opisująca produkt', image: '', frame: 'No frame' }
      case 'IMG,IMG':
        return { 
          image1: '', frame1: 'No frame',
          image2: '', frame2: 'No frame'
        }
      default:
        return {}
    }
  }

  // Drag and drop handling
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event

    if (over && active.id !== over.id) {
      setSections((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id)
        const newIndex = items.findIndex((item) => item.id === over.id)

        const newSections = arrayMove(items, oldIndex, newIndex)
        
        // Preserve validation errors for the reordered sections
        // Since validation errors are keyed by section.id, they will automatically follow
        
        return newSections
      })
    }
  }

  // Template management
  const loadTemplate = (templateName: string) => {
    if (templateName === 'Wybierz szablon') {
      setSelectedTemplateId(null)
      setIsUpdatingTemplate(false)
      setTemplateName('')
      return
    }
    
    const template = templates?.find(t => t.name === templateName)
    if (!template) {
      addToast('Nie znaleziono szablonu', 'error')
      return
    }

    try {
      const content = template.content
      setPrompt(content.prompt || '')
      setSections(content.sections || [])
      setSelectedTemplateId(template.id)
      setTemplateName(template.name)
      setIsUpdatingTemplate(true)
      addToast(`Szablon '${templateName}' został załadowany`, 'success')
    } catch (error) {
      addToast('Błąd podczas ładowania szablonu', 'error')
    }
  }

  const saveTemplate = async () => {
    if (!templateName.trim() || templateName === 'Nazwa szablonu') {
      addToast('Proszę podać nazwę szablonu', 'error')
      return
    }

    if (!current) {
      addToast('Proszę wybrać konto', 'error')
      return
    }

    const templateData = {
      name: templateName.trim(),
      content: {
        prompt: prompt.trim(),
        sections
      },
      account_id: current.id
    }

    try {
      await createTemplateMutation.mutateAsync(templateData)
      addToast(`Szablon '${templateName}' został zapisany dla konta ${current.nazwa_konta}`, 'success')
      setTemplateName('')
      setIsUpdatingTemplate(false)
      setSelectedTemplateId(null)
    } catch (error) {
      addToast('Błąd podczas zapisywania szablonu', 'error')
    }
  }

  const updateTemplate = async () => {
    if (!selectedTemplateId || !templateName.trim()) {
      addToast('Nie można zaktualizować szablonu', 'error')
      return
    }

    if (!current) {
      addToast('Proszę wybrać konto', 'error')
      return
    }

    const templateData = {
      id: selectedTemplateId,
      name: templateName.trim(),
      content: {
        prompt: prompt.trim(),
        sections
      }
    }

    try {
      await updateTemplateMutation.mutateAsync(templateData)
      addToast(`Szablon '${templateName}' został zaktualizowany`, 'success')
    } catch (error) {
      addToast('Błąd podczas aktualizacji szablonu', 'error')
    }
  }

  const clearTemplate = () => {
    setSelectedTemplate('Wybierz szablon')
    setSelectedTemplateId(null)
    setTemplateName('')
    setIsUpdatingTemplate(false)
    clearSections()
  }

  // Helper function to check if current user is the owner of selected template
  const isTemplateOwner = () => {
    if (!selectedTemplateId || !templates || !user) return false
    const template = templates.find(t => t.id === selectedTemplateId)
    return template?.owner_id === user.id
  }

  // Filter templates based on showMyTemplatesOnly flag
  const filteredTemplates = templates?.filter(template => {
    if (!showMyTemplatesOnly || !user) return true
    return template.owner_id === user.id
  })

  const deleteTemplate = async () => {
    if (selectedTemplate === 'Wybierz szablon' || !selectedTemplate) {
      addToast('Proszę wybrać szablon do usunięcia', 'error')
      return
    }

    const template = templates?.find(t => t.name === selectedTemplate)
    if (!template) return

    if (!confirm(`Czy na pewno chcesz usunąć szablon "${selectedTemplate}" z konta "${current?.nazwa_konta}"?`)) return

    try {
      await deleteTemplateMutation.mutateAsync(template.id)
      addToast(`Szablon '${selectedTemplate}' został usunięty z konta ${current?.nazwa_konta}`, 'success')
      setSelectedTemplate('Wybierz szablon')
      clearSections()
    } catch (error) {
      addToast('Błąd podczas usuwania szablonu', 'error')
    }
  }

  const duplicateTemplate = () => {
    if (selectedTemplate === 'Wybierz szablon' || !selectedTemplate) {
      addToast('Proszę wybrać szablon do duplikowania', 'error')
      return
    }

    const template = templates?.find(t => t.name === selectedTemplate)
    if (!template) {
      addToast('Nie znaleziono szablonu', 'error')
      return
    }

    setDuplicateTemplateName(`${template.name} (kopia)`)
    setIsDuplicateModalOpen(true)
  }

  const confirmDuplicateTemplate = async () => {
    if (!duplicateTemplateName.trim()) {
      addToast('Proszę podać nazwę szablonu', 'error')
      return
    }

    const template = templates?.find(t => t.name === selectedTemplate)
    if (!template) {
      addToast('Nie znaleziono szablonu źródłowego', 'error')
      return
    }

    try {
      await duplicateTemplateMutation.mutateAsync({
        template_id: template.id,
        new_name: duplicateTemplateName.trim()
      })
      addToast(`Szablon został skopiowany jako '${duplicateTemplateName}'`, 'success')
      setIsDuplicateModalOpen(false)
      setDuplicateTemplateName('')
    } catch (error) {
      addToast('Błąd podczas duplikowania szablonu', 'error')
    }
  }

  const copyTemplate = async () => {
    if (!selectedTemplate || !selectedTargetAccountId) {
      addToast('Proszę wybrać szablon i konto docelowe', 'error')
      return
    }

    const sourceTemplate = templates?.find(t => t.name === selectedTemplate)
    if (!sourceTemplate) {
      addToast('Nie znaleziono szablonu źródłowego', 'error')
      return
    }

    const targetAccount = (accounts as AccountWithOwnership[])?.find(acc => acc.id.toString() === selectedTargetAccountId)
    if (!targetAccount) {
      addToast('Nie znaleziono konta docelowego', 'error')
      return
    }

    try {
      await copyTemplateMutation.mutateAsync({
        template_id: sourceTemplate.id,
        target_account_id: parseInt(selectedTargetAccountId)
      })
      addToast(`Szablon "${selectedTemplate}" został skopiowany do konta "${targetAccount.nazwa_konta}"`, 'success')
      setSelectedTargetAccountId('')
    } catch (error: any) {
      if (error.response?.status === 409) {
        // Name conflict - open modal for user to enter new name
        const conflictData = error.response.data.detail
        setConflictData({
          original_name: conflictData.original_name,
          suggested_name: conflictData.suggested_name,
          template_id: sourceTemplate.id,
          target_account_id: parseInt(selectedTargetAccountId)
        })
        setNewTemplateName(conflictData.suggested_name)
        setIsNameConflictModalOpen(true)
      } else {
        addToast(error.response?.data?.detail || 'Błąd podczas kopiowania szablonu', 'error')
      }
    }
  }

  // Handle name conflict modal submission
  const handleNameConflictSubmit = async () => {
    if (!conflictData || !newTemplateName.trim()) {
      addToast('Proszę podać nazwę szablonu', 'error')
      return
    }

    const targetAccount = (accounts as AccountWithOwnership[])?.find(acc => acc.id === conflictData.target_account_id)
    if (!targetAccount) {
      addToast('Nie znaleziono konta docelowego', 'error')
      return
    }

    try {
      // Use the new copy-with-name endpoint
      await api.post('/allegro/templates/copy-with-name', {
        template_id: conflictData.template_id,
        target_account_id: conflictData.target_account_id
      }, {
        params: { new_name: newTemplateName.trim() }
      })
      addToast(`Szablon "${newTemplateName}" został skopiowany do konta "${targetAccount.nazwa_konta}"`, 'success')
      setSelectedTargetAccountId('')
      setIsNameConflictModalOpen(false)
      setConflictData(null)
      setNewTemplateName('')
    } catch (copyError: any) {
      addToast(copyError.response?.data?.detail || 'Błąd podczas kopiowania szablonu z nową nazwą', 'error')
    }
  }

  // Handle name conflict modal cancel
  const handleNameConflictCancel = () => {
    setIsNameConflictModalOpen(false)
    setConflictData(null)
    setNewTemplateName('')
  }

  // File handling
  const importOfferIds = () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.txt,.csv'
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (file) {
        const reader = new FileReader()
        reader.onload = (e) => {
          const content = e.target?.result as string
          setOfferIds(content.replace(/[,;]/g, '\n').replace(/\r/g, ''))
        }
        reader.readAsText(file)
      }
    }
    input.click()
  }

  const clearOfferIds = () => {
    setOfferIds('')
    setFileImportError(null)
  }

  const handleFileImport = (result: FileImportResult) => {
    if (result.offerIds && result.offerIds.length > 0) {
      setOfferIds(result.offerIds.join('\n'))
      setFileImportError(null)
    } else {
      setFileImportError('Nie znaleziono ID ofert w pliku')
    }
  }

  // Browse functions removed - save location is handled automatically by cloud storage

  // Frame scale synchronization
  const updateFrameScaleFromSlider = (value: number) => {
    setFrameScale(value)
    setFrameScaleEntry(Math.round(value).toString())
  }

  const updateFrameScaleFromEntry = (value: string) => {
    const numValue = parseInt(value) || 2235
    const clampedValue = Math.max(1792, Math.min(2560, numValue))
    setFrameScale(clampedValue)
    setFrameScaleEntry(clampedValue.toString())
  }

  // Save images options logic
  const handleSaveImagesOnlyChange = (checked: boolean) => {
    setSaveImagesOnly(checked)
    if (checked) {
      // When enabling "only save images", ensure at least original images are saved
      // but allow processed images to remain checked for process-only mode
      if (!saveOriginalImages && !saveProcessedImages) {
        setSaveOriginalImages(true)
      }
      setGeneratePdf(false)
    }
    // Don't auto-enable PDF when unchecking - let user decide
  }

  // Generate JSON structure from sections - DEPRECATED
  // This function is kept for backward compatibility but the backend now processes
  // the raw section format directly to preserve frame information
  const generateJsonStructure = () => {
    return sections.map(section => {
      const items: any[] = []
      
      switch (section.type) {
        case 'TXT':
          if (section.values.text) {
            items.push({
              type: 'TEXT',
              content: section.values.text
            })
          }
          break
          
        case 'IMG':
          if (section.values.image) {
            items.push({
              type: 'IMAGE',
              url: section.values.image,
              frame_url: section.values.frame || 'No frame'
            })
          }
          break
          
        case 'IMG,TXT':
          if (section.values.image) {
            items.push({
              type: 'IMAGE',
              url: section.values.image,
              frame_url: section.values.frame || 'No frame'
            })
          }
          if (section.values.text) {
            items.push({
              type: 'TEXT',
              content: section.values.text
            })
          }
          break
          
        case 'TXT,IMG':
          if (section.values.text) {
            items.push({
              type: 'TEXT',
              content: section.values.text
            })
          }
          if (section.values.image) {
            items.push({
              type: 'IMAGE',
              url: section.values.image,
              frame_url: section.values.frame || 'No frame'
            })
          }
          break
          
        case 'IMG,IMG':
          if (section.values.image1) {
            items.push({
              type: 'IMAGE',
              url: section.values.image1,
              frame_url: section.values.frame1 || 'No frame'
            })
          }
          if (section.values.image2) {
            items.push({
              type: 'IMAGE',
              url: section.values.image2,
              frame_url: section.values.frame2 || 'No frame'
            })
          }
          break
      }
      
      return { items }
    })
  }

  // Main processing functions
  const updateOffers = async () => {
    console.log('updateOffers called')
    if (!current) {
      addToast('Proszę wybrać konto', 'error')
      return
    }

    const offerIdList = offerIds.split('\n').map(id => id.trim()).filter(id => id)
    if (offerIdList.length === 0) {
      addToast('Proszę wprowadzić ID ofert', 'error')
      return
    }

    // Validate sections before processing
    console.log('About to validate sections...')
    const validationResult = validateSections()
    console.log('Validation result in updateOffers:', validationResult)
    if (validationResult.generalErrors.length > 0 || Object.keys(validationResult.sectionErrors).length > 0) {
      // Set validation errors for display in UI
      console.log('Validation failed, setting errors:', validationResult.sectionErrors)
      setSectionValidationErrors(validationResult.sectionErrors)
      
      // Show general errors as toast if any
      if (validationResult.generalErrors.length > 0) {
        validationResult.generalErrors.forEach(error => {
          addToast(error, 'error')
        })
      }
      console.log('Validation failed, returning early')
      return
    }
    
    console.log('Validation passed, proceeding with processing...')
    // Clear validation errors if validation passes
    setSectionValidationErrors({})

    // Note: Images are automatically saved to cloud storage (MinIO) when save options are enabled

    setIsProcessing(true)
    
    // Clear previous results
    setRestoreTaskIds([])
    setCompletedTaskResult(null)
    
    try {
      const requestData = {
        account_id: current.id,
        offer_ids: offerIdList,
        template: {
          prompt: prompt.trim(),
          sections: sections  // Send raw sections format to preserve frame information
        },
        options: {
          mode: imageProcessingMode,
          frame_scale: frameScale,
          generate_pdf: generatePdf,
          auto_fill_images: autoFillImages,
          save_original_images: saveOriginalImages,
          save_processed_images: saveProcessedImages,
          save_images_only: saveImagesOnly,
          save_location: 'cloud-storage', // Images saved to MinIO cloud storage
          custom_path: ''
        }
      }

      const task = await bulkUpdateMutation.mutateAsync(requestData)
      setCurrentTaskId(task.task_id)
      addToast(`Rozpoczęto przetwarzanie ${offerIdList.length} ofert`, 'success')
      
      // Task monitoring will handle progress updates and completion
      
    } catch (error) {
      addToast('Błąd podczas przetwarzania ofert', 'error')
      setIsProcessing(false)
    }
  }

  const restoreOffers = async () => {
    if (!current) {
      addToast('Proszę wybrać konto', 'error')
      return
    }

    const offerIdList = offerIds.split('\n').map(id => id.trim()).filter(id => id)
    if (offerIdList.length === 0) {
      addToast('Proszę wprowadzić ID ofert', 'error')
      return
    }

    if (!confirm(`Czy na pewno chcesz przywrócić ${offerIdList.length} ofert do poprzedniego stanu?`)) {
      return
    }

    setIsProcessing(true)
    
    // Clear previous results
    setRestoreTaskIds([])
    setCompletedTaskResult(null)
    
    try {
      const tasks = await bulkRestoreMutation.mutateAsync({
        account_id: current.id,
        offer_ids: offerIdList
      })
      
      // Store task IDs for monitoring
      setRestoreTaskIds(tasks)
      addToast(`Rozpoczęto przywracanie ${tasks.length} ofert`, 'success')
      
    } catch (error) {
      addToast('Błąd podczas przywracania ofert', 'error')
      setIsProcessing(false)
    }
  }

  // Clear template selection when account changes
  useEffect(() => {
    clearTemplate()
  }, [current?.nazwa_konta])

  // Handle task status changes
  useEffect(() => {
    if (taskStatus.data) {
      const { status, result, meta } = taskStatus.data
      
      if (status === 'SUCCESS') {
        setIsProcessing(false)
        // Store the completed task result before clearing currentTaskId
        setCompletedTaskResult(taskStatus.data)
        setCurrentTaskId(null)
        
        // Show simple completion toast - detailed results are shown in the results section
        addToast('Przetwarzanie zakończone - sprawdź wyniki poniżej', 'info')
      } else if (status === 'FAILURE') {
        setIsProcessing(false)
        // Store the failed task result before clearing currentTaskId
        setCompletedTaskResult(taskStatus.data)
        setCurrentTaskId(null)
        addToast('Przetwarzanie zakończone błędem - sprawdź szczegóły poniżej', 'error')
      } else if (status === 'PROGRESS') {
        // Task is still running, keep processing state
        if (!isProcessing) {
          setIsProcessing(true)
        }
      }
    }
  }, [taskStatus.data, isProcessing, addToast, saveImagesOnly])

  // Handle restore task status changes
  useEffect(() => {
    if (restoreTasksStatus.data && restoreTaskIds.length > 0) {
      const tasksData = restoreTasksStatus.data as TaskStatus[]
      const allTasksComplete = tasksData.every((task: TaskStatus) => 
        task.status === 'SUCCESS' || task.status === 'FAILURE'
      )
      
      if (allTasksComplete) {
        setIsProcessing(false)
        
        const summary = getRestoreSummary()
        
        if (summary.successful > 0) {
          addToast(`Pomyślnie przywrócono ${summary.successful} ${summary.successful === 1 ? 'ofertę' : 'ofert'}`, 'success')
        }
        
        if (summary.failed > 0) {
          addToast(`Nie udało się przywrócić ${summary.failed} ${summary.failed === 1 ? 'oferty' : 'ofert'}`, 'error')
        }
      }
    }
  }, [restoreTasksStatus.data, restoreTaskIds, addToast])

  // Helper function to calculate restore summary
  const getRestoreSummary = () => {
    if (!restoreTasksStatus.data || !Array.isArray(restoreTasksStatus.data)) {
      return { successful: 0, failed: 0, pending: 0, total: 0 }
    }
    
    let successful = 0
    let failed = 0
    let pending = 0
    let total = 0
    
    const tasksData = restoreTasksStatus.data as TaskStatus[]
    tasksData.forEach((task: TaskStatus) => {
      if (task.status === 'SUCCESS' && task.result) {
        // For restore tasks, each task handles one offer
        if (task.result.status === 'SUCCESS') {
          successful += 1
        } else {
          failed += 1
        }
        total += 1
      } else if (task.status === 'FAILURE') {
        // If entire task failed, count as one failure
        failed += 1
        total += 1
      } else if (task.status === 'PENDING' || task.status === 'PROGRESS') {
        // For pending tasks, we don't know the result yet
        pending += 1
      }
    })
    
    return { successful, failed, pending, total }
  }

  // No account selected
  if (!current) {
    return (
      <div className="space-y-6 w-full flex flex-col">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-semibold">Edytor Ofert</h1>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Wybierz konto:</span>
            <MarketplaceAccountSelector marketplaceType="allegro" />
          </div>
        </div>
        <div className="bg-white shadow rounded-lg p-8 text-center">
          <div className="text-gray-500 space-y-2">
            <div className="text-lg">Wybierz konto</div>
            <div className="text-sm">Aby edytować oferty, wybierz konto powyżej</div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 w-full flex flex-col max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Edytor Ofert</h1>
          <p className="text-gray-600 mt-1">
            Edytuj oferty dla konta: <span className="font-medium text-blue-600">{current.nazwa_konta}</span>
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">Konto:</span>
          <MarketplaceAccountSelector marketplaceType="allegro" />
        </div>
      </div>

      {/* AI Configuration Warning */}
      {aiStatus && !aiStatus.can_use_default && !aiStatus.has_config && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-amber-800 font-medium">Brak dostępu do AI</h3>
              <p className="text-amber-700 text-sm mt-1">
                Aby korzystać z automatycznego generowania treści AI, musisz skonfigurować własny klucz API.
                Bez konfiguracji AI, szablon będzie przetwarzany tylko z istniejącymi treściami.
              </p>
              <Link
                to="/profile/ai-config"
                className="inline-flex items-center mt-3 px-3 py-1.5 bg-amber-600 text-white text-sm rounded-md hover:bg-amber-700 transition-colors"
              >
                <Settings className="h-4 w-4 mr-1.5" />
                Skonfiguruj AI
              </Link>
            </div>
          </div>
        </div>
      )}

      {aiStatus && !aiStatus.can_use_default && aiStatus.has_config && !aiStatus.is_active && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-yellow-800 font-medium">Konfiguracja AI nieaktywna</h3>
              <p className="text-yellow-700 text-sm mt-1">
                Twoja konfiguracja AI została zdezaktywowana. Sprawdź ustawienia i klucz API.
              </p>
              <Link
                to="/profile/ai-config"
                className="inline-flex items-center mt-3 px-3 py-1.5 bg-yellow-600 text-white text-sm rounded-md hover:bg-yellow-700 transition-colors"
              >
                <Settings className="h-4 w-4 mr-1.5" />
                Sprawdź konfigurację
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Input Data */}
      <div className="bg-white rounded-lg shadow border">
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Dane wejściowe</h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  ID ofert (jedno na linię):
                </label>
                <span className="text-sm text-gray-500">
                  {offerIds.split('\n').filter(id => id.trim()).length} ofert
                </span>
              </div>
              <textarea
                value={offerIds}
                onChange={(e) => {
                  setOfferIds(e.target.value)
                  if (fileImportError) setFileImportError(null)
                }}
                className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                placeholder="12345678901&#10;12345678902&#10;12345678903"
              />
              <div className="flex justify-between items-center mt-2">
                <p className="text-xs text-gray-500">
                  💡 Obsługiwane formaty plików: .csv, .xlsx, .xls, .txt | Automatyczne wykrywanie separatorów i nagłówków
                </p>
                <div className="flex space-x-2">
                  <OfferSelectorButton
                    accountId={current.id}
                    offerIds={offerIds}
                    setOfferIds={setOfferIds}
                    setError={setFileImportError}
                    className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors flex items-center gap-2"
                  />
                  <FileImportButton
                    label="Importuj z pliku"
                    onImport={handleFileImport}
                    onError={setFileImportError}
                    config={{ extractOfferIds: true, validateOfferIds: true }}
                    className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
                  />
                  <button
                    onClick={clearOfferIds}
                    className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
                  >
                    Wyczyść
                  </button>
                </div>
              </div>
              
              {/* File Import Error Display */}
              {fileImportError && (
                <div className="mt-2 p-3 bg-red-50 rounded-lg border border-red-200">
                  <div className="flex items-start">
                    <div className="text-red-600 text-sm">
                      <span className="font-medium">Błąd:</span> {fileImportError}
                    </div>
                    <button
                      onClick={() => setFileImportError(null)}
                      className="ml-auto text-red-400 hover:text-red-600"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Dostępne obrazy:
              </label>
              <div className="border border-gray-300 rounded-lg p-3 h-32 overflow-y-auto bg-gray-50">
                <div className="text-sm text-gray-500">
                    {/* Offer images */}
                    <div className="font-medium text-gray-700 mb-1">Obrazy z oferty:</div>
                    {Array.from({ length: 16 }, (_, i) => (
                      <div key={i}>Aukcja:{i + 1}</div>
                    ))}
                  
                  {/* Account uploaded images */}
                  {accountImages && accountImages.length > 0 && (
                    <div className="mt-2 border-t pt-2">
                      <div className="font-medium text-gray-700 mb-1">Uploaded Images:</div>
                      {accountImages.map((image) => (
                        <div key={image.id} className="flex items-center justify-between">
                          <span>{image.original_filename}</span>
                          <span className="text-xs text-gray-400">
                            {image.is_logo && '(Logo)'} {image.is_filler && '(Filler)'}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {(!accountImages || accountImages.length === 0) && (
                    <div className="mt-2 border-t pt-2 text-gray-400">
                      <div>Brak uploaded images dla tego konta</div>
                      <div className="text-xs">Dodaj obrazy w sekcji "Dodawanie grafik"</div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Processing Options */}
      <div className="bg-white rounded-lg shadow border">
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Opcje przetwarzania</h3>
          
          {/* Mode Selection */}
          <div className="mb-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sposób wpasowania zdjęć w ramki:
                </label>
                <select 
                  value={imageProcessingMode}
                  onChange={(e) => setImageProcessingMode(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                >
                  <option value="Oryginalny">Oryginalny</option>
                  <option value="Przytnij do kwadratu">Przytnij do kwadratu</option>
                  <option value="Efekt rozmycia">Efekt rozmycia</option>
                  <option value="Usunięcie tła + Efekt rozmycia">Usunięcie tła + Efekt rozmycia</option>
                  <option value="Usunięcie tła + Przytnij do kwadratu">Usunięcie tła + Przytnij do kwadratu</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Rozmiar zawartości w ramce:
                </label>
                <div className="flex items-center space-x-2">
                  <input
                    type="range"
                    min="1792"
                    max="2560"
                    value={frameScale}
                    onChange={(e) => updateFrameScaleFromSlider(parseInt(e.target.value))}
                    className="flex-1"
                  />
                  <input
                    type="number"
                    value={frameScaleEntry}
                    onChange={(e) => setFrameScaleEntry(e.target.value)}
                    onBlur={(e) => updateFrameScaleFromEntry(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && updateFrameScaleFromEntry((e.target as HTMLInputElement).value)}
                    className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
                  />
                  <span className="text-sm text-gray-500">px</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">(polecane: 2235px)</p>
              </div>
            </div>
          </div>

          {/* Processing Checkboxes */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h4 className="text-sm font-medium text-gray-700">Opcje generowania:</h4>
              <div className="space-y-3">
                <label className="flex items-center">
                  <input 
                    type="checkbox" 
                    checked={generatePdf}
                    onChange={(e) => setGeneratePdf(e.target.checked)}
                    disabled={saveImagesOnly}
                    className="mr-2" 
                  />
                  <span className="text-sm">Wygeneruj i dołącz kartę produktową</span>
                </label>
                <label className="flex items-center">
                  <input 
                    type="checkbox" 
                    checked={autoFillImages}
                    onChange={(e) => setAutoFillImages(e.target.checked)}
                    disabled={saveImagesOnly}
                    className="mr-2" 
                  />
                  <span className="text-sm">Uzupełnij brakujące zdjęcia</span>
                </label>
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="text-sm font-medium text-gray-700">Opcje zapisu:</h4>
              <div className="space-y-3">
                <label className="flex items-center">
                  <input 
                    type="checkbox" 
                    checked={saveOriginalImages}
                    onChange={(e) => setSaveOriginalImages(e.target.checked)}
                    className="mr-2" 
                  />
                  <span className="text-sm">Zapisz oryginalne obrazy</span>
                </label>
                <label className="flex items-center">
                  <input 
                    type="checkbox" 
                    checked={saveProcessedImages}
                    onChange={(e) => setSaveProcessedImages(e.target.checked)}
                    className="mr-2" 
                  />
                  <span className="text-sm">Zapisz przetworzone obrazy</span>
                </label>
                <label className="flex items-center">
                  <input 
                    type="checkbox" 
                    checked={saveImagesOnly}
                    onChange={(e) => handleSaveImagesOnlyChange(e.target.checked)}
                    disabled={!saveOriginalImages && !saveProcessedImages}
                    className="mr-2" 
                  />
                  <span className="text-sm">Tylko zapisz obrazy</span>
                </label>
              </div>
              
              {/* Save Location Info */}
              {(saveOriginalImages || saveProcessedImages) && (
                <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <div className="flex items-start space-x-2">
                    <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                      <h4 className="text-sm font-medium text-blue-800">Automatyczne zapisywanie obrazów</h4>
                      <p className="text-sm text-blue-700 mt-1">
                        Obrazy będą automatycznie zapisane w chmurze i dostępne w sekcji "Zapisane zdjęcia". 
                        Możesz je pobrać jako pliki ZIP po zakończeniu przetwarzania.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Sections */}
      <div className="bg-white rounded-lg shadow border">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setSectionsCollapsed(!sectionsCollapsed)}
                className="flex items-center space-x-2 text-gray-700 hover:text-gray-900"
              >
                <span className="text-sm font-medium">
                  {sectionsCollapsed ? 'Rozwiń' : 'Zwiń'}
                </span>
                <svg
                  className={`w-4 h-4 transform transition-transform ${sectionsCollapsed ? 'rotate-0' : 'rotate-90'}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>

            {/* Template Controls */}
            <div className="flex items-center space-x-4">
              {/* Vsprint employee filter */}
              {user?.role === 'vsprint_employee' || user?.role === 'admin' ? (
                <div className="flex items-center space-x-2">
                  <label className="flex items-center text-sm">
                    <input
                      type="checkbox"
                      checked={showMyTemplatesOnly}
                      onChange={(e) => setShowMyTemplatesOnly(e.target.checked)}
                      className="mr-1"
                    />
                    Tylko moje szablony
                  </label>
                </div>
              ) : null}
              
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">Szablon:</span>
                <select
                  value={selectedTemplate}
                  onChange={(e) => setSelectedTemplate(e.target.value)}
                  className="px-3 py-1 border border-gray-300 rounded text-sm w-48"
                >
                  <option value="Wybierz szablon">Wybierz szablon</option>
                  {filteredTemplates?.map(template => (
                    <option key={template.id} value={template.name}>
                      {template.name} {template.owner_id !== user?.id ? '(udostępniony)' : ''}
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => loadTemplate(selectedTemplate)}
                  disabled={!selectedTemplate || selectedTemplate === 'Wybierz szablon'}
                  className={`px-3 py-1 text-sm rounded ${
                    !selectedTemplate || selectedTemplate === 'Wybierz szablon'
                      ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  Wczytaj
                </button>
                <button
                  onClick={duplicateTemplate}
                  disabled={!selectedTemplate || selectedTemplate === 'Wybierz szablon'}
                  className={`px-3 py-1 text-sm rounded ${
                    !selectedTemplate || selectedTemplate === 'Wybierz szablon'
                      ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                      : 'bg-green-600 text-white hover:bg-green-700'
                  }`}
                >
                  Duplikuj
                </button>
                {isTemplateOwner() && (
                  <button
                    onClick={deleteTemplate}
                    className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                  >
                    Usuń
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Second row - Save, Update and Copy controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
                placeholder="Nazwa szablonu"
                className="px-3 py-1 border border-gray-300 rounded text-sm w-48"
              />
              {isUpdatingTemplate && isTemplateOwner() ? (
                <button
                  onClick={updateTemplate}
                  disabled={updateTemplateMutation.isPending}
                  className="px-3 py-1 text-sm bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50"
                >
                  {updateTemplateMutation.isPending ? 'Aktualizowanie...' : 'Aktualizuj'}
                </button>
              ) : (
                <button
                  onClick={saveTemplate}
                  disabled={createTemplateMutation.isPending}
                  className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                >
                  {createTemplateMutation.isPending ? 'Zapisywanie...' : 'Zapisz'}
                </button>
              )}
              {isUpdatingTemplate && (
                <button
                  onClick={clearTemplate}
                  className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
                >
                  Wyczyść
                </button>
              )}
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">Kopiuj do:</span>
              <select
                value={selectedTargetAccountId}
                onChange={(e) => setSelectedTargetAccountId(e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded text-sm w-48"
              >
                <option value="">Wybierz konto docelowe</option>
                {(accounts as AccountWithOwnership[])?.filter(account => account.id.toString() !== current?.id.toString()).map((account) => (
                  <option key={account.id} value={account.id.toString()}>
                    {account.nazwa_konta}
                  </option>
                ))}
              </select>
              <button
                onClick={copyTemplate}
                disabled={!selectedTargetAccountId || !selectedTemplate || selectedTemplate === 'Wybierz szablon' || copyTemplateMutation.isPending}
                className="px-3 py-1 text-sm bg-orange-600 text-white rounded hover:bg-orange-700 disabled:opacity-50"
              >
                {copyTemplateMutation.isPending ? 'Kopiowanie...' : 'Kopiuj'}
              </button>
            </div>
          </div>

          {/* Prompt Field */}
          {!sectionsCollapsed && (
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Podpowiedź:
              </label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                placeholder="Ogólne informacje dla AI (opcjonalne)"
              />
            </div>
          )}

          {/* Template Buttons */}
          {!sectionsCollapsed && (
            <div className="mt-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Dodaj sekcję:</span>
                <div className="flex space-x-2">
                  <button
                    onClick={clearSections}
                    className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                  >
                    Wyczyść sekcje
                  </button>
                  <button
                    onClick={() => {
                      addSection('TXT')
                      addSection('IMG,TXT')
                      addSection('TXT,IMG')
                      addSection('IMG,IMG')
                    }}
                    disabled={sections.length > 12}
                    className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                  >
                    Dodaj przykładowe sekcje
                  </button>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                  <button
                    onClick={() => addSection('TXT')}
                    disabled={sections.length >= 100}
                    className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50"
                  >
                    TXT
                  </button>
                  <button
                    onClick={() => addSection('IMG,TXT')}
                    disabled={sections.length >= 100}
                    className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50"
                  >
                  IMG, TXT
                </button>
                <button
                  onClick={() => addSection('TXT,IMG')}
                  disabled={sections.length >= 100}
                  className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50"
                >
                  TXT, IMG
                </button>
                <button
                  onClick={() => addSection('IMG,IMG')}
                  disabled={sections.length >= 100}
                  className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50"
                >
                  IMG, IMG
                </button>
                <button
                  onClick={() => addSection('IMG')}
                  disabled={sections.length >= 100}
                  className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50"
                >
                  IMG
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Sections Container */}
        {!sectionsCollapsed && (
          <div className="p-6">
            {sections.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <div className="text-lg">Brak sekcji</div>
                <div className="text-sm">Dodaj sekcję używając przycisków powyżej</div>
              </div>
            ) : (
              <DndContext 
                collisionDetection={closestCenter}
                onDragEnd={handleDragEnd}
              >
                <SortableContext 
                  items={sections.map(section => section.id)}
                  strategy={verticalListSortingStrategy}
                >
                  <div className="space-y-4">
                    {sections.map((section, index) => (
                      <TemplateSection
                        key={section.id}
                        section={section}
                        index={index}
                        accountId={current?.id}
                        onUpdate={(values) => updateSection(section.id, values)}
                        onRemove={() => removeSection(section.id)}
                        validationErrors={sectionValidationErrors[section.id] || []}
                      />
                    ))}
                  </div>
                </SortableContext>
              </DndContext>
            )}
          </div>
        )}
      </div>

      {/* Progress Indicator */}
      {isProcessing && taskStatus.data && taskStatus.data.status === 'PROGRESS' && (
        <div className="bg-white rounded-lg shadow border p-6">
          <h3 className="text-lg font-semibold mb-4">Postęp przetwarzania</h3>
          
          {/* Progress Bar */}
          <div className="mb-4">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>{taskStatus.data.meta?.status || 'Przetwarzanie...'}</span>
              <span>{taskStatus.data.meta?.progress || 0}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${taskStatus.data.meta?.progress || 0}%` }}
              ></div>
            </div>
          </div>
          
          {/* Statistics */}
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-gray-900">
                {taskStatus.data.meta?.total_offers || 0}
              </div>
              <div className="text-sm text-gray-600">Wszystkie</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">
                {taskStatus.data.meta?.successful || 0}
              </div>
              <div className="text-sm text-gray-600">Pomyślne</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-600">
                {taskStatus.data.meta?.failed || 0}
              </div>
              <div className="text-sm text-gray-600">Błędy</div>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Update Results */}
      {completedTaskResult && (completedTaskResult.status === 'SUCCESS' || completedTaskResult.status === 'FAILURE') && (
        <div className="bg-white rounded-lg shadow border p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">
              {completedTaskResult.status === 'SUCCESS' ? 'Wyniki aktualizacji ofert' : 'Błąd aktualizacji ofert'}
            </h3>
            <button
              onClick={() => setCompletedTaskResult(null)}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              title="Zamknij wyniki"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          {completedTaskResult.status === 'SUCCESS' && (
            <>
              {/* Summary Statistics */}
              <div className="grid grid-cols-3 gap-4 text-center mb-6">
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {(completedTaskResult.result?.successful_offers?.length || 0) + (completedTaskResult.result?.failed_offers?.length || 0)}
                  </div>
                  <div className="text-sm text-gray-600">Wszystkie</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-green-600">
                    {completedTaskResult.result?.successful_offers?.length || 0}
                  </div>
                  <div className="text-sm text-gray-600">Pomyślne</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-red-600">
                    {completedTaskResult.result?.failed_offers?.length || 0}
                  </div>
                  <div className="text-sm text-gray-600">Błędy</div>
                </div>
              </div>

              {/* Successful offers */}
              {completedTaskResult.result?.successful_offers && completedTaskResult.result.successful_offers.length > 0 && (
                <div className="mb-6">
                  <h4 className="text-sm font-medium text-green-800 mb-2">✅ Pomyślnie zaktualizowane oferty:</h4>
                  <div className="max-h-24 overflow-y-auto bg-green-50 rounded p-3 border border-green-200">
                    {completedTaskResult.result.successful_offers.map((offerId: string, index: number) => (
                      <div key={index} className="text-xs text-green-700 mb-1">
                        <span className="font-medium">Oferta {offerId}:</span> Zaktualizowano pomyślnie
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Failed offers */}
              {completedTaskResult.result?.failed_offers && completedTaskResult.result.failed_offers.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-red-800 mb-2">❌ Błędy aktualizacji ({completedTaskResult.result.failed_offers.length}):</h4>
                  <div className="max-h-32 overflow-y-auto bg-red-50 rounded border border-red-200">
                    {completedTaskResult.result.failed_offers.map((failedOffer: any, index: number) => {
                      const originalError = failedOffer.error || 'Nieznany błąd'
                      const friendlyError = getUserFriendlyError(originalError)
                      const showTechnicalDetails = originalError !== friendlyError

                      return (
                        <div key={index} className="text-xs p-2 border-b border-red-100 last:border-b-0">
                          <div className="font-medium text-red-800">
                            Oferta {failedOffer.offer_id}:
                          </div>
                          <div className="text-red-600 mt-1">
                            {friendlyError}
                            {showTechnicalDetails && (
                              <div className="text-red-500 text-xs mt-1 opacity-75" title={originalError}>
                                Szczegóły techniczne: {originalError}
                              </div>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Task Failure */}
          {completedTaskResult.status === 'FAILURE' && (
            <div className="bg-red-50 rounded border border-red-200 p-4">
              <h4 className="text-sm font-medium text-red-800 mb-2">❌ Zadanie zakończone błędem:</h4>
              <div className="text-red-600 text-sm">
                {completedTaskResult.result?.exc_message || 'Nieznany błąd podczas przetwarzania'}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Restore Results */}
      {restoreTasksStatus && restoreTaskIds.length > 0 && (
        <div className="bg-white rounded-lg shadow border p-6">
          <h3 className="text-lg font-semibold mb-4">Wyniki przywracania ofert</h3>
          
          {(() => {
            const summary = getRestoreSummary()
            const hasCompletedTasks = restoreTasksStatus.data && (restoreTasksStatus.data as TaskStatus[]).some((task: TaskStatus) => 
              task.status === 'SUCCESS' || task.status === 'FAILURE'
            )
            
            if (!hasCompletedTasks) {
              return (
                <div className="text-center py-4">
                  <div className="text-blue-600">Przywracanie ofert w toku...</div>
                  <div className="text-sm text-gray-500 mt-1">
                    Przetwarzane: {summary.pending} ofert
                  </div>
                </div>
              )
            }
            
            return (
              <>
                {/* Summary Statistics */}
                <div className="grid grid-cols-3 gap-4 text-center mb-6">
                  <div>
                    <div className="text-2xl font-bold text-gray-900">
                      {summary.total}
                    </div>
                    <div className="text-sm text-gray-600">Wszystkie</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-green-600">
                      {summary.successful}
                    </div>
                    <div className="text-sm text-gray-600">Przywrócone</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-red-600">
                      {summary.failed}
                    </div>
                    <div className="text-sm text-gray-600">Błędy</div>
                  </div>
                </div>

                {/* Successful offers */}
                {summary.successful > 0 && (
                  <div className="mb-6">
                    <h4 className="text-sm font-medium text-green-800 mb-2">✅ Pomyślnie przywrócone oferty:</h4>
                    <div className="max-h-24 overflow-y-auto bg-green-50 rounded p-3 border border-green-200">
                      {(restoreTasksStatus.data as TaskStatus[])
                        ?.filter((task: TaskStatus) => task.status === 'SUCCESS' && task.result?.status === 'SUCCESS')
                        .map((task: TaskStatus, index: number) => (
                          <div key={index} className="text-xs text-green-700 mb-1">
                            <span className="font-medium">Oferta {task.result?.offer_id}:</span> 
                            {' '}Przywrócono z kopii zapasowej
                          </div>
                        ))}
                    </div>
                  </div>
                )}

                {/* Failed offers */}
                {summary.failed > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-red-800 mb-2">❌ Błędy przywracania ({summary.failed}):</h4>
                    <div className="max-h-32 overflow-y-auto bg-red-50 rounded border border-red-200">
                      {(restoreTasksStatus.data as TaskStatus[])
                        ?.filter((task: TaskStatus) => 
                          (task.status === 'SUCCESS' && task.result?.status !== 'SUCCESS') ||
                          task.status === 'FAILURE'
                        )
                        .map((task: TaskStatus, index: number) => (
                          <div key={index} className="text-xs p-2 border-b border-red-100 last:border-b-0">
                            <div className="font-medium text-red-800">
                              Oferta {task.result?.offer_id || 'nieznana'}:
                            </div>
                            <div className="text-red-600 mt-1">
                              {task.result?.error || task.error || 'Nieznany błąd'}
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </>
            )
          })()}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-center space-x-4">
        <button 
          onClick={updateOffers}
          disabled={isProcessing}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isProcessing ? 'Przetwarzanie...' : 'Aktualizuj oferty'}
        </button>
        <button 
          onClick={restoreOffers}
          disabled={isProcessing}
          className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isProcessing ? 'Przywracanie...' : 'Przywróć ofertę sprzed edycji'}
        </button>
      </div>

      {/* Name conflict modal */}
      <Modal 
        isOpen={isNameConflictModalOpen}
        onClose={handleNameConflictCancel}
        title="Konflikt nazwy szablonu"
        className="max-w-md"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Szablon o nazwie "{conflictData?.original_name}" już istnieje w docelowym koncie.
          </p>
          <p className="text-sm text-gray-600">
            Podaj nową nazwę dla kopiowanego szablonu:
          </p>
          <div>
            <Label htmlFor="new-template-name">Nowa nazwa szablonu</Label>
            <Input
              id="new-template-name"
              type="text"
              value={newTemplateName}
              onChange={(e) => setNewTemplateName(e.target.value)}
              placeholder="Podaj nową nazwę szablonu"
              className="mt-1"
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleNameConflictSubmit()
                }
              }}
            />
          </div>
          <div className="flex justify-end space-x-2">
            <Button 
              variant="outline" 
              onClick={handleNameConflictCancel}
            >
              Anuluj
            </Button>
            <Button 
              onClick={handleNameConflictSubmit}
              disabled={!newTemplateName.trim()}
            >
              Kopiuj
            </Button>
          </div>
        </div>
      </Modal>

      {/* Duplicate Template Modal */}
      <Modal
        isOpen={isDuplicateModalOpen}
        onClose={() => {
          setIsDuplicateModalOpen(false)
          setDuplicateTemplateName('')
        }}
        title="Duplikuj szablon"
      >
        <div className="space-y-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium mb-2">Szczegóły duplikowania</h4>
            <div className="text-sm space-y-1">
              <div><span className="font-medium">Szablon źródłowy:</span> {selectedTemplate}</div>
              <div><span className="font-medium">Konto:</span> {current?.nazwa_konta}</div>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nazwa nowego szablonu
            </label>
            <input
              type="text"
              value={duplicateTemplateName}
              onChange={(e) => setDuplicateTemplateName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Wprowadź nazwę nowego szablonu"
              autoFocus
            />
            <p className="text-xs text-gray-500 mt-1">
              Nowy szablon zostanie utworzony w tym samym koncie
            </p>
          </div>
          
          <div className="flex justify-end gap-2">
            <button
              onClick={() => {
                setIsDuplicateModalOpen(false)
                setDuplicateTemplateName('')
              }}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Anuluj
            </button>
            <button
              onClick={confirmDuplicateTemplate}
              disabled={!duplicateTemplateName.trim() || duplicateTemplateMutation.isPending}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {duplicateTemplateMutation.isPending ? 'Duplikowanie...' : 'Duplikuj szablon'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
} 