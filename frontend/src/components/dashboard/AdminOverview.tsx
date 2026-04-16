import React from 'react'
import { Link } from 'react-router-dom'
import { Users, Clock, AlertCircle } from 'lucide-react'

interface AdminOverviewProps {
  stats: any
  isLoading: boolean
}

export const AdminOverview: React.FC<AdminOverviewProps> = ({ stats, isLoading }) => {
  if (isLoading) {
    return (
      <div className="animate-pulse bg-white rounded-xl p-6 border border-gray-200 h-24">
        <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="h-8 bg-gray-200 rounded w-1/2"></div>
      </div>
    )
  }

  if (!stats?.user_stats?.pending_approval) return null

  const pendingCount = stats.user_stats.pending_approval

  return (
    <div className="bg-orange-50 rounded-xl border border-orange-200 p-6 transition-all hover:shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex gap-4">
          <div className="p-3 bg-orange-100 rounded-lg text-orange-600">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Wymagane działanie administratora
            </h3>
            <p className="text-gray-600 mt-1">
              {pendingCount} {pendingCount === 1 ? 'użytkownik oczekuje' : 'użytkowników oczekuje'} na zatwierdzenie dostępu do systemu.
            </p>
            <div className="mt-4">
              <Link
                to="/admin/users"
                className="inline-flex items-center gap-2 px-4 py-2 bg-orange-600 text-white text-sm font-medium rounded-lg hover:bg-orange-700 transition-colors"
              >
                <Users className="w-4 h-4" />
                Zarządzaj użytkownikami
              </Link>
            </div>
          </div>
        </div>
        
        <div className="hidden md:block">
          <div className="flex items-center gap-2 text-orange-700 bg-orange-100 px-3 py-1 rounded-full text-xs font-medium">
            <Clock className="w-3 h-3" />
            Oczekujące wnioski
          </div>
        </div>
      </div>
    </div>
  )
}
