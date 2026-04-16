import React, { useState, useEffect } from 'react'
import { Users, Clock, CheckCircle, XCircle, Settings, Mail, Search, Filter, ChevronLeft, ChevronRight, Shield, 
         UserX, UserCheck, Trash2, AlertTriangle, Info, Eye, Loader2, UserPlus } from 'lucide-react'
import { useToastStore } from '../../store/toastStore'
import { api } from '../../lib/api'
import PermissionManager from '../../components/admin/PermissionManager'
import CreateUserModal from '../../components/admin/CreateUserModal'

interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  is_active: boolean
  is_verified: boolean
  admin_approved: boolean
  role: 'user' | 'admin' | 'vsprint_employee'
  company_domain?: string
  google_id?: string
  created_at: string
  updated_at?: string
  deactivated_at?: string
  deactivation_reason?: string
}

interface UserManagementInfo {
  user_id: number
  email: string
  first_name: string
  last_name: string
  role: string
  is_active: boolean
  is_deactivated: boolean
  deactivated_at?: string
  deactivation_reason?: string
  data_counts: {
    accounts: number
    templates: number
    images: number
  }
  can_delete: boolean
  can_deactivate: boolean
  is_vsprint: boolean
}

interface UserManagementResponse {
  success: boolean
  message: string
  user_email: string
  user_type?: string
  transferred_data?: {
    accounts: number
    templates: number
    images: number
  }
  archived_data?: {
    token_usage: number
    daily_stats: number
    activity_logs: number
  }
  action_timestamp: string
}

interface PendingUsersResponse {
  pending_users: User[]
  total_count: number
}

interface AdminNotificationEmail {
  id: number
  email: string
  is_active: boolean
  created_at: string
  created_by_admin_id: number
}

interface NotificationEmailsResponse {
  emails: AdminNotificationEmail[]
  total_count: number
}

interface UsersSearchResponse {
  users: User[]
  total_count: number
  total_pages: number
  current_page: number
  per_page: number
}

