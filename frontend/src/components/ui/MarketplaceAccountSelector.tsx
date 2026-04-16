import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useSharedAccounts } from '../../hooks/marketplaces/allegro/accounts'
import { useAccountStore } from '../../store/accountStore'
import { MARKETPLACE_CONFIGS } from '../../types/marketplace'

interface Props {
  marketplaceType?: string // Filter by marketplace type (e.g., 'allegro', 'decathlon')
}

export default function MarketplaceAccountSelector({ marketplaceType }: Props) {
  const { accounts, isLoading } = useSharedAccounts()
  const { current, setCurrent, autoSelectFirst } = useAccountStore()
  
  // Filter accounts by marketplace type if specified
  const filteredAccounts = marketplaceType
    ? accounts?.filter(acc => acc.marketplace_type === marketplaceType)
    : accounts

  // Auto-select first account when accounts are loaded
  useEffect(() => {
    if (filteredAccounts && filteredAccounts.length > 0) {
      // If current account doesn't match the filter, auto-select first filtered account
      if (current && marketplaceType && current.marketplace_type !== marketplaceType) {
        setCurrent(filteredAccounts[0])
      } else if (!current) {
        autoSelectFirst(filteredAccounts)
      }
    }
  }, [filteredAccounts, autoSelectFirst, current, setCurrent, marketplaceType])

  // Show "No accounts" message with link to add account
  if (!isLoading && filteredAccounts && filteredAccounts.length === 0) {
    const marketplaceName = marketplaceType ? MARKETPLACE_CONFIGS[marketplaceType]?.name : 'marketplace'
    return (
      <div className="flex items-center space-x-2 text-sm">
        <span className="text-gray-500">Brak kont {marketplaceName}</span>
        <Link 
          to="/accounts" 
          className="text-blue-600 hover:text-blue-800 underline"
        >
          Dodaj konto
        </Link>
      </div>
    )
  }

  return (
    <select
      className="rounded border-gray-300 text-sm focus:ring-primary focus:border-primary"
      disabled={isLoading}
      value={current?.id ?? ''}
      onChange={e => {
        const id = Number(e.target.value)
        const sel = filteredAccounts?.find(a => a.id === id)
        setCurrent(sel)
      }}
    >
      <option value="" disabled>
        {isLoading ? 'Ładowanie...' : 'Wybierz konto'}
      </option>
      {filteredAccounts?.map(acc => {
        const marketplaceType = acc.marketplace_type || 'allegro'
        const icon = MARKETPLACE_CONFIGS[marketplaceType]?.icon || '❓'
        return (
          <option key={acc.id} value={acc.id}>
            {icon} {acc.nazwa_konta}
          </option>
        )
      })}
    </select>
  )
}
