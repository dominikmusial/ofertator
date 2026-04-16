import { useState } from 'react'

interface WeekSchedule {
  monday: number[];
  tuesday: number[];
  wednesday: number[];
  thursday: number[];
  friday: number[];
  saturday: number[];
  sunday: number[];
}

interface Props {
  value: WeekSchedule;
  onChange: (schedule: WeekSchedule) => void;
}

export default function WeeklyScheduleGrid({ value, onChange }: Props) {
  const [isDragging, setIsDragging] = useState(false)
  const [selectionMode, setSelectionMode] = useState<'select' | 'deselect'>('select')

  const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'] as const
  const dayLabels = ['Pon', 'Wt', 'Śr', 'Czw', 'Pt', 'Sob', 'Nie']
  const hours = Array.from({ length: 24 }, (_, i) => i)

  const isSelected = (day: keyof WeekSchedule, hour: number) => {
    return value[day].includes(hour)
  }

  const toggleCell = (day: keyof WeekSchedule, hour: number) => {
    const newSchedule = { ...value }
    const hourIndex = newSchedule[day].indexOf(hour)

    if (hourIndex > -1) {
      newSchedule[day] = newSchedule[day].filter(h => h !== hour)
    } else {
      newSchedule[day] = [...newSchedule[day], hour].sort((a, b) => a - b)
    }

    onChange(newSchedule)
  }

  const handleMouseDown = (day: keyof WeekSchedule, hour: number) => {
    setIsDragging(true)
    const currentlySelected = isSelected(day, hour)
    setSelectionMode(currentlySelected ? 'deselect' : 'select')
    toggleCell(day, hour)
  }

  const handleMouseEnter = (day: keyof WeekSchedule, hour: number) => {
    if (!isDragging) return

    const currentlySelected = isSelected(day, hour)

    if (selectionMode === 'select' && !currentlySelected) {
      toggleCell(day, hour)
    } else if (selectionMode === 'deselect' && currentlySelected) {
      toggleCell(day, hour)
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  // Bulk selection functions
  const selectAll = () => {
    const newSchedule = {} as WeekSchedule
    days.forEach(day => {
      newSchedule[day] = hours
    })
    onChange(newSchedule)
  }

  const clearAll = () => {
    const newSchedule = {} as WeekSchedule
    days.forEach(day => {
      newSchedule[day] = []
    })
    onChange(newSchedule)
  }

  const selectWeekdays = () => {
    const newSchedule = { ...value }
    const weekdays: (keyof WeekSchedule)[] = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    weekdays.forEach(day => {
      newSchedule[day] = hours
    })
    onChange(newSchedule)
  }

  const selectTimeRange = (start: number, end: number) => {
    const newSchedule = { ...value }
    const range = Array.from({ length: end - start }, (_, i) => start + i)
    days.forEach(day => {
      const existing = newSchedule[day].filter(h => h < start || h >= end)
      newSchedule[day] = [...existing, ...range].sort((a, b) => a - b)
    })
    onChange(newSchedule)
  }

  const countSelected = () => {
    return days.reduce((sum, day) => sum + value[day].length, 0)
  }

  return (
    <div className="weekly-schedule-grid" onMouseUp={handleMouseUp} onMouseLeave={handleMouseUp}>
      {/* Toolbar */}
      <div className="flex gap-2 mb-4 flex-wrap">
        <button
          onClick={selectAll}
          className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 transition"
        >
          🗹 Zaznacz wszystko
        </button>
        <button
          onClick={clearAll}
          className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 transition"
        >
          ⬜ Wyczyść
        </button>
        <button
          onClick={selectWeekdays}
          className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 transition"
        >
          📅 Dni robocze (Pn-Pt)
        </button>
        <button
          onClick={() => selectTimeRange(8, 18)}
          className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 transition"
        >
          🕐 Godziny robocze (8-18)
        </button>
      </div>

      {/* Grid */}
      <div className="overflow-x-auto border rounded-lg">
        <table className="w-full border-collapse select-none">
          <thead>
            <tr>
              <th className="sticky top-0 bg-gray-50 border-b-2 border-gray-300 p-2 text-sm font-semibold text-gray-700 min-w-[60px]">
                Godz.
              </th>
              {dayLabels.map((label, i) => (
                <th
                  key={i}
                  className="sticky top-0 bg-gray-50 border-b-2 border-gray-300 p-2 text-sm font-semibold text-gray-700 min-w-[60px]"
                >
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {hours.map(hour => (
              <tr key={hour}>
                <td className="bg-gray-50 border border-gray-200 p-1 text-xs text-center text-gray-600 font-medium">
                  {hour.toString().padStart(2, '0')}:00
                </td>
                {days.map(day => {
                  const selected = isSelected(day, hour)
                  return (
                    <td
                      key={`${day}-${hour}`}
                      className={`border border-gray-200 cursor-pointer transition-colors ${
                        selected
                          ? 'bg-blue-500 hover:bg-blue-600'
                          : 'bg-white hover:bg-gray-100'
                      }`}
                      onMouseDown={() => handleMouseDown(day, hour)}
                      onMouseEnter={() => handleMouseEnter(day, hour)}
                      style={{ width: '60px', height: '36px' }}
                    >
                      <div className="flex items-center justify-center h-full text-lg">
                        {selected ? (
                          <span className="text-white">☑</span>
                        ) : (
                          <span className="text-gray-300">☐</span>
                        )}
                      </div>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Summary */}
      <div className="mt-3 p-2 bg-blue-50 rounded-md text-sm text-blue-800">
        Zaznaczone komórki: <strong>{countSelected()}</strong> / 168
      </div>
    </div>
  )
}
