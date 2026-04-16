import React, { useState, useEffect } from 'react';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { useAuthStore } from '../../store/authStore';
import { api } from '../../lib/api';

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
  daily_stats: Array<{
    date: string;
    total_requests: number;
    total_input_tokens: number;
    total_output_tokens: number;
    total_cost_usd: string;
    operations_breakdown?: Record<string, number>;
  }>;
}

interface OverviewStats {
  this_month: {
    requests: number;
    input_tokens: number;
    output_tokens: number;
    total_cost: string;
  };
  last_month: {
    requests: number;
    total_cost: string;
  };
  comparison: {
    requests_change: number;
    cost_change: number;
  };
}

export default function Usage() {
  const { user } = useAuthStore();
  const [usageSummary, setUsageSummary] = useState<UsageSummary | null>(null);
  const [overviewStats, setOverviewStats] = useState<OverviewStats | null>(null);
  const [detailedUsage, setDetailedUsage] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [detailedLoading, setDetailedLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedOperation, setSelectedOperation] = useState<string>('');
  
  // Date range state
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  
  // Pagination state for detailed usage
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);
  const pageSize = 100;

  // Available operation types (from database)
  const operationTypes = [
    { value: '', label: 'Wszystkie Operacje' },
    { value: 'offer_update', label: 'Aktualizacje Ofert' },
    { value: 'bulk_update', label: 'Masowe Aktualizacje' },
    { value: 'template_generation', label: 'Generowanie Szablonów' },
    { value: 'template_create', label: 'Tworzenie Szablonów' },
    { value: 'offer_bulk_update_template', label: 'Masowa Aktualizacja Ofert z Szablonu' },
    { value: 'titles_bulk_edit', label: 'Masowa Edycja Tytułów' },
    { value: 'banners_bulk_generate', label: 'Masowe Generowanie Banerów' },
    { value: 'product_cards_bulk_generate', label: 'Masowe Generowanie Kart Produktów' }
  ];

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
    setCurrentPage(1); // Reset pagination when changing dates
  };

  useEffect(() => {
    // Set default to current month
    setDatePreset('current_month');
  }, []);

  useEffect(() => {
    if (startDate && endDate) {
      fetchUsageData();
      fetchOverviewStats();
    }
  }, [startDate, endDate, selectedOperation]);

  useEffect(() => {
    if (startDate && endDate) {
      fetchDetailedUsage();
    }
  }, [startDate, endDate, selectedOperation, currentPage]);

  const fetchUsageData = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
      });

      if (selectedOperation) {
        params.append('operation_type', selectedOperation);
      }

      const response = await api.get(`/analytics/token-usage/my-usage?${params}`);
      setUsageSummary(response.data);
    } catch (err) {
      console.error('Failed to fetch usage data:', err);
      setError('Nie udało się załadować danych użycia');
    } finally {
      setLoading(false);
    }
  };

  const fetchOverviewStats = async () => {
    try {
      const response = await api.get('/analytics/stats/overview');
      setOverviewStats(response.data);
    } catch (err) {
      console.error('Failed to fetch overview stats:', err);
    }
  };

  const fetchDetailedUsage = async () => {
    try {
      setDetailedLoading(true);
      const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
        limit: pageSize.toString(),
        offset: ((currentPage - 1) * pageSize).toString()
      });

      if (selectedOperation) {
        params.append('operation_type', selectedOperation);
      }

      const response = await api.get(`/analytics/token-usage/detailed?${params}`);
      setDetailedUsage(response.data);
      
      // For total records, we need to make a separate call or modify the backend
      // For now, we'll estimate based on the current page
      if (response.data.length === pageSize) {
        setTotalPages(currentPage + 1); // At least one more page
      } else {
        setTotalPages(currentPage);
      }
      setTotalRecords((currentPage - 1) * pageSize + response.data.length);
    } catch (err) {
      console.error('Failed to fetch detailed usage:', err);
    } finally {
      setDetailedLoading(false);
    }
  };

  const exportData = async (format: 'csv' | 'json') => {
    try {
      const params = new URLSearchParams({
        format,
        start_date: startDate,
        end_date: endDate,
      });

      if (selectedOperation) {
        params.append('operation_type', selectedOperation);
      }

      const response = await api.get(`/analytics/reports/usage-export?${params}`, {
        responseType: 'blob',
      });

      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `usage_report_${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export data:', err);
      setError('Nie udało się wyeksportować danych');
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

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center h-64">
          <div className="text-lg">Ładowanie danych użycia...</div>
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
    <div className="container mx-auto px-4 py-8 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Zużycie Tokenów AI</h1>
        <div className="flex gap-2">
          <Button
            onClick={() => exportData('csv')}
            variant="outline"
            className="text-sm"
          >
            Eksport CSV
          </Button>
          <Button
            onClick={() => exportData('json')}
            variant="outline"
            className="text-sm"
          >
            Eksport JSON
          </Button>
        </div>
      </div>

      {/* Overview Stats */}
      {overviewStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="text-sm text-gray-600">Żądania Ten Miesiąc</div>
            <div className="text-2xl font-bold">{overviewStats.this_month.requests}</div>
            <div className={`text-xs ${overviewStats.comparison.requests_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {overviewStats.comparison.requests_change >= 0 ? '+' : ''}{overviewStats.comparison.requests_change} vs poprzedni miesiąc
            </div>
          </Card>
          <Card className="p-4">
            <div className="text-sm text-gray-600">Tokeny Ten Miesiąc</div>
            <div className="text-2xl font-bold">
              {formatTokens(overviewStats.this_month.input_tokens + overviewStats.this_month.output_tokens)}
            </div>
            <div className="text-xs text-gray-500">
              {formatTokens(overviewStats.this_month.input_tokens)} in + {formatTokens(overviewStats.this_month.output_tokens)} out
            </div>
          </Card>
          <Card className="p-4">
            <div className="text-sm text-gray-600">Koszt Ten Miesiąc</div>
            <div className="text-2xl font-bold">{formatCost(overviewStats.this_month.total_cost)}</div>
            <div className={`text-xs ${overviewStats.comparison.cost_change >= 0 ? 'text-red-600' : 'text-green-600'}`}>
              {overviewStats.comparison.cost_change >= 0 ? '+' : ''}${overviewStats.comparison.cost_change.toFixed(4)} vs poprzedni miesiąc
            </div>
          </Card>
          <Card className="p-4">
            <div className="text-sm text-gray-600">Śr. Koszt/Żądanie</div>
            <div className="text-2xl font-bold">
              {overviewStats.this_month.requests > 0 
                ? formatCost((parseFloat(overviewStats.this_month.total_cost) / overviewStats.this_month.requests).toString())
                : '$0.0000'
              }
            </div>
          </Card>
        </div>
      )}

      {/* Date Range and Filters */}
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
                onChange={(e) => {
                  setStartDate(e.target.value);
                  setCurrentPage(1);
                }}
                className="border rounded px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Data Do</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => {
                  setEndDate(e.target.value);
                  setCurrentPage(1);
                }}
                className="border rounded px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Typ Operacji</label>
              <select
                value={selectedOperation}
                onChange={(e) => {
                  setSelectedOperation(e.target.value);
                  setCurrentPage(1);
                }}
                className="border rounded px-3 py-2"
              >
                {operationTypes.map(op => (
                  <option key={op.value} value={op.value}>{op.label}</option>
                ))}
              </select>
            </div>
            <div className="text-sm text-gray-600 mt-6">
              Zakres: {startDate} - {endDate}
            </div>
          </div>
        </div>
      </Card>

      {/* Usage Summary */}
      {usageSummary && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="p-6">
              <div className="text-sm text-gray-600">Łączne Żądania</div>
              <div className="text-3xl font-bold">{usageSummary.total_requests}</div>
              <div className="text-xs text-gray-500">{usageSummary.date_range}</div>
            </Card>
            <Card className="p-6">
              <div className="text-sm text-gray-600">Tokeny Wejściowe</div>
              <div className="text-3xl font-bold">{formatTokens(usageSummary.total_input_tokens)}</div>
            </Card>
            <Card className="p-6">
              <div className="text-sm text-gray-600">Tokeny Wyjściowe</div>
              <div className="text-3xl font-bold">{formatTokens(usageSummary.total_output_tokens)}</div>
            </Card>
            <Card className="p-6">
              <div className="text-sm text-gray-600">Łączny Koszt</div>
              <div className="text-3xl font-bold">{formatCost(usageSummary.total_cost_usd)}</div>
            </Card>
          </div>

          {/* Operation Breakdown */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Podział Operacji</h3>
            <div className="space-y-4">
              {Object.entries(usageSummary.operation_breakdown).map(([operation, data]) => (
                <div key={operation} className="flex justify-between items-center p-4 bg-gray-50 rounded">
                  <div>
                    <div className="font-medium capitalize">{operation.replace('_', ' ')}</div>
                    <div className="text-sm text-gray-600">
                      {data.count} żądań • {formatTokens(data.input_tokens)} wej + {formatTokens(data.output_tokens)} wyj
                    </div>
                  </div>
                  <div className="text-lg font-bold">{formatCost(data.total_cost)}</div>
                </div>
              ))}
            </div>
          </Card>

          {/* Daily Usage Chart */}
          {usageSummary.daily_stats.length > 0 && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Użycie Dzienne</h3>
              <div className="space-y-2">
                {usageSummary.daily_stats.slice(-14).map((day) => (
                  <div key={day.date} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <div>{new Date(day.date).toLocaleDateString()}</div>
                    <div className="flex gap-4 text-sm">
                      <span>{day.total_requests} żądań</span>
                      <span>{formatTokens(day.total_input_tokens + day.total_output_tokens)} tokenów</span>
                      <span className="font-bold">{formatCost(day.total_cost_usd)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Detailed Usage Records with Pagination */}
          <Card className="p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Szczegółowe Rekordy Użycia</h3>
              <div className="text-sm text-gray-600">
                Strona {currentPage} z {totalPages} | Łącznie rekordów: {totalRecords}
              </div>
            </div>
            
            {detailedLoading ? (
              <div className="text-center py-8">
                <div className="text-lg">Ładowanie szczegółowych danych...</div>
              </div>
            ) : (
              <>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {detailedUsage.map((record, index) => (
                    <div key={`${record.id}-${index}`} className="flex justify-between items-center p-3 bg-gray-50 rounded border-l-4 border-green-200">
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <div className="text-sm bg-green-100 text-green-800 px-2 py-1 rounded">
                            {record.operation_type}
                          </div>
                          <div className="text-sm text-gray-600">
                            {record.ai_provider} - {record.model_name}
                          </div>
                        </div>
                        <div className="text-sm text-gray-600 mt-1">
                          <span className="mr-4">Wej: {formatTokens(record.input_tokens)}</span>
                          <span className="mr-4">Wyj: {formatTokens(record.output_tokens)}</span>
                          <span className="text-green-600 font-medium">Koszt: {formatCost(record.total_cost_usd)}</span>
                        </div>
                      </div>
                      <div className="text-right text-sm">
                        <div className="text-gray-600">{new Date(record.request_timestamp).toLocaleString()}</div>
                      </div>
                    </div>
                  ))}
                  {detailedUsage.length === 0 && (
                    <div className="text-center text-gray-500 py-8">
                      Brak szczegółowych danych w wybranym okresie
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
    </div>
  );
}
