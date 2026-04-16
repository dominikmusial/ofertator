interface ScheduleTypeSwitchProps {
  value: 'hourly' | 'daily'
  onChange: (value: 'hourly' | 'daily') => void
}

export default function ScheduleTypeSwitch({ value, onChange }: ScheduleTypeSwitchProps) {
  return (
    <div className="bg-white rounded-lg shadow p-4 mb-6">
      <div className="flex items-center justify-center gap-4">
        <label className="text-sm font-medium text-gray-700">Typ harmonogramu:</label>
        <div className="inline-flex rounded-lg border border-gray-300 bg-gray-50 p-1">
          <button
            type="button"
            onClick={() => onChange('hourly')}
            className={`
              px-6 py-2 text-sm font-medium rounded-md transition-all
              ${value === 'hourly'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
              }
            `}
          >
            Godzinowy
          </button>
          <button
            type="button"
            onClick={() => onChange('daily')}
            className={`
              px-6 py-2 text-sm font-medium rounded-md transition-all
              ${value === 'daily'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
              }
            `}
          >
            Dzienny (Import)
          </button>
        </div>
      </div>

      <div className="mt-3 text-center text-sm text-gray-500">
        {value === 'hourly' ? (
          <p>Ręczne tworzenie harmonogramów na podstawie godzin w tygodniu</p>
        ) : (
          <p>Import harmonogramów z pliku Excel/CSV na podstawie dni miesiąca (1-31)</p>
        )}
      </div>
    </div>
  )
}
