import { useState } from 'react'
import { Search } from 'lucide-react'
import OfferSelectorModal from '../titles/OfferSelectorModal'

interface OfferSelectorButtonProps {
  /** Current account ID for fetching offers */
  accountId: number
  /** Current offer IDs string (newline-separated) */
  offerIds: string
  /** Function to update offer IDs */
  setOfferIds: (ids: string) => void
  /** Optional error setter to clear errors when selection changes */
  setError?: (error: string | null) => void
  /** Optional custom button text */
  label?: string
  /** Optional custom button className */
  className?: string
  /** Optional callback when selection is confirmed */
  onSelectionChange?: (selectedIds: string[]) => void
}

/**
 * Reusable button component that opens the visual offer selector modal
 * and integrates with any module's existing offer ID input pattern.
 */
export default function OfferSelectorButton({
  accountId,
  offerIds,
  setOfferIds,
  setError,
  label = "Wybierz z listy",
  className = "px-4 py-2 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors flex items-center gap-2",
  onSelectionChange
}: OfferSelectorButtonProps) {
  const [isModalOpen, setIsModalOpen] = useState(false)

  const handleOpenModal = () => {
    setIsModalOpen(true)
  }

  const handleConfirm = (selectedOfferIds: string[]) => {
    // Convert selected offer IDs back to newline-separated string
    const newOfferIds = selectedOfferIds.join('\n')
    setOfferIds(newOfferIds)
    
    // Clear any existing errors
    if (setError) {
      setError(null)
    }
    
    // Call optional selection change callback
    if (onSelectionChange) {
      onSelectionChange(selectedOfferIds)
    }
    
    setIsModalOpen(false)
  }

  const handleCancel = () => {
    setIsModalOpen(false)
  }

  // Parse current offer IDs for the modal
  const getCurrentSelectedIds = () => {
    return offerIds
      .split('\n')
      .map(id => id.trim())
      .filter(id => id.length > 0 && /^\d+$/.test(id))
  }

  return (
    <>
      <button
        type="button"
        onClick={handleOpenModal}
        className={className}
      >
        <Search className="w-4 h-4" />
        {label}
      </button>

      <OfferSelectorModal
        isOpen={isModalOpen}
        onClose={handleCancel}
        onConfirm={handleConfirm}
        accountId={accountId}
        initialSelectedIds={getCurrentSelectedIds()}
      />
    </>
  )
}
