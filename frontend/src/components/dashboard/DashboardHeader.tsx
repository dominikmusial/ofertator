import React from 'react'
import { User } from '../../store/authStore'
import { Shield, User as UserIcon, Briefcase } from 'lucide-react'

interface DashboardHeaderProps {
  user: User | null
  stats: {
    accountsCount: number
    featuresCount: number
  }
}

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({ user, stats }) => {
  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'admin':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-700 border border-purple-200">
            <Shield className="w-3 h-3" />
            Administrator
          </span>
        )
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200">
            <UserIcon className="w-3 h-3" />
            Użytkownik
          </span>
        )
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">
              Witaj, {user?.first_name}! 👋
            </h1>
            {user?.role && getRoleBadge(user.role)}
          </div>
          <p className="text-gray-500">
            Centrum zarządzania Twoimi ofertami i integracjami marketplace.
          </p>
        </div>

        <div className="flex items-center gap-4 border-t md:border-t-0 md:border-l border-gray-100 pt-4 md:pt-0 md:pl-6">
          <div className="px-4 py-2 bg-blue-50 rounded-lg border border-blue-100">
            <div className="text-2xl font-bold text-blue-600 leading-none">
              {stats.accountsCount}
            </div>
            <div className="text-xs font-medium text-blue-600/80 mt-1">
              Aktywne Konta
            </div>
          </div>
          <div className="px-4 py-2 bg-green-50 rounded-lg border border-green-100">
            <div className="text-2xl font-bold text-green-600 leading-none">
              {stats.featuresCount}
            </div>
            <div className="text-xs font-medium text-green-600/80 mt-1">
              Dostępne Funkcje
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