export default function AdminUsers() {
  const [pendingUsers, setPendingUsers] = useState<User[]>([])
  const [allUsers, setAllUsers] = useState<User[]>([])
  const [notificationEmails, setNotificationEmails] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'pending' | 'all' | 'settings'>('pending')
  const [rejectionReason, setRejectionReason] = useState('')
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null)
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [showPermissionModal, setShowPermissionModal] = useState(false)
  const [showCreateUserModal, setShowCreateUserModal] = useState(false)
  const [permissionUserId, setPermissionUserId] = useState<number | null>(null)
  const [newEmail, setNewEmail] = useState('')

  // User management modals and state
  const [showUserManagementModal, setShowUserManagementModal] = useState(false)
  const [managementAction, setManagementAction] = useState<'deactivate' | 'reactivate' | 'delete' | 'info'>('info')
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [userManagementInfo, setUserManagementInfo] = useState<UserManagementInfo | null>(null)
  const [loadingUserInfo, setLoadingUserInfo] = useState(false)
  const [managementReason, setManagementReason] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  
  // Delete user options (for vsprint users)
  const [deleteOptions, setDeleteOptions] = useState({
    keep_accounts: true,
    keep_templates: true,
    keep_images: true
  })

  // Search and pagination state
  const [searchTerm, setSearchTerm] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalUsers, setTotalUsers] = useState(0)
  const [perPage] = useState(25)
  
  const { addToast } = useToastStore()

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    if (activeTab === 'all') {
      loadAllUsers()
    }
  }, [currentPage, searchTerm, roleFilter, statusFilter, activeTab])

  const loadData = async () => {
    try {
      setLoading(true)
      
      // Load pending users
      const pendingResponse = await api.get<PendingUsersResponse>('/admin/users/pending')
      setPendingUsers(pendingResponse.data.pending_users)
      
      // Load all users with search and pagination
      await loadAllUsers()
      
      // Load notification emails
      const emailsResponse = await api.get<NotificationEmailsResponse>('/admin/notification-emails')
      setNotificationEmails(emailsResponse.data.emails.map(e => e.email))
      
    } catch (error: any) {
      console.error('Failed to load admin data:', error)
      addToast('Nie udało się wczytać danych administratora', 'error')
    } finally {
      setLoading(false)
    }
  }

  const loadAllUsers = async () => {
    try {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        per_page: perPage.toString()
      })
      
      if (searchTerm) params.append('search', searchTerm)
      if (roleFilter) params.append('role_filter', roleFilter)
      if (statusFilter) params.append('status_filter', statusFilter)
      
      const response = await api.get<UsersSearchResponse>(`/admin/users/search?${params}`)
      const data = response.data
      
      setAllUsers(data.users)
      setTotalUsers(data.total_count)
      setTotalPages(data.total_pages)
      setCurrentPage(data.current_page)
      
    } catch (error: any) {
      console.error('Failed to load users:', error)
      addToast('Nie udało się wczytać użytkowników', 'error')
    }
  }

  const handleSearch = (value: string) => {
    setSearchTerm(value)
    setCurrentPage(1) // Reset to first page when searching
  }

  const handleRoleFilter = (value: string) => {
    setRoleFilter(value)
    setCurrentPage(1)
  }

  const handleStatusFilter = (value: string) => {
    setStatusFilter(value)
    setCurrentPage(1)
  }

  const clearFilters = () => {
    setSearchTerm('')
    setRoleFilter('')
    setStatusFilter('')
    setCurrentPage(1)
  }

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  const approveUser = async (userId: number) => {
    try {
      await api.post(`/admin/users/${userId}/approve`)
      addToast('Użytkownik został zatwierdzony', 'success')
      loadData()
    } catch (error: any) {
      console.error('Failed to approve user:', error)
      addToast(error.response?.data?.detail || 'Nie udało się zatwierdzić użytkownika', 'error')
    }
  }

  const rejectUser = async () => {
    if (!selectedUserId) return
    
    try {
      await api.post(`/admin/users/${selectedUserId}/reject`, {
        user_id: selectedUserId,
        approved: false,
        rejection_reason: rejectionReason
      })
      addToast('Użytkownik został odrzucony', 'success')
      setShowRejectModal(false)
      setRejectionReason('')
      setSelectedUserId(null)
      loadData()
    } catch (error: any) {
      console.error('Failed to reject user:', error)
      addToast(error.response?.data?.detail || 'Nie udało się odrzucić użytkownika', 'error')
    }
  }

  const updateNotificationEmails = async () => {
    try {
      await api.post('/admin/notification-emails', {
        emails: notificationEmails
      })
      addToast('Lista emaili została zaktualizowana', 'success')
    } catch (error: any) {
      console.error('Failed to update notification emails:', error)
      addToast(error.response?.data?.detail || 'Nie udało się zaktualizować emaili', 'error')
    }
  }

  const addNotificationEmail = async () => {
    if (newEmail && !notificationEmails.includes(newEmail)) {
      const updatedEmails = [...notificationEmails, newEmail]
      setNotificationEmails(updatedEmails)
      setNewEmail('')
      
      // Auto-save immediately
      try {
        await api.post('/admin/notification-emails', {
          emails: updatedEmails
        })
        addToast('Email został dodany do powiadomień', 'success')
      } catch (error: any) {
        console.error('Failed to save notification email:', error)
        addToast(error.response?.data?.detail || 'Nie udało się zapisać emaila', 'error')
        // Revert the change on error
        setNotificationEmails(notificationEmails)
      }
    }
  }

  const removeNotificationEmail = async (email: string) => {
    if (confirm(`Czy na pewno chcesz usunąć email ${email} z powiadomień?`)) {
      const updatedEmails = notificationEmails.filter(e => e !== email)
      setNotificationEmails(updatedEmails)
      
      // Auto-save immediately
      try {
        await api.post('/admin/notification-emails', {
          emails: updatedEmails
        })
        addToast('Email został usunięty z powiadomień', 'success')
      } catch (error: any) {
        console.error('Failed to remove notification email:', error)
        addToast(error.response?.data?.detail || 'Nie udało się usunąć emaila', 'error')
        // Revert the change on error
        setNotificationEmails(notificationEmails)
      }
    }
  }

  const openPermissionModal = (userId: number) => {
    setPermissionUserId(userId)
    setShowPermissionModal(true)
  }

  const closePermissionModal = () => {
    setPermissionUserId(null)
    setShowPermissionModal(false)
  }

  // User management functions
  const openUserManagementModal = async (user: User, action: 'deactivate' | 'reactivate' | 'delete' | 'info') => {
    setSelectedUser(user)
    setManagementAction(action)
    setShowUserManagementModal(true)
    setManagementReason('')
    setDeleteOptions({ keep_accounts: true, keep_templates: true, keep_images: true })
    
    // Load user management info
    if (action === 'delete' || action === 'info') {
      await loadUserManagementInfo(user.id)
    }
  }

  const closeUserManagementModal = () => {
    setSelectedUser(null)
    setUserManagementInfo(null)
    setShowUserManagementModal(false)
    setManagementReason('')
    setDeleteOptions({ keep_accounts: true, keep_templates: true, keep_images: true })
    setIsProcessing(false)
  }

  const loadUserManagementInfo = async (userId: number) => {
    setLoadingUserInfo(true)
    try {
      const response = await api.get<UserManagementInfo>(`/admin/users/${userId}/management-info`)
      setUserManagementInfo(response.data)
    } catch (error: any) {
      console.error('Failed to load user management info:', error)
      addToast(error.response?.data?.detail || 'Nie udało się wczytać informacji o użytkowniku', 'error')
    } finally {
      setLoadingUserInfo(false)
    }
  }

  const handleDeactivateUser = async () => {
    if (!selectedUser || isProcessing) return
    
    setIsProcessing(true)
    try {
      const response = await api.post<UserManagementResponse>(`/admin/users/${selectedUser.id}/deactivate`, {
        reason: managementReason || undefined
      })
      
      addToast(`Użytkownik ${response.data.user_email} został dezaktywowany`, 'success')
      closeUserManagementModal()
      loadData()
    } catch (error: any) {
      console.error('Failed to deactivate user:', error)
      addToast(error.response?.data?.detail || 'Nie udało się dezaktywować użytkownika', 'error')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleReactivateUser = async () => {
    if (!selectedUser || isProcessing) return
    
    setIsProcessing(true)
    try {
      const response = await api.post<UserManagementResponse>(`/admin/users/${selectedUser.id}/reactivate`, {})
      
      addToast(`Użytkownik ${response.data.user_email} został przywrócony`, 'success')
      closeUserManagementModal()
      loadData()
    } catch (error: any) {
      console.error('Failed to reactivate user:', error)
      addToast(error.response?.data?.detail || 'Nie udało się przywrócić użytkownika', 'error')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleDeleteUser = async () => {
    if (!selectedUser || isProcessing) return
    
    setIsProcessing(true)
    try {
      const requestData = {
        reason: managementReason || undefined,
        ...deleteOptions
      }
      
      const response = await api.delete<UserManagementResponse>(`/admin/users/${selectedUser.id}/delete`, {
        data: requestData
      })
      
      let successMessage = `Użytkownik ${response.data.user_email} został usunięty`
      if (response.data.transferred_data) {
        const transferred = response.data.transferred_data
        successMessage += ` (przeniesiono: ${transferred.accounts} kont, ${transferred.templates} szablonów, ${transferred.images} zdjęć)`
      }
      
      addToast(successMessage, 'success')
      closeUserManagementModal()
      loadData()
    } catch (error: any) {
      console.error('Failed to delete user:', error)
      addToast(error.response?.data?.detail || 'Nie udało się usunąć użytkownika', 'error')
    } finally {
      setIsProcessing(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('pl-PL')
  }

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'user': return 'Użytkownik zewnętrzny'
      case 'admin': return 'Administrator'
      case 'vsprint_employee': return 'Pracownik vsprint'
      default: return role
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8 flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Zarządzanie użytkownikami</h1>
            <p className="text-gray-600">Zatwierdzaj nowych użytkowników i zarządzaj powiadomieniami</p>
          </div>
          <button
            onClick={() => setShowCreateUserModal(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            <UserPlus className="w-5 h-5" />
            <span>Utwórz użytkownika</span>
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Oczekujące zatwierdzenia</p>
                <p className="text-3xl font-bold text-orange-600">{pendingUsers.length}</p>
              </div>
              <Clock className="h-8 w-8 text-orange-600" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Wszyscy użytkownicy</p>
                <p className="text-3xl font-bold text-blue-600">{allUsers.length}</p>
              </div>
              <Users className="h-8 w-8 text-blue-600" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Emaile powiadomień</p>
                <p className="text-3xl font-bold text-green-600">{notificationEmails.length}</p>
              </div>
              <Mail className="h-8 w-8 text-green-600" />
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="border-b border-gray-200">
            <nav className="flex">
              <button
                onClick={() => setActiveTab('pending')}
                className={`px-6 py-4 text-sm font-medium ${
                  activeTab === 'pending'
                    ? 'bg-blue-50 border-b-2 border-blue-600 text-blue-600'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                <Clock className="inline h-4 w-4 mr-2" />
                Oczekujące ({pendingUsers.length})
              </button>
              <button
                onClick={() => setActiveTab('all')}
                className={`px-6 py-4 text-sm font-medium ${
                  activeTab === 'all'
                    ? 'bg-blue-50 border-b-2 border-blue-600 text-blue-600'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                <Users className="inline h-4 w-4 mr-2" />
                Wszyscy użytkownicy ({totalUsers})
              </button>
              <button
                onClick={() => setActiveTab('settings')}
                className={`px-6 py-4 text-sm font-medium ${
                  activeTab === 'settings'
                    ? 'bg-blue-50 border-b-2 border-blue-600 text-blue-600'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                <Settings className="inline h-4 w-4 mr-2" />
                Ustawienia powiadomień
              </button>
            </nav>
          </div>

          <div className="p-6">
            {/* Pending Users Tab */}
            {activeTab === 'pending' && (
              <div>
                {pendingUsers.length === 0 ? (
                  <div className="text-center py-12">
                    <CheckCircle className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">Brak oczekujących użytkowników</h3>
                    <p className="mt-1 text-sm text-gray-500">Wszyscy użytkownicy zostali już zatwierdzeni</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Użytkownik
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Email
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Data rejestracji
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Akcje
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {pendingUsers.map((user) => (
                          <tr key={user.id}>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                                  <span className="text-sm font-medium text-gray-700">
                                    {user.first_name[0]}{user.last_name[0]}
                                  </span>
                                </div>
                                <div className="ml-4">
                                  <div className="text-sm font-medium text-gray-900">
                                    {user.first_name} {user.last_name}
                                  </div>
                                  <div className="text-sm text-gray-500">
                                    {getRoleLabel(user.role)}
                                  </div>
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {user.email}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {formatDate(user.created_at)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                              <div className="flex flex-col space-y-2">
                                <div className="flex space-x-2">
                                  <button
                                    onClick={() => approveUser(user.id)}
                                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                                  >
                                    <CheckCircle className="h-4 w-4 mr-1" />
                                    Zatwierdź
                                  </button>
                                  <button
                                    onClick={() => {
                                      setSelectedUserId(user.id)
                                      setShowRejectModal(true)
                                    }}
                                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                                  >
                                    <XCircle className="h-4 w-4 mr-1" />
                                    Odrzuć
                                  </button>
                                </div>
                                <button
                                  onClick={() => openPermissionModal(user.id)}
                                  className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                                >
                                  <Shield className="h-4 w-4 mr-1" />
                                  Zarządzaj uprawnieniami
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* All Users Tab */}
            {activeTab === 'all' && (
              <div className="space-y-4">
                {/* Search and Filters */}
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {/* Search */}
                    <div className="md:col-span-2">
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <input
                          type="text"
                          placeholder="Szukaj po nazwie lub emailu..."
                          value={searchTerm}
                          onChange={(e) => handleSearch(e.target.value)}
                          className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                    </div>
                    
                    {/* Role Filter */}
                    <div>
                      <select
                        value={roleFilter}
                        onChange={(e) => handleRoleFilter(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="">Wszystkie role</option>
                        <option value="user">Użytkownik zewnętrzny</option>
                        <option value="vsprint_employee">Pracownik vsprint</option>
                        <option value="admin">Administrator</option>
                      </select>
                    </div>
                    
                    {/* Status Filter */}
                    <div>
                      <select
                        value={statusFilter}
                        onChange={(e) => handleStatusFilter(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="">Wszystkie statusy</option>
                        <option value="active">Aktywny</option>
                        <option value="inactive">Nieaktywny</option>
                        <option value="verified">Zweryfikowany</option>
                        <option value="unverified">Niezweryfikowany</option>
                        <option value="approved">Zatwierdzony</option>
                        <option value="unapproved">Oczekujący</option>
                      </select>
                    </div>
                  </div>
                  
                  {/* Filter Summary and Clear */}
                  {(searchTerm || roleFilter || statusFilter) && (
                    <div className="mt-3 flex items-center justify-between">
                      <div className="text-sm text-gray-600">
                        Znaleziono {totalUsers} użytkowników
                        {searchTerm && ` dla "${searchTerm}"`}
                        {roleFilter && ` (rola: ${roleFilter})`}
                        {statusFilter && ` (status: ${statusFilter})`}
                      </div>
                      <button
                        onClick={clearFilters}
                        className="text-sm text-blue-600 hover:text-blue-800"
                      >
                        Wyczyść filtry
                      </button>
                    </div>
                  )}
                </div>
                {/* Desktop Table */}
                <div className="hidden lg:block overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Użytkownik
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Email
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Rola
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Data rejestracji
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Akcje
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {allUsers.map((user) => (
                        <tr key={user.id}>
                          <td className="px-4 py-4">
                            <div className="flex items-center">
                              <div className="h-8 w-8 rounded-full bg-gray-300 flex items-center justify-center flex-shrink-0">
                                <span className="text-xs font-medium text-gray-700">
                                  {user.first_name[0]}{user.last_name[0]}
                                </span>
                              </div>
                              <div className="ml-3 min-w-0">
                                <div className="text-sm font-medium text-gray-900 truncate">
                                  {user.first_name} {user.last_name}
                                </div>
                                <div className="text-xs text-gray-500">
                                  ID: {user.id}
                                </div>
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-4">
                            <div className="text-sm text-gray-900 truncate max-w-xs">
                              {user.email}
                            </div>
                          </td>
                          <td className="px-4 py-4">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              user.role === 'admin' ? 'bg-purple-100 text-purple-800' :
                              user.role === 'vsprint_employee' ? 'bg-blue-100 text-blue-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {getRoleLabel(user.role)}
                            </span>
                          </td>
                          <td className="px-4 py-4">
                            <div className="flex flex-wrap gap-1">
                              <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                              }`}>
                                {user.is_active ? 'Aktywny' : 'Nieaktywny'}
                              </span>
                              <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                user.is_verified ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                              }`}>
                                {user.is_verified ? 'Zweryfikowany' : 'Niezweryfikowany'}
                              </span>
                              {user.role === 'user' && (
                                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                  user.admin_approved ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800'
                                }`}>
                                  {user.admin_approved ? 'Zatwierdzony' : 'Oczekujący'}
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-4 text-sm text-gray-500">
                            {formatDate(user.created_at)}
                          </td>
                          <td className="px-4 py-4 text-sm text-gray-500">
                            <div className="flex flex-wrap gap-1">
                              {/* Permissions button for external users */}
                              {user.role === 'user' && (
                                <button
                                  onClick={() => openPermissionModal(user.id)}
                                  className="inline-flex items-center px-2 py-1 border border-gray-300 text-xs leading-4 font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                                >
                                  <Shield className="h-3 w-3 mr-1" />
                                  Uprawnienia
                                </button>
                              )}
                              
                              {/* User info button */}
                              <button
                                onClick={() => openUserManagementModal(user, 'info')}
                                className="inline-flex items-center px-2 py-1 border border-gray-300 text-xs leading-4 font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                              >
                                <Info className="h-3 w-3 mr-1" />
                                Info
                              </button>
                              
                              {/* Deactivate/Reactivate button - disabled for admin users */}
                              {user.role !== 'admin' && (
                                user.is_active ? (
                                  <button
                                    onClick={() => openUserManagementModal(user, 'deactivate')}
                                    className="inline-flex items-center px-2 py-1 border border-orange-300 text-xs leading-4 font-medium rounded text-orange-700 bg-orange-50 hover:bg-orange-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500"
                                  >
                                    <UserX className="h-3 w-3 mr-1" />
                                    Dezaktywuj
                                  </button>
                                ) : (
                                  <button
                                    onClick={() => openUserManagementModal(user, 'reactivate')}
                                    className="inline-flex items-center px-2 py-1 border border-green-300 text-xs leading-4 font-medium rounded text-green-700 bg-green-50 hover:bg-green-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                                  >
                                    <UserCheck className="h-3 w-3 mr-1" />
                                    Przywróć
                                  </button>
                                )
                              )}
                              
                              {/* Delete button - disabled for admin users */}
                              {user.role !== 'admin' && (
                                <button
                                  onClick={() => openUserManagementModal(user, 'delete')}
                                  className="inline-flex items-center px-2 py-1 border border-red-300 text-xs leading-4 font-medium rounded text-red-700 bg-red-50 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                                >
                                  <Trash2 className="h-3 w-3 mr-1" />
                                  Usuń
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                
                {/* Mobile Cards */}
                <div className="lg:hidden space-y-4">
                  {allUsers.map((user) => (
                    <div key={user.id} className="bg-white border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center space-x-3 mb-3">
                        <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                          <span className="text-sm font-medium text-gray-700">
                            {user.first_name[0]}{user.last_name[0]}
                          </span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-900">
                            {user.first_name} {user.last_name}
                          </div>
                          <div className="text-sm text-gray-500 truncate">
                            {user.email}
                          </div>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <span className="text-gray-500">Rola:</span>
                          <div className="mt-1">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              user.role === 'admin' ? 'bg-purple-100 text-purple-800' :
                              user.role === 'vsprint_employee' ? 'bg-blue-100 text-blue-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {getRoleLabel(user.role)}
                            </span>
                          </div>
                        </div>
                        
                        <div>
                          <span className="text-gray-500">ID:</span>
                          <div className="text-gray-900">{user.id}</div>
                        </div>
                        
                        <div className="col-span-2">
                          <span className="text-gray-500">Status:</span>
                          <div className="mt-1 flex flex-wrap gap-1">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                              {user.is_active ? 'Aktywny' : 'Nieaktywny'}
                            </span>
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              user.is_verified ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                            }`}>
                              {user.is_verified ? 'Zweryfikowany' : 'Niezweryfikowany'}
                            </span>
                            {user.role === 'user' && (
                              <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                user.admin_approved ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800'
                              }`}>
                                {user.admin_approved ? 'Zatwierdzony' : 'Oczekujący'}
                              </span>
                            )}
                          </div>
                        </div>
                        
                        <div className="col-span-2">
                          <span className="text-gray-500">Data rejestracji:</span>
                          <div className="text-gray-900">{formatDate(user.created_at)}</div>
                        </div>
                        
                        <div className="col-span-2 pt-2 border-t border-gray-100">
                          <span className="text-gray-500 text-sm">Akcje:</span>
                          <div className="mt-2 flex flex-wrap gap-2">
                            {user.role === 'user' && (
                              <button
                                onClick={() => openPermissionModal(user.id)}
                                className="inline-flex items-center px-2 py-1 border border-gray-300 text-xs leading-4 font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                              >
                                <Shield className="h-3 w-3 mr-1" />
                                Uprawnienia
                              </button>
                            )}
                            
                            <button
                              onClick={() => openUserManagementModal(user, 'info')}
                              className="inline-flex items-center px-2 py-1 border border-gray-300 text-xs leading-4 font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                            >
                              <Info className="h-3 w-3 mr-1" />
                              Info
                            </button>
                            
                            {/* Deactivate/Reactivate button - disabled for admin users */}
                            {user.role !== 'admin' && (
                              user.is_active ? (
                                <button
                                  onClick={() => openUserManagementModal(user, 'deactivate')}
                                  className="inline-flex items-center px-2 py-1 border border-orange-300 text-xs leading-4 font-medium rounded text-orange-700 bg-orange-50 hover:bg-orange-100"
                                >
                                  <UserX className="h-3 w-3 mr-1" />
                                  Dezaktywuj
                                </button>
                              ) : (
                                <button
                                  onClick={() => openUserManagementModal(user, 'reactivate')}
                                  className="inline-flex items-center px-2 py-1 border border-green-300 text-xs leading-4 font-medium rounded text-green-700 bg-green-50 hover:bg-green-100"
                                >
                                  <UserCheck className="h-3 w-3 mr-1" />
                                  Przywróć
                                </button>
                              )
                            )}
                            
                            {/* Delete button - disabled for admin users */}
                            {user.role !== 'admin' && (
                              <button
                                onClick={() => openUserManagementModal(user, 'delete')}
                                className="inline-flex items-center px-2 py-1 border border-red-300 text-xs leading-4 font-medium rounded text-red-700 bg-red-50 hover:bg-red-100"
                              >
                                <Trash2 className="h-3 w-3 mr-1" />
                                Usuń
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
                    <div className="flex-1 flex justify-between sm:hidden">
                      <button
                        onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                        disabled={currentPage <= 1}
                        className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Poprzednia
                      </button>
                      <button
                        onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
                        disabled={currentPage >= totalPages}
                        className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Następna
                      </button>
                    </div>
                    <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                      <div>
                        <p className="text-sm text-gray-700">
                          Wyświetlanie{' '}
                          <span className="font-medium">{(currentPage - 1) * perPage + 1}</span>
                          {' '}do{' '}
                          <span className="font-medium">
                            {Math.min(currentPage * perPage, totalUsers)}
                          </span>
                          {' '}z{' '}
                          <span className="font-medium">{totalUsers}</span> wyników
                        </p>
                      </div>
                      <div>
                        <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                          <button
                            onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                            disabled={currentPage <= 1}
                            className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            <ChevronLeft className="h-5 w-5" />
                          </button>
                          
                          {/* Page numbers */}
                          {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                            let pageNum;
                            if (totalPages <= 5) {
                              pageNum = i + 1;
                            } else if (currentPage <= 3) {
                              pageNum = i + 1;
                            } else if (currentPage >= totalPages - 2) {
                              pageNum = totalPages - 4 + i;
                            } else {
                              pageNum = currentPage - 2 + i;
                            }
                            
                            return (
                              <button
                                key={pageNum}
                                onClick={() => handlePageChange(pageNum)}
                                className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                                  pageNum === currentPage
                                    ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                                    : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                                }`}
                              >
                                {pageNum}
                              </button>
                            );
                          })}
                          
                          <button
                            onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
                            disabled={currentPage >= totalPages}
                            className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            <ChevronRight className="h-5 w-5" />
                          </button>
                        </nav>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Settings Tab */}
            {activeTab === 'settings' && (
              <div className="max-w-2xl">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Emaile powiadomień administratorów</h3>
                <p className="text-sm text-gray-600 mb-6">
                  Gdy nowy użytkownik zarejestruje się i zweryfikuje email, powiadomienie zostanie wysłane na wszystkie poniższe adresy.
                </p>
                
                <div className="space-y-4">
                  <div className="flex space-x-2">
                    <input
                      type="email"
                      value={newEmail}
                      onChange={(e) => setNewEmail(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && addNotificationEmail()}
                      placeholder="Dodaj nowy email..."
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                    <button
                      onClick={addNotificationEmail}
                      className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      Dodaj
                    </button>
                  </div>
                  
                  <div className="space-y-2">
                    {notificationEmails.length === 0 ? (
                      <div className="text-center py-8 text-gray-500">
                        <p>Brak skonfigurowanych emaili powiadomień</p>
                        <p className="text-sm">Dodaj pierwszy email powyżej</p>
                      </div>
                    ) : (
                      notificationEmails.map((email) => (
                        <div key={email} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                          <span className="text-sm text-gray-900">{email}</span>
                          <button
                            onClick={() => removeNotificationEmail(email)}
                            className="text-red-600 hover:text-red-800 text-sm font-medium"
                          >
                            Usuń
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Permission Management Modal */}
      {showPermissionModal && permissionUserId && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border max-w-4xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Zarządzanie uprawnieniami użytkownika
                </h3>
                <button
                  onClick={closePermissionModal}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="h-6 w-6" />
                </button>
              </div>
              
              <PermissionManager
                userId={permissionUserId}
                onPermissionsUpdated={() => {
                  loadData()
                  closePermissionModal()
                }}
                showTitle={false}
              />
            </div>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                <XCircle className="h-6 w-6 text-red-600" />
              </div>
              <div className="mt-3 text-center">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Odrzuć użytkownika
                </h3>
                <div className="mt-4">
                  <p className="text-sm text-gray-500 mb-4">
                    Czy na pewno chcesz odrzucić tego użytkownika? Ta akcja usunie konto i wyśle powiadomienie email.
                  </p>
                  <textarea
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                    placeholder="Opcjonalny powód odrzucenia..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-red-500 focus:border-red-500"
                    rows={3}
                  />
                </div>
                <div className="flex space-x-2 mt-4">
                  <button
                    onClick={() => {
                      setShowRejectModal(false)
                      setRejectionReason('')
                      setSelectedUserId(null)
                    }}
                    className="flex-1 px-4 py-2 bg-gray-300 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-400 focus:outline-none"
                  >
                    Anuluj
                  </button>
                  <button
                    onClick={rejectUser}
                    className="flex-1 px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-md hover:bg-red-700 focus:outline-none"
                  >
                    Odrzuć
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* User Management Modal */}
      {showUserManagementModal && selectedUser && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border max-w-4xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  {managementAction === 'info' && 'Informacje o użytkowniku'}
                  {managementAction === 'deactivate' && 'Dezaktywacja użytkownika'}
                  {managementAction === 'reactivate' && 'Przywrócenie użytkownika'}
                  {managementAction === 'delete' && 'Usunięcie użytkownika'}
                </h3>
                <button
                  onClick={closeUserManagementModal}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="h-6 w-6" />
                </button>
              </div>
              
              {/* User Basic Info */}
              <div className="bg-gray-50 p-4 rounded-lg mb-4">
                <div className="flex items-center space-x-3">
                  <div className="h-12 w-12 rounded-full bg-gray-300 flex items-center justify-center">
                    <span className="text-lg font-medium text-gray-700">
                      {selectedUser.first_name[0]}{selectedUser.last_name[0]}
                    </span>
                  </div>
                  <div>
                    <div className="text-lg font-medium text-gray-900">
                      {selectedUser.first_name} {selectedUser.last_name}
                    </div>
                    <div className="text-sm text-gray-500">{selectedUser.email}</div>
                    <div className="text-sm text-gray-500">
                      {getRoleLabel(selectedUser.role)} • ID: {selectedUser.id}
                    </div>
                  </div>
                </div>
                
                {/* Current Status */}
                <div className="mt-3 flex flex-wrap gap-2">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    selectedUser.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {selectedUser.is_active ? 'Aktywny' : 'Nieaktywny'}
                  </span>
                  {selectedUser.deactivated_at && (
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-orange-100 text-orange-800">
                      Dezaktywowany {formatDate(selectedUser.deactivated_at)}
                    </span>
                  )}
                </div>
                
                {selectedUser.deactivation_reason && (
                  <div className="mt-2 p-2 bg-yellow-50 border-l-4 border-yellow-400">
                    <p className="text-sm text-yellow-800">
                      <strong>Powód dezaktywacji:</strong> {selectedUser.deactivation_reason}
                    </p>
                  </div>
                )}
              </div>

              {/* User Info Tab */}
              {managementAction === 'info' && (
                <div>
                  {loadingUserInfo ? (
                    <div className="flex justify-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    </div>
                  ) : userManagementInfo ? (
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-blue-50 p-4 rounded-lg">
                          <div className="text-2xl font-bold text-blue-600">
                            {userManagementInfo.data_counts.accounts}
                          </div>
                          <div className="text-sm text-blue-800">Konta</div>
                        </div>
                        <div className="bg-green-50 p-4 rounded-lg">
                          <div className="text-2xl font-bold text-green-600">
                            {userManagementInfo.data_counts.templates}
                          </div>
                          <div className="text-sm text-green-800">Szablony</div>
                        </div>
                        <div className="bg-purple-50 p-4 rounded-lg">
                          <div className="text-2xl font-bold text-purple-600">
                            {userManagementInfo.data_counts.images}
                          </div>
                          <div className="text-sm text-purple-800">Zdjęcia</div>
                        </div>
                      </div>
                      
                      <div className="bg-white border border-gray-200 p-4 rounded-lg">
                        <h4 className="font-medium text-gray-900 mb-2">Status użytkownika</h4>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">Typ użytkownika:</span>
                            <div className="font-medium">{userManagementInfo.is_vsprint ? 'Pracownik vsprint' : 'Użytkownik zewnętrzny'}</div>
                          </div>
                          <div>
                            <span className="text-gray-500">Można usunąć:</span>
                            <div className={`font-medium ${userManagementInfo.can_delete ? 'text-green-600' : 'text-red-600'}`}>
                              {userManagementInfo.can_delete ? 'Tak' : 'Nie'}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      Nie udało się wczytać informacji o użytkowniku
                    </div>
                  )}
                </div>
              )}

              {/* Deactivate Tab */}
              {managementAction === 'deactivate' && (
                <div className="space-y-4">
                  <div className="bg-orange-50 border-l-4 border-orange-400 p-4">
                    <div className="flex items-start">
                      <AlertTriangle className="h-5 w-5 text-orange-400 mt-0.5 mr-2" />
                      <div>
                        <h4 className="text-orange-800 font-medium">Uwaga</h4>
                        <p className="text-orange-700 text-sm mt-1">
                          Dezaktywacja użytkownika spowoduje:
                        </p>
                        <ul className="text-orange-700 text-sm mt-2 list-disc list-inside">
                          <li>Natychmiastowe wylogowanie użytkownika</li>
                          <li>Uniemożliwienie logowania</li>
                          <li>Zachowanie wszystkich danych użytkownika</li>
                          <li>Możliwość późniejszego przywrócenia</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Powód dezaktywacji (opcjonalny)
                    </label>
                    <textarea
                      value={managementReason}
                      onChange={(e) => setManagementReason(e.target.value)}
                      placeholder="Podaj powód dezaktywacji użytkownika..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
                      rows={3}
                    />
                  </div>
                  
                  <div className="flex justify-end space-x-3">
                    <button
                      onClick={closeUserManagementModal}
                      disabled={isProcessing}
                      className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Anuluj
                    </button>
                    <button
                      onClick={handleDeactivateUser}
                      disabled={isProcessing}
                      className="px-4 py-2 bg-orange-600 text-white text-sm font-medium rounded-md hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center"
                    >
                      {isProcessing ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : null}
                      {isProcessing ? 'Dezaktywuję...' : 'Dezaktywuj użytkownika'}
                    </button>
                  </div>
                </div>
              )}

              {/* Reactivate Tab */}
              {managementAction === 'reactivate' && (
                <div className="space-y-4">
                  <div className="bg-green-50 border-l-4 border-green-400 p-4">
                    <div className="flex items-start">
                      <UserCheck className="h-5 w-5 text-green-400 mt-0.5 mr-2" />
                      <div>
                        <h4 className="text-green-800 font-medium">Przywrócenie użytkownika</h4>
                        <p className="text-green-700 text-sm mt-1">
                          Przywrócenie użytkownika spowoduje:
                        </p>
                        <ul className="text-green-700 text-sm mt-2 list-disc list-inside">
                          <li>Ponowne umożliwienie logowania</li>
                          <li>Usunięcie informacji o dezaktywacji</li>
                          <li>Wysłanie powiadomienia email do użytkownika</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex justify-end space-x-3">
                    <button
                      onClick={closeUserManagementModal}
                      disabled={isProcessing}
                      className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Anuluj
                    </button>
                    <button
                      onClick={handleReactivateUser}
                      disabled={isProcessing}
                      className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center"
                    >
                      {isProcessing ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : null}
                      {isProcessing ? 'Przywracam...' : 'Przywróć użytkownika'}
                    </button>
                  </div>
                </div>
              )}

              {/* Delete Tab */}
              {managementAction === 'delete' && (
                <div className="space-y-4">
                  <div className="bg-red-50 border-l-4 border-red-400 p-4">
                    <div className="flex items-start">
                      <AlertTriangle className="h-5 w-5 text-red-400 mt-0.5 mr-2" />
                      <div>
                        <h4 className="text-red-800 font-medium">Ostrzeżenie - Trwałe usunięcie</h4>
                        <p className="text-red-700 text-sm mt-1">
                          Ta operacja jest nieodwracalna! Spowoduje ona:
                        </p>
                        <ul className="text-red-700 text-sm mt-2 list-disc list-inside">
                          <li>Trwałe usunięcie konta użytkownika</li>
                          <li>Natychmiastowe wylogowanie</li>
                          <li>Archiwizację danych analitycznych</li>
                          <li>Wysłanie powiadomienia email</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {loadingUserInfo ? (
                    <div className="flex justify-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600"></div>
                    </div>
                  ) : userManagementInfo ? (
                    <>
                      {/* Data Overview */}
                      <div>
                        <h4 className="font-medium text-gray-900 mb-3">Dane użytkownika</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                          <div className="bg-blue-50 p-3 rounded-lg">
                            <div className="text-xl font-bold text-blue-600">
                              {userManagementInfo.data_counts.accounts}
                            </div>
                            <div className="text-sm text-blue-800">Konta</div>
                          </div>
                          <div className="bg-green-50 p-3 rounded-lg">
                            <div className="text-xl font-bold text-green-600">
                              {userManagementInfo.data_counts.templates}
                            </div>
                            <div className="text-sm text-green-800">Szablony</div>
                          </div>
                          <div className="bg-purple-50 p-3 rounded-lg">
                            <div className="text-xl font-bold text-purple-600">
                              {userManagementInfo.data_counts.images}
                            </div>
                            <div className="text-sm text-purple-800">Zdjęcia</div>
                          </div>
                        </div>
                      </div>

                      {/* Data Transfer Options (for vsprint users) */}
                      {userManagementInfo.is_vsprint && (
                        <div>
                          <h4 className="font-medium text-gray-900 mb-3">Opcje przenoszenia danych</h4>
                          <div className="bg-blue-50 p-4 rounded-lg space-y-3">
                            <p className="text-sm text-blue-800">
                              Jako pracownik vsprint, dane tego użytkownika mogą zostać przeniesione do Ciebie:
                            </p>
                            <div className="space-y-2">
                              <label className="flex items-center">
                                <input
                                  type="checkbox"
                                  checked={deleteOptions.keep_accounts}
                                  onChange={(e) => setDeleteOptions(prev => ({...prev, keep_accounts: e.target.checked}))}
                                  className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                                />
                                <span className="text-sm text-gray-700">
                                  Przejmij konta ({userManagementInfo.data_counts.accounts})
                                </span>
                              </label>
                              <label className="flex items-center">
                                <input
                                  type="checkbox"
                                  checked={deleteOptions.keep_templates}
                                  onChange={(e) => setDeleteOptions(prev => ({...prev, keep_templates: e.target.checked}))}
                                  className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                                />
                                <span className="text-sm text-gray-700">
                                  Przejmij szablony ({userManagementInfo.data_counts.templates})
                                </span>
                              </label>
                              <label className="flex items-center">
                                <input
                                  type="checkbox"
                                  checked={deleteOptions.keep_images}
                                  onChange={(e) => setDeleteOptions(prev => ({...prev, keep_images: e.target.checked}))}
                                  className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                                />
                                <span className="text-sm text-gray-700">
                                  Przejmij zdjęcia ({userManagementInfo.data_counts.images})
                                </span>
                              </label>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Reason */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Powód usunięcia (opcjonalny)
                        </label>
                        <textarea
                          value={managementReason}
                          onChange={(e) => setManagementReason(e.target.value)}
                          placeholder="Podaj powód usunięcia użytkownika..."
                          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-red-500 focus:border-red-500"
                          rows={3}
                        />
                      </div>

                      <div className="flex justify-end space-x-3">
                        <button
                          onClick={closeUserManagementModal}
                          disabled={isProcessing}
                          className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Anuluj
                        </button>
                        <button
                          onClick={handleDeleteUser}
                          disabled={isProcessing}
                          className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center"
                        >
                          {isProcessing ? (
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          ) : null}
                          {isProcessing ? 'Usuwam...' : 'Usuń użytkownika'}
                        </button>
                      </div>
                    </>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      Nie udało się wczytać informacji o użytkowniku
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Create User Modal */}
      <CreateUserModal
        isOpen={showCreateUserModal}
        onClose={() => setShowCreateUserModal(false)}
        onSuccess={() => {
          fetchAllUsers()
          if (activeTab === 'all') {
            setCurrentPage(1)
          }
        }}
      />
    </div>
  )
}
