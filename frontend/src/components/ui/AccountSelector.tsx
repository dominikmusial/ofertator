import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useSharedAccounts } from '../../hooks/marketplaces/allegro/accounts'
import { useAccountStore } from '../../store/accountStore'
import { MARKETPLACE_CONFIGS } from '../../types/marketplace'

export default function AccountSelector() {
  const { accounts, isLoading } = useSharedAccounts()
  const { current, setCurrent, autoSelectFirst } = useAccountStore()
  
  // Auto-select first account when accounts are loaded
  useEffect(() => {
    if (accounts && accounts.length > 0) {
      autoSelectFirst(accounts)
    }
  }, [accounts, autoSelectFirst])

  // Show "No accounts" message with link to add account
  if (!isLoading && accounts && accounts.length === 0) {
    return (
      <div className="flex items-center space-x-2 text-sm">
        <span className="text-gray-500">Brak kont</span>
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
        const sel = accounts?.find(a => a.id === id)
        setCurrent(sel)
      }}
    >
      <option value="" disabled>
        {isLoading ? 'Ładowanie...' : 'Wybierz konto'}
      </option>
      {accounts?.map(acc => {
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