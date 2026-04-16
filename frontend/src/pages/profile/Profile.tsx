import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { useChangePassword, useDeleteAccount } from '../../hooks/shared/auth'
import { useFeatureFlags } from '../../hooks/shared/useFeatureFlags'
import { Bot, Settings } from 'lucide-react'

export default function Profile() {
  const { user } = useAuthStore()
  const { isUserAIConfigEnabled } = useFeatureFlags()
  const changePasswordMutation = useChangePassword()
  const deleteAccountMutation = useDeleteAccount()
  
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  })
  
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleteConfirmText, setDeleteConfirmText] = useState('')

  const handlePasswordChange = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      alert('Nowe hasła nie są identyczne')
      return
    }
    
    if (passwordForm.new_password.length < 8) {
      alert('Hasło musi mieć co najmniej 8 znaków')
      return
    }
    
    changePasswordMutation.mutate({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password
    }, {
      onSuccess: () => {
        setPasswordForm({
          current_password: '',
          new_password: '',
          confirm_password: ''
        })
      }
    })
  }

  const handleDeleteAccount = () => {
    if (deleteConfirmText !== 'USUŃ KONTO') {
      alert('Wpisz "USUŃ KONTO" aby potwierdzić')
      return
    }
    
    deleteAccountMutation.mutate()
  }

  const isVsprintEmployee = user?.role === 'vsprint_employee'
  const isGoogleSSOUser = !!user?.google_id
  const hasPassword = user?.email && !user?.email.endsWith('@vsprint.pl')
  const canDeleteAccount = !isVsprintEmployee && !isGoogleSSOUser

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <h1 className="text-3xl font-semibold">Profil użytkownika</h1>
      
      {/* User Info */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Informacje o koncie</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Imię</label>
            <p className="mt-1 text-sm text-gray-900">{user?.first_name}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Nazwisko</label>
            <p className="mt-1 text-sm text-gray-900">{user?.last_name}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <p className="mt-1 text-sm text-gray-900">{user?.email}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Rola</label>
            <p className="mt-1 text-sm text-gray-900">
              {user?.role === 'admin' ? 'Administrator' : 'Użytkownik'}
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Typ konta</label>
            <p className="mt-1 text-sm text-gray-900">
              {isGoogleSSOUser ? 'Google SSO' : 'Standardowe'}
            </p>
          </div>
        </div>
      </div>

      {/* AI Configuration - Only show if enabled */}
      {isUserAIConfigEnabled() && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Bot className="h-5 w-5 text-blue-600" />
              <h2 className="text-xl font-semibold">Konfiguracja AI</h2>
            </div>
            <Link
              to="/profile/ai-config"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <Settings className="h-4 w-4 mr-2" />
              Zarządzaj
            </Link>
          </div>
          <p className="text-gray-600">
            Skonfiguruj własne klucze API dla AI (Anthropic Claude, Google Gemini) 
            lub skorzystaj z domyślnego klucza vAutomate.
          </p>
        </div>
      )}

      {/* Password Change */}
      {hasPassword && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Zmiana hasła</h2>
          <form onSubmit={handlePasswordChange} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Obecne hasło
              </label>
              <input
                type="password"
                value={passwordForm.current_password}
                onChange={(e) => setPasswordForm(prev => ({ ...prev, current_password: e.target.value }))}
                className="mt-1 block w-full px-3 py-2 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Nowe hasło
              </label>
              <input
                type="password"
                value={passwordForm.new_password}
                onChange={(e) => setPasswordForm(prev => ({ ...prev, new_password: e.target.value }))}
                className="mt-1 block w-full px-3 py-2 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                minLength={8}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Potwierdź nowe hasło
              </label>
              <input
                type="password"
                value={passwordForm.confirm_password}
                onChange={(e) => setPasswordForm(prev => ({ ...prev, confirm_password: e.target.value }))}
                className="mt-1 block w-full px-3 py-2 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                minLength={8}
                required
              />
            </div>
            <button
              type="submit"
              disabled={changePasswordMutation.isPending}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {changePasswordMutation.isPending ? 'Zmieniam...' : 'Zmień hasło'}
            </button>
          </form>
        </div>
      )}

      {/* Google SSO Info */}
      {isGoogleSSOUser && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-2 text-blue-800">Konto Google SSO</h2>
          <p className="text-blue-700">
            Twoje konto jest połączone z Google SSO. Hasło jest zarządzane przez Google.
          </p>
        </div>
      )}

      {/* Account Deletion */}
      {canDeleteAccount && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4 text-red-800">Strefa niebezpieczna</h2>
          
          {!showDeleteConfirm ? (
            <div>
              <p className="text-red-700 mb-4">
                Usunięcie konta spowoduje trwałe usunięcie wszystkich Twoich danych, 
                w tym kont marketplace, szablonów i kopii zapasowych.
              </p>
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"
              >
                Usuń konto
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-red-700 font-medium">
                Czy na pewno chcesz usunąć swoje konto? Ta operacja jest nieodwracalna!
              </p>
              <p className="text-red-600 text-sm">
                Wpisz "USUŃ KONTO" aby potwierdzić:
              </p>
              <input
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                className="block w-full px-3 py-2 rounded-md border-red-300 shadow-sm focus:border-red-500 focus:ring-red-500"
                placeholder="USUŃ KONTO"
              />
              <div className="flex gap-2">
                <button
                  onClick={handleDeleteAccount}
                  disabled={deleteAccountMutation.isPending || deleteConfirmText !== 'USUŃ KONTO'}
                  className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 disabled:opacity-50"
                >
                  {deleteAccountMutation.isPending ? 'Usuwam...' : 'Potwierdź usunięcie'}
                </button>
                <button
                  onClick={() => {
                    setShowDeleteConfirm(false)
                    setDeleteConfirmText('')
                  }}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
                >
                  Anuluj
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Vsprint Employee Info */}
      {isVsprintEmployee && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-2 text-green-800">Konto pracownika</h2>
          <p className="text-green-700">
            Nie możesz usunąć swojego konta. 
            Skontaktuj się z administratorem w sprawie zarządzania kontem.
          </p>
        </div>
      )}

      {/* Google SSO Account Protection Info */}
      {isGoogleSSOUser && !isVsprintEmployee && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-2 text-blue-800">Ochrona konta Google SSO</h2>
          <p className="text-blue-700">
            Konta połączone z Google SSO nie mogą być usuwane z poziomu aplikacji. 
            Aby usunąć konto, skontaktuj się z administratorem.
          </p>
        </div>
      )}
    </div>
  )
} 