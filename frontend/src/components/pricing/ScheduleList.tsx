interface Schedule {
  id: number;
  offer_id: string;
  offer_name: string;
  sku?: string | null;
  original_price: string;
  scheduled_price: string;
  schedule_type: string;
  schedule_config?: { [key: string]: number[] };
  daily_schedule_config?: { days: number[] };
  is_active: boolean;
  current_price_state: string;
  last_price_update: string | null;
  created_at: string;
}

interface Props {
  schedules: Schedule[];
  onDelete: (scheduleId: number, restorePrice: boolean) => void;
  onRefresh: () => void;
}

export default function ScheduleList({ schedules, onDelete, onRefresh }: Props) {
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Nigdy'
    const date = new Date(dateStr)
    return date.toLocaleString('pl-PL')
  }

  const getStateLabel = (state: string) => {
    return state === 'scheduled' ? 'Cena harmonogramu' : 'Cena oryginalna'
  }

  const getStateBadge = (state: string) => {
    if (state === 'scheduled') {
      return <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">Aktywna</span>
    }
    return <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs font-medium rounded">Nieaktywna</span>
  }

  const getScheduleTypeBadge = (type: string) => {
    if (type === 'daily') {
      return <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs font-medium rounded">Dzienny</span>
    }
    return <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">Godzinowy</span>
  }

  const getScheduleInfo = (schedule: Schedule) => {
    if (schedule.schedule_type === 'daily' && schedule.daily_schedule_config) {
      const days = schedule.daily_schedule_config.days || []
      return `Dni miesiąca: ${days.join(', ')}`
    }
    // For hourly schedules, count total hours
    if (schedule.schedule_config) {
      const totalHours = Object.values(schedule.schedule_config).reduce(
        (sum, hours) => sum + hours.length,
        0
      )
      return `${totalHours} godzin/tydzień`
    }
    return 'Brak konfiguracji'
  }

  if (schedules.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 mb-4">Brak harmonogramów cen</p>
        <p className="text-sm text-gray-400">Utwórz nowy harmonogram w zakładce "Utwórz harmonogram"</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Harmonogramy cen ({schedules.length})</h2>
        <button
          onClick={onRefresh}
          className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 transition"
        >
          🔄 Odśwież
        </button>
      </div>

      <div className="space-y-3">
        {schedules.map(schedule => (
          <div
            key={schedule.id}
            className={`border rounded-lg p-4 ${
              schedule.is_active ? 'border-blue-300 bg-blue-50' : 'border-gray-300 bg-white'
            }`}
          >
            <div className="flex justify-between items-start mb-3">
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">{schedule.offer_name}</h3>
                <p className="text-sm text-gray-500">ID: {schedule.offer_id}</p>
                {schedule.sku && (
                  <p className="text-xs text-gray-400">SKU: {schedule.sku}</p>
                )}
              </div>
              <div className="flex items-center gap-2">
                {getScheduleTypeBadge(schedule.schedule_type)}
                {getStateBadge(schedule.current_price_state)}
                {schedule.is_active ? (
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                    Włączony
                  </span>
                ) : (
                  <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded">
                    Wyłączony
                  </span>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-3">
              <div>
                <p className="text-xs text-gray-500">Cena oryginalna</p>
                <p className="text-lg font-semibold text-gray-900">{schedule.original_price} PLN</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Cena w harmonogramie</p>
                <p className="text-lg font-semibold text-blue-600">{schedule.scheduled_price} PLN</p>
              </div>
            </div>

            <div className="text-sm text-gray-600 mb-3">
              <p>Harmonogram: <strong>{getScheduleInfo(schedule)}</strong></p>
              <p>Stan aktualny: <strong>{getStateLabel(schedule.current_price_state)}</strong></p>
              <p>Ostatnia zmiana: {formatDate(schedule.last_price_update)}</p>
              <p className="text-xs text-gray-400 mt-1">Utworzono: {formatDate(schedule.created_at)}</p>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => {
                  if (confirm('Czy chcesz przywrócić oryginalną cenę przed usunięciem?')) {
                    onDelete(schedule.id, true)
                  }
                }}
                className="px-3 py-1 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 transition"
              >
                Usuń (przywróć cenę)
              </button>
              <button
                onClick={() => {
                  if (confirm('Usunąć harmonogram BEZ przywracania ceny?')) {
                    onDelete(schedule.id, false)
                  }
                }}
                className="px-3 py-1 text-sm border border-red-600 text-red-600 rounded-md hover:bg-red-50 transition"
              >
                Usuń (zostaw cenę)
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
