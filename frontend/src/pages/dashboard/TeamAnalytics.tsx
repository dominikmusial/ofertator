import React, { useState, useEffect } from 'react';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { useAuthStore } from '../../store/authStore';
import { api } from '../../lib/api';

interface TeamActivitySummary {
  total_active_users: number;
  total_operations_today: number;
  total_cost_today: string;
  recent_activities: Array<{
    id: number;
    user_id: number;
    action_type: string;
    resource_type?: string;
    resource_id?: string;
    details?: any;
    timestamp: string;
    account_id?: number;
  }>;
  user_summaries: Array<{
    user_id: number;
    user_name: string;
    user_email: string;
    role: string;
    registration_source: string;
    key_source?: string;
    activity_count: number;
    ai_requests: number;
    cost: string;
    last_activity?: string;
  }>;
}

interface UsageSummary {
  total_requests: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_cost_usd: string;
  date_range: string;
  operation_breakdown: Record<string, {
    count: number;
    input_tokens: number;
    output_tokens: number;
    total_cost: string;
  }>;
}

export default function TeamAnalytics() {
  const { user } = useAuthStore();
  const [teamSummary, setTeamSummary] = useState<TeamActivitySummary | null>(null);
  const [selectedEmployee, setSelectedEmployee] = useState<number | null>(null);
  const [employeeUsage, setEmployeeUsage] = useState<UsageSummary | null>(null);
  const [employeeActivities, setEmployeeActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activitiesLoading, setActivitiesLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Date range state
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  
  // Filter state
  const [filters, setFilters] = useState({
    search: '',
    role: '',
    registration_source: '',
    key_source: '',
    show_zero_usage: true
  });
  
  // Pagination for users list
  const [userPage, setUserPage] = useState(1);
  const [userPageSize, setUserPageSize] = useState(10);
  
  // Pagination for activities
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const pageSize = 100;

  // Date preset functions
  const setDatePreset = (preset: string) => {
    const now = new Date();
    let start: Date, end: Date;

    switch (preset) {
      case 'current_month':
        start = new Date(now.getFullYear(), now.getMonth(), 1);
        end = new Date(); // Today's date, not end of month
        break;
      case 'previous_month':
        start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
        end = new Date(now.getFullYear(), now.getMonth(), 0);
        break;
      case 'last_30_days':
        end = new Date();
        start = new Date();
        start.setDate(start.getDate() - 30);
        break;
      case 'last_7_days':
        end = new Date();
        start = new Date();
        start.setDate(start.getDate() - 7);
        break;
      case 'last_90_days':
        end = new Date();
        start = new Date();
        start.setDate(start.getDate() - 90);
        break;
      case 'this_year':
        start = new Date(now.getFullYear(), 0, 1);
        end = new Date(now.getFullYear(), 11, 31);
        break;
      default:
        return;
    }

    setStartDate(start.toISOString().split('T')[0]);
    setEndDate(end.toISOString().split('T')[0]);
  };

  useEffect(() => {
    if (user?.role !== 'vsprint_employee' && user?.role !== 'admin') {
      setError('Brak dostępu. Wymagane uprawnienia menedżera.');
      return;
    }
    
    // Set default to current month
    setDatePreset('current_month');
  }, [user]);

  useEffect(() => {
    if (startDate && endDate) {
      fetchTeamData();
    }
  }, [startDate, endDate, filters.role, filters.registration_source, filters.key_source]);
  
  // Function to clear all filters
  const clearFilters = () => {
    setFilters({
      search: '',
      role: '',
      registration_source: '',
      key_source: '',
      show_zero_usage: true
    });
    setUserPage(1);
  };
  
  // Client-side filtering for search and zero usage
  const filteredUsers = teamSummary?.user_summaries.filter(user => {
    // Apply search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      if (!user.user_name.toLowerCase().includes(searchLower) && 
          !user.user_email.toLowerCase().includes(searchLower)) {
        return false;
      }
    }
    
    // Apply zero usage filter
    if (!filters.show_zero_usage && user.ai_requests === 0) {
      return false;
    }
    
    return true;
  }) || [];
  
  // Paginate filtered users
  const totalUserPages = Math.ceil(filteredUsers.length / userPageSize);
  const paginatedUsers = filteredUsers.slice(
    (userPage - 1) * userPageSize,
    userPage * userPageSize
  );

  useEffect(() => {
    if (selectedEmployee && startDate && endDate) {
      fetchEmployeeUsage(selectedEmployee);
      fetchEmployeeActivities(selectedEmployee);
    }
  }, [selectedEmployee, startDate, endDate, currentPage]);

  const fetchTeamData = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
      });
      
      // Add filter params
      if (filters.role) params.append('role', filters.role);
      if (filters.registration_source) params.append('registration_source', filters.registration_source);
      if (filters.key_source) params.append('key_source', filters.key_source);
      
      const response = await api.get(`/analytics/activity/team-activity?${params}`);
      setTeamSummary(response.data);
    } catch (err) {
      console.error('Failed to fetch team data:', err);
      setError('Nie udało się załadować danych zespołu');
    } finally {
      setLoading(false);
    }
  };





  const fetchEmployeeUsage = async (employeeId: number) => {
    try {
      const params = new URLSearchParams({
        employee_id: employeeId.toString(),
        start_date: startDate,
        end_date: endDate,
      });
      const response = await api.get(`/analytics/token-usage/team-usage?${params}`);
      setEmployeeUsage(response.data);
    } catch (err) {
      console.error('Failed to fetch employee usage:', err);
    }
  };

  const fetchEmployeeActivities = async (employeeId: number) => {
    try {
      setActivitiesLoading(true);
      const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
        limit: pageSize.toString(),
        offset: ((currentPage - 1) * pageSize).toString()
      });
      
      // Use team activity endpoint to get specific employee's activities
      const response = await api.get(`/analytics/activity/team-activity?employee_id=${employeeId}&${params}`);
      setEmployeeActivities(response.data.activities || []);
      
      // Calculate total pages based on total activities
      if (response.data.total_activities) {
        setTotalPages(Math.ceil(response.data.total_activities / pageSize));
      } else {
        // Fallback pagination logic
        if (response.data.activities && response.data.activities.length === pageSize) {
          setTotalPages(currentPage + 1);
        } else {
          setTotalPages(currentPage);
        }
      }
    } catch (err) {
      console.error('Failed to fetch employee activities:', err);
    } finally {
      setActivitiesLoading(false);
    }
  };

  const formatCost = (cost: string) => {
    return `$${parseFloat(cost).toFixed(4)}`;
  };

  const formatTokens = (tokens: number) => {
    if (tokens >= 1000000) {
      return `${(tokens / 1000000).toFixed(1)}M`;
    } else if (tokens >= 1000) {
      return `${(tokens / 1000).toFixed(1)}K`;
    }
    return tokens.toString();
  };

  const formatActionType = (actionType: string) => {
    // Polish translations for common action types
    const translations: Record<string, string> = {
      // Authentication
      'user_login': 'Logowanie',
      'user_logout': 'Wylogowanie',
      'user_register': 'Rejestracja',
      'user_google_login': 'Logowanie Google',
      'email_verify': 'Weryfikacja email',
      'password_reset': 'Reset hasła',
      'password_change': 'Zmiana hasła',
      
      // Templates
      'template_create': 'Utworzenie szablonu',
      'template_update': 'Aktualizacja szablonu',
      'template_delete': 'Usunięcie szablonu',
      'template_copy': 'Kopiowanie szablonu',
      
      // Offers
      'offer_bulk_update_template': 'Masowa aktualizacja ofert',
      'offer_restore_backup': 'Przywracanie oferty',
      'offer_copy': 'Kopiowanie ofert',
      'offer_generate_pdf': 'Generowanie PDF',
      'titles_bulk_edit': 'Edycja tytułów',
      'titles_pull_from_allegro': 'Pobieranie tytułów',
      'offers_status_change': 'Zmiana statusu ofert',
      'thumbnails_bulk_update': 'Aktualizacja miniatur',
      'banners_bulk_generate': 'Generowanie banerów',
      'product_cards_bulk_generate': 'Generowanie kart produktów',
      
      // Images
      'image_upload_general': 'Upload obrazu',
      'image_upload_account': 'Upload obrazu konta',
      'account_logo_set': 'Ustawienie logo',
      'account_fillers_set': 'Ustawienie wypełniaczy',
      
      // Promotions
      'promotion_create': 'Utworzenie promocji',
      'promotion_delete': 'Usunięcie promocji',
      'promotion_bundle_create': 'Utworzenie pakietu',
      
      // AI Configuration
      'ai_config_create': 'Konfiguracja AI',
      'ai_config_update': 'Aktualizacja konfiguracji AI',
      'ai_config_test_key': 'Test klucza AI',
      
      // System activities
      'system_login': 'Logowanie do systemu',
      'system_logout': 'Wylogowanie z systemu',
      'profile_update': 'Aktualizacja profilu',
      'settings_change': 'Zmiana ustawień',
      
      // Allegro
      'allegro_auth_start': 'Autoryzacja Allegro',
      'allegro_token_refresh': 'Odświeżenie tokena',
      'allegro_account_delete': 'Usunięcie konta Allegro',
    };
    
    return translations[actionType] || actionType.replace(/_/g, ' ').split(' ').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now.getTime() - time.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Przed chwilą';
    if (diffMins < 60) return `${diffMins} min temu`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} godz temu`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} dni temu`;
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center h-64">
          <div className="text-lg">Ładowanie analityki zespołu...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-red-600 text-center">{error}</div>
      </div>
    );
  }

  return (
    <div className="w-full space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Analityka Zespołu</h1>
        <Button onClick={() => { fetchTeamData(); }} variant="outline">
          Odśwież
        </Button>
      </div>

      {/* Date Range Filters */}
      <Card className="p-4">
        <div className="space-y-4">
          {/* Date Presets */}
          <div>
            <label className="block text-sm font-medium mb-2">Szybki Wybór Okresu</label>
            <div className="flex flex-wrap gap-2">
              <Button 
                onClick={() => setDatePreset('current_month')} 
                variant="outline" 
                size="sm"
                className="text-xs"
              >
                Bieżący Miesiąc
              </Button>
              <Button 
                onClick={() => setDatePreset('previous_month')} 
                variant="outline" 
                size="sm"
                className="text-xs"
              >
                Poprzedni Miesiąc
              </Button>
              <Button 
                onClick={() => setDatePreset('last_30_days')} 
                variant="outline" 
                size="sm"
                className="text-xs"
              >
                Ostatnie 30 dni
              </Button>
              <Button 
                onClick={() => setDatePreset('last_7_days')} 
                variant="outline" 
                size="sm"
                className="text-xs"
              >
                Ostatnie 7 dni
              </Button>
              <Button 
                onClick={() => setDatePreset('last_90_days')} 
                variant="outline" 
                size="sm"
                className="text-xs"
              >
                Ostatnie 90 dni
              </Button>
              <Button 
                onClick={() => setDatePreset('this_year')} 
                variant="outline" 
                size="sm"
                className="text-xs"
              >
                Ten Rok
              </Button>
            </div>
          </div>

          {/* Custom Date Range */}
          <div className="flex flex-wrap gap-4 items-center">
            <div>
              <label className="block text-sm font-medium mb-1">Data Od</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="border rounded px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Data Do</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="border rounded px-3 py-2"
              />
            </div>
            <div className="text-sm text-gray-600 mt-6">
              Zakres: {startDate} - {endDate}
            </div>
          </div>
        </div>
      </Card>

      {/* Team Overview */}
      {teamSummary && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="p-6">
              <div className="text-sm text-gray-600">Aktywni Użytkownicy</div>
              <div className="text-3xl font-bold">{teamSummary.total_active_users}</div>
            </Card>
            <Card className="p-6">
              <div className="text-sm text-gray-600">Łączne Operacje</div>
              <div className="text-3xl font-bold">{teamSummary.total_operations_today}</div>
            </Card>
            <Card className="p-6">
              <div className="text-sm text-gray-600">Łączny Koszt</div>
              <div className="text-3xl font-bold">{formatCost(teamSummary.total_cost_today)}</div>
            </Card>
          </div>

          {/* Filter Controls */}
          <Card className="p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Filtry</h3>
              <Button onClick={clearFilters} variant="outline" size="sm">
                Wyczyść filtry
              </Button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Search */}
              <div>
                <label className="block text-sm font-medium mb-1">Wyszukaj</label>
                <input
                  type="text"
                  placeholder="Imię, email..."
                  value={filters.search}
                  onChange={(e) => {
                    setFilters({...filters, search: e.target.value});
                    setUserPage(1);
                  }}
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              
              {/* Role Filter */}
              <div>
                <label className="block text-sm font-medium mb-1">Rola</label>
                <select
                  value={filters.role}
                  onChange={(e) => {
                    setFilters({...filters, role: e.target.value});
                    setUserPage(1);
                  }}
                  className="w-full border rounded px-3 py-2"
                >
                  <option value="">Wszyscy</option>
                  <option value="user">Użytkownicy Zewnętrzni</option>
                  <option value="vsprint_employee">Pracownicy Vsprint</option>
                  <option value="admin">Administratorzy</option>
                </select>
              </div>
              
              {/* Registration Source Filter */}
              <div>
                <label className="block text-sm font-medium mb-1">Źródło Rejestracji</label>
                <select
                  value={filters.registration_source}
                  onChange={(e) => {
                    setFilters({...filters, registration_source: e.target.value});
                    setUserPage(1);
                  }}
                  className="w-full border rounded px-3 py-2"
                >
                  <option value="">Wszystkie</option>
                  <option value="web">Web</option>
                  <option value="asystenciai">Asystenci AI</option>
                </select>
              </div>
              
              {/* Key Source Filter */}
              <div>
                <label className="block text-sm font-medium mb-1">Klucz API</label>
                <select
                  value={filters.key_source}
                  onChange={(e) => {
                    setFilters({...filters, key_source: e.target.value});
                    setUserPage(1);
                  }}
                  className="w-full border rounded px-3 py-2"
                >
                  <option value="">Wszystkie</option>
                  <option value="company_default">Klucz Firmowy</option>
                  <option value="user_custom">Własny Klucz</option>
                  <option value="none">Bez Konfiguracji</option>
                </select>
              </div>
            </div>
            
            {/* Zero Usage Toggle */}
            <div className="mt-4 flex items-center space-x-2">
              <input
                type="checkbox"
                id="show-zero-usage"
                checked={filters.show_zero_usage}
                onChange={(e) => {
                  setFilters({...filters, show_zero_usage: e.target.checked});
                  setUserPage(1);
                }}
                className="h-4 w-4"
              />
              <label htmlFor="show-zero-usage" className="text-sm">
                Pokaż użytkowników bez użycia AI
              </label>
            </div>
          </Card>
          
          {/* User List Table */}
          <Card className="overflow-hidden">
            <div className="flex justify-between items-center mb-4 px-6 pt-6">
              <h3 className="text-lg font-semibold">
                Użytkownicy ({filteredUsers.length})
              </h3>
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Pokaż:</span>
                <select
                  value={userPageSize}
                  onChange={(e) => {
                    setUserPageSize(Number(e.target.value));
                    setUserPage(1);
                  }}
                  className="border rounded px-2 py-1 text-sm"
                >
                  <option value="10">10</option>
                  <option value="25">25</option>
                  <option value="50">50</option>
                </select>
                    </div>
                  </div>
            
            <div className="overflow-x-auto px-6">
              <table className="w-full table-auto" style={{ minWidth: '800px' }}>
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-2 whitespace-nowrap">Nazwa</th>
                    <th className="text-left py-2 px-3 whitespace-nowrap">Email</th>
                    <th className="text-left py-2 px-3 whitespace-nowrap">Rola</th>
                    <th className="text-left py-2 px-3 whitespace-nowrap">Źródło</th>
                    <th className="text-left py-2 px-3 whitespace-nowrap">Klucz API</th>
                    <th className="text-right py-2 px-3 whitespace-nowrap">Aktywności</th>
                    <th className="text-right py-2 px-3 whitespace-nowrap">AI Zapytania</th>
                    <th className="text-right py-2 px-3 whitespace-nowrap">Koszt</th>
                    <th className="text-center py-2 px-3 whitespace-nowrap">Akcje</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedUsers.map((user) => (
                    <tr 
                      key={user.user_id}
                      className={`border-b hover:bg-gray-50 ${selectedEmployee === user.user_id ? 'bg-blue-50' : ''}`}
                    >
                      <td className="py-2 px-3 whitespace-nowrap">{user.user_name}</td>
                      <td className="py-2 px-3 text-sm text-gray-600">{user.user_email}</td>
                      <td className="py-2 px-3">
                        <span className="text-xs px-2 py-1 rounded bg-gray-100 whitespace-nowrap">
                          {user.role === 'user' ? 'Zewnętrzny' : user.role === 'vsprint_employee' ? 'Vsprint' : 'Admin'}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-sm whitespace-nowrap">{user.registration_source === 'web' ? 'Web' : 'Asystenci AI'}</td>
                      <td className="py-2 px-3">
                        {user.key_source === 'company_default' && <span className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-800 whitespace-nowrap">🔑 Firmowy</span>}
                        {user.key_source === 'user_custom' && <span className="text-xs px-2 py-1 rounded bg-green-100 text-green-800 whitespace-nowrap">👤 Własny</span>}
                        {user.key_source === 'none' && <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-600 whitespace-nowrap">❌ Brak</span>}
                      </td>
                      <td className="py-2 px-3 text-right">{user.activity_count}</td>
                      <td className="py-2 px-3 text-right">{user.ai_requests}</td>
                      <td className="py-2 px-3 text-right whitespace-nowrap">{formatCost(user.cost)}</td>
                      <td className="py-2 px-3 text-center">
                        <Button
                          size="sm"
                          variant={selectedEmployee === user.user_id ? "default" : "outline"}
                          onClick={() => {
                            setSelectedEmployee(user.user_id);
                            setCurrentPage(1);
                          }}
                        >
                          {selectedEmployee === user.user_id ? 'Wybrany' : 'Zobacz'}
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {filteredUsers.length === 0 && (
              <div className="text-center py-8 px-6 text-gray-500">
                Brak użytkowników spełniających kryteria
              </div>
            )}
            
            {/* User Pagination */}
            {totalUserPages > 1 && (
              <div className="flex justify-between items-center mt-4 pt-4 px-6 pb-6 border-t">
                <div className="text-sm text-gray-600">
                  Pokazuję {((userPage - 1) * userPageSize) + 1} - {Math.min(userPage * userPageSize, filteredUsers.length)} z {filteredUsers.length}
                </div>
                <div className="flex justify-center items-center gap-2">
                  <Button
                    onClick={() => setUserPage(prev => Math.max(1, prev - 1))}
                    disabled={userPage === 1}
                    variant="outline"
                    size="sm"
                  >
                    Poprzednia
                  </Button>
                  
                  {Array.from({ length: Math.min(5, totalUserPages) }, (_, i) => {
                    const pageNum = Math.max(1, Math.min(totalUserPages - 4, userPage - 2)) + i;
                    if (pageNum > totalUserPages) return null;
                    
                    return (
                      <Button
                        key={pageNum}
                        onClick={() => setUserPage(pageNum)}
                        variant={userPage === pageNum ? "default" : "outline"}
                        size="sm"
                      >
                        {pageNum}
                      </Button>
                    );
                  })}
                  
                  <Button
                    onClick={() => setUserPage(prev => Math.min(totalUserPages, prev + 1))}
                    disabled={userPage === totalUserPages}
                    variant="outline"
                    size="sm"
                  >
                    Następna
                  </Button>
                </div>
              </div>
            )}
          </Card>

          {/* Selected Employee Details */}
          {selectedEmployee && (
            <>
              {/* Employee Token Usage */}
              {employeeUsage && (
                <Card className="p-6">
                  <h3 className="text-lg font-semibold mb-4">
                    Użycie AI - {teamSummary.user_summaries.find(u => u.user_id === selectedEmployee)?.user_name}
                  </h3>
                  
                  {/* Stats Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="text-sm text-blue-600 font-medium">Łączne Żądania</div>
                      <div className="text-2xl font-bold text-blue-900">{employeeUsage.total_requests}</div>
                    </div>
                    <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                      <div className="text-sm text-green-600 font-medium">Tokeny Wejściowe</div>
                      <div className="text-2xl font-bold text-green-900">{formatTokens(employeeUsage.total_input_tokens)}</div>
                    </div>
                    <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                      <div className="text-sm text-purple-600 font-medium">Tokeny Wyjściowe</div>
                      <div className="text-2xl font-bold text-purple-900">{formatTokens(employeeUsage.total_output_tokens)}</div>
                    </div>
                    <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                      <div className="text-sm text-orange-600 font-medium">Łączny Koszt</div>
                      <div className="text-2xl font-bold text-orange-900">{formatCost(employeeUsage.total_cost_usd)}</div>
                    </div>
                  </div>
                  
                  {/* Operation Breakdown */}
                  {Object.keys(employeeUsage.operation_breakdown).length > 0 && (
                    <div className="space-y-3">
                      <h4 className="font-semibold text-gray-900">Podział Operacji AI</h4>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {Object.entries(employeeUsage.operation_breakdown).map(([operation, data]) => (
                          <div key={operation} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg border">
                            <div>
                              <div className="font-medium text-gray-900 capitalize">{operation.replace('_', ' ')}</div>
                              <div className="text-sm text-gray-600">
                                {data.count} żądań • {formatTokens(data.input_tokens)} wej + {formatTokens(data.output_tokens)} wyj
                              </div>
                            </div>
                            <div className="font-bold text-gray-900">{formatCost(data.total_cost)}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </Card>
              )}

              {/* Employee Activities */}
              <Card className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold">
                    Aktywność - {teamSummary.user_summaries.find(u => u.user_id === selectedEmployee)?.user_name}
                  </h3>
                  <div className="text-sm text-gray-600">
                    Strona {currentPage} z {totalPages}
                  </div>
                </div>
                
                {activitiesLoading ? (
                  <div className="text-center py-8">
                    <div className="text-lg">Ładowanie aktywności...</div>
                  </div>
                ) : (
                  <>
                    <div className="space-y-3 max-h-96 overflow-y-auto">
                      {employeeActivities.map((activity, index) => (
                        <div key={`${activity.id}-${index}`} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg border border-gray-200">
                          <div className="flex-1">
                            <div className="flex items-center gap-3">
                              <div className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">
                                {formatActionType(activity.action_type)}
                              </div>
                            </div>
                            <div className="text-sm text-gray-600 mt-1">
                              {activity.resource_type && (
                                <span className="mr-3">Typ: {activity.resource_type}</span>
                              )}
                              {activity.resource_id && (
                                <span className="mr-3">ID: {activity.resource_id}</span>
                              )}
                              {activity.details?.account_name && (
                                <span className="text-purple-600">Konto: {activity.details.account_name}</span>
                              )}
                            </div>
                            {activity.details && (
                              <div className="text-xs text-gray-500 mt-1">
                                {activity.details.duration_ms && `Czas: ${activity.details.duration_ms}ms`}
                                {activity.details.status_code && ` | Status: ${activity.details.status_code}`}
                                {activity.details.method && ` | ${activity.details.method}`}
                              </div>
                            )}
                          </div>
                          <div className="text-right text-sm">
                            <div className="text-gray-600">{formatTimestamp(activity.timestamp)}</div>
                            <div className="text-gray-500">{getTimeAgo(activity.timestamp)}</div>
                          </div>
                        </div>
                      ))}
                      {employeeActivities.length === 0 && (
                        <div className="text-center py-8">
                          <div className="text-gray-400 text-4xl mb-3">📋</div>
                          <div className="text-gray-500">Brak aktywności w wybranym okresie</div>
                        </div>
                      )}
                    </div>
                    
                    {/* Pagination */}
                    {totalPages > 1 && (
                      <div className="flex justify-center items-center gap-2 mt-6">
                        <Button
                          onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                          disabled={currentPage === 1}
                          variant="outline"
                          size="sm"
                        >
                          Poprzednia
                        </Button>
                        
                        {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                          const pageNum = Math.max(1, Math.min(totalPages - 4, currentPage - 2)) + i;
                          if (pageNum > totalPages) return null;
                          
                          return (
                            <Button
                              key={pageNum}
                              onClick={() => setCurrentPage(pageNum)}
                              variant={currentPage === pageNum ? "default" : "outline"}
                              size="sm"
                            >
                              {pageNum}
                            </Button>
                          );
                        })}
                        
                        <Button
                          onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                          disabled={currentPage === totalPages}
                          variant="outline"
                          size="sm"
                        >
                          Następna
                        </Button>
                      </div>
                    )}
                  </>
                )}
              </Card>
            </>
          )}

          {/* Instructions when no employee selected */}
          {!selectedEmployee && (
            <Card className="p-6">
              <div className="text-center py-12">
                <div className="text-gray-400 text-6xl mb-4">👆</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Wybierz Pracownika</h3>
                <p className="text-gray-600">
                  Kliknij na jednego z pracowników powyżej, aby zobaczyć jego szczegółową aktywność i użycie AI.
                </p>
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
