import { useSharedAccounts } from '../../hooks/marketplaces/allegro/accounts'
import { useState } from 'react'
import AddAccountModal from '../../components/accounts/AddAccountModal'
import ReAuthAccountModal from '../../components/accounts/ReAuthAccountModal'
import { MARKETPLACE_CONFIGS, AuthenticationType } from '../../types/marketplace'
import { Trash2, RefreshCw } from 'lucide-react'

export default function Accounts() {
  const [modalOpen, setModalOpen] = useState(false)
  const [reAuthModal, setReAuthModal] = useState<{ open: boolean; accountId: number; accountName: string }>({
    open: false,
    accountId: 0,
    accountName: ''
  })
  const { 
    accounts, 
    isLoading, 
    deleteAccount,
    canManageAccount,
    ownedCount,
    sharedCount,
    sharedWithTeamCount,
    totalAccounts,
    isVsprintEmployee
  } = useSharedAccounts()
  
  const handleDelete = async (accountId: number, accountName: string) => {
    if (confirm(`Usunąć konto ${accountName}?`)) {
      await deleteAccount(accountId)
    }
  }

  const handleReAuth = (accountId: number, accountName: string) => {
    setReAuthModal({ open: true, accountId, accountName })
  }

  const getTokenStatus = (account: any) => {
    const marketplace = account.marketplace_type || 'allegro'
    const config = MARKETPLACE_CONFIGS[marketplace]
    
    // API key-based marketplaces (Mirakl) don't have token expiry
    if (config?.authType === AuthenticationType.API_KEY) {
      return { status: 'valid', label: 'Aktywne', color: 'green' }
    }
    
    // OAuth-based marketplaces check token expiry
    if (account.needs_reauth) {
      return { status: 'expired', label: 'Wymaga ponownej autoryzacji', color: 'red' }
    }

    if (account.refresh_token_expires_at) {
      const expiryDate = new Date(account.refresh_token_expires_at)
      const daysUntilExpiry = Math.floor((expiryDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24))
      
      if (daysUntilExpiry <= 7) {
        return { status: 'expiring', label: `Wygasa za ${daysUntilExpiry} dni`, color: 'yellow' }
      }
      
      if (daysUntilExpiry <= 14) {
        return { status: 'warning', label: `Wygasa za ${daysUntilExpiry} dni`, color: 'yellow' }
      }

      return { status: 'valid', label: 'Aktywne', color: 'green' }
    }

    return { status: 'unknown', label: 'Nieznany status', color: 'gray' }
  }

  return (
    <div className="space-y-6 w-full flex flex-col">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Integracje</h1>
          <p className="text-gray-600 mt-1">
            Liczba kont: {totalAccounts}
          </p>
        </div>
        <button 
          className="rounded bg-green-600 px-4 py-2 text-white hover:bg-green-700 flex items-center space-x-2" 
          onClick={() => setModalOpen(true)}
        >
          <span className="text-xl">+</span>
          <span>Dodaj integrację</span>
        </button>
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}
      
      {!isLoading && accounts.length === 0 && (
        <div className="bg-white rounded-lg shadow border p-12 text-center">
          <div className="text-gray-400 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <p className="text-gray-500 text-lg mb-4">Brak połączonych integracji</p>
          <p className="text-gray-400 text-sm mb-6">Dodaj pierwsze połączenie z marketplace</p>
          <button 
            className="rounded bg-green-600 px-6 py-3 text-white hover:bg-green-700 inline-flex items-center space-x-2" 
            onClick={() => setModalOpen(true)}
          >
            <span className="text-xl">+</span>
            <span>Dodaj integrację</span>
          </button>
        </div>
      )}

      {!isLoading && accounts.length > 0 && (
        <div className="bg-white rounded-lg shadow border overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Platforma
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Nazwa
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Właściciel
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Data dodania
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Akcje
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {accounts.map(account => {
                const tokenStatus = getTokenStatus(account)
                const marketplace = account.marketplace_type || 'allegro'
                const config = MARKETPLACE_CONFIGS[marketplace]
                
                return (
                  <tr key={account.id} className={tokenStatus.status === 'expired' ? 'bg-red-50' : 'hover:bg-gray-50'}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl">{config?.icon || '❓'}</span>
                        <span className="text-sm font-medium text-gray-900">{config?.name || marketplace}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{account.nazwa_konta}</div>
                      {isVsprintEmployee && account.shared_with_vsprint && account.is_owner && (
                        <span className="inline-block bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full mt-1">
                          Udostępnione zespołowi
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        tokenStatus.color === 'red' ? 'bg-red-100 text-red-800' :
                        tokenStatus.color === 'yellow' ? 'bg-yellow-100 text-yellow-800' :
                        tokenStatus.color === 'green' ? 'bg-green-100 text-green-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {tokenStatus.label}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {isVsprintEmployee ? (
                        account.is_owner ? 'Właściciel' : 'Udostępnione'
                      ) : (
                        'Ty'
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(account.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end space-x-2">
                        {/* Only show re-auth button for OAuth-based marketplaces */}
                        {config?.authType === AuthenticationType.OAUTH && (
                          <button 
                            className={`inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded ${
                              account.needs_reauth 
                                ? 'text-white bg-orange-600 hover:bg-orange-700' 
                                : 'text-blue-700 bg-blue-100 hover:bg-blue-200'
                            }`}
                            onClick={() => handleReAuth(account.id, account.nazwa_konta)}
                            title="Ponowna autoryzacja"
                          >
                            <RefreshCw className="w-3 h-3 mr-1" />
                            Re-auth
                          </button>
                        )}
                        {canManageAccount(account) && (
                          <button 
                            className="inline-flex items-center px-3 py-1.5 text-xs font-medium rounded text-red-700 bg-red-100 hover:bg-red-200"
                            onClick={() => handleDelete(account.id, account.nazwa_konta)}
                            title="Usuń konto"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <AddAccountModal open={modalOpen} onClose={() => setModalOpen(false)} />
      <ReAuthAccountModal 
        open={reAuthModal.open} 
        onClose={() => setReAuthModal({ open: false, accountId: 0, accountName: '' })} 
        accountId={reAuthModal.accountId}
        accountName={reAuthModal.accountName}
      />
    </div>
  )
} 