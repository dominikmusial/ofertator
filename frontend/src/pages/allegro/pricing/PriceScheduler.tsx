import { useState } from 'react'
import { useAccountStore } from '../../../store/accountStore'
import { useActiveOffers } from '../../../hooks/shared/offers'
import { usePriceSchedules } from '../../../hooks/shared/pricing'
import { useCreatePriceSchedule } from '../../../hooks/shared/pricing'
import { useDeletePriceSchedule } from '../../../hooks/shared/pricing'
import AccountSelector from '../../../components/ui/AccountSelector'
import WeeklyScheduleGrid from '../../../components/pricing/WeeklyScheduleGrid'
import OfferSelectionTable from '../../../components/pricing/OfferSelectionTable'
import ScheduleList from '../../../components/pricing/ScheduleList'
import ScheduleTypeSwitch from '../../../components/pricing/ScheduleTypeSwitch'
import FileImportSection from '../../../components/pricing/FileImportSection'

interface WeekSchedule {
  monday: number[];
  tuesday: number[];
  wednesday: number[];
  thursday: number[];
  friday: number[];
  saturday: number[];
  sunday: number[];
}

export default function PriceScheduler() {
  const { current } = useAccountStore()
  const [activeTab, setActiveTab] = useState<'create' | 'manage'>('create')
  const [scheduleType, setScheduleType] = useState<'hourly' | 'daily'>('hourly')

  // Fetch offers
  const { data: offersData, isLoading: loadingOffers, refetch: refetchOffers } = useActiveOffers(current?.id)

  // Fetch schedules
  const { data: schedulesData, isLoading: loadingSchedules, refetch: refetchSchedules } = usePriceSchedules(current?.id)

  // Mutations
  const createMutation = useCreatePriceSchedule()
  const deleteMutation = useDeletePriceSchedule()

  // Form state
  const [selectedOffers, setSelectedOffers] = useState<Set<string>>(new Set())
  const [scheduledPrice, setScheduledPrice] = useState('')
  const [weekSchedule, setWeekSchedule] = useState<WeekSchedule>({
    monday: [],
    tuesday: [],
    wednesday: [],
    thursday: [],
    friday: [],
    saturday: [],
    sunday: []
  })

  const handleFetchOffers = () => {
    refetchOffers()
  }

  const handleCreateSchedule = async () => {
    if (!current?.id || selectedOffers.size === 0 || !scheduledPrice) {
      alert('Wypełnij wszystkie pola: wybierz oferty, ustaw cenę i zaznacz godziny')
      return
    }

    // Check if any hours are selected
    const totalHours = Object.values(weekSchedule).reduce((sum, hours) => sum + hours.length, 0)
    if (totalHours === 0) {
      alert('Zaznacz co najmniej jedną godzinę w harmonogramie')
      return
    }

    try {
      // Create schedule for each selected offer
      const offers = offersData?.offers || []
      const promises = Array.from(selectedOffers).map(offerId => {
        const offer = offers.find(o => o.id === offerId)
        if (!offer) return null

        return createMutation.mutateAsync({
          account_id: current.id,
          offer_id: offerId,
          offer_name: offer.name,
          scheduled_price: scheduledPrice,
          schedule_config: weekSchedule
        })
      })

      await Promise.all(promises.filter(p => p !== null))

      // Reset form
      setSelectedOffers(new Set())
      setScheduledPrice('')
      setWeekSchedule({
        monday: [],
        tuesday: [],
        wednesday: [],
        thursday: [],
        friday: [],
        saturday: [],
        sunday: []
      })

      // Switch to manage tab
      setActiveTab('manage')
      refetchSchedules()
    } catch (error) {
      console.error('Error creating schedules:', error)
    }
  }

  const handleDeleteSchedule = async (scheduleId: number, restorePrice: boolean = true) => {
    try {
      await deleteMutation.mutateAsync({
        schedule_id: scheduleId,
        restore_original: restorePrice
      })
      refetchSchedules()
    } catch (error) {
      console.error('Error deleting schedule:', error)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <h1 className="text-3xl font-bold mb-6 text-gray-900">Harmonogram Cen</h1>

      <AccountSelector />

      {!current && (
        <div className="mt-8 text-center text-gray-500 bg-gray-50 rounded-lg p-8">
          Wybierz konto aby zarządzać harmonogramem cen
        </div>
      )}

      {current && (
        <>
          {/* Schedule Type Switch */}
          <ScheduleTypeSwitch value={scheduleType} onChange={setScheduleType} />

          {/* Tabs */}
          <div className="flex gap-4 border-b border-gray-300 mb-6">
            <button
              className={`px-4 py-2 font-medium transition ${
                activeTab === 'create'
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
              onClick={() => setActiveTab('create')}
            >
              {scheduleType === 'hourly' ? 'Utwórz harmonogram' : 'Import z pliku'}
            </button>
            <button
              className={`px-4 py-2 font-medium transition ${
                activeTab === 'manage'
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
              onClick={() => setActiveTab('manage')}
            >
              Zarządzaj harmonogramami
            </button>
          </div>

          {/* Create Tab */}
          {activeTab === 'create' && scheduleType === 'hourly' && (
            <div className="space-y-8">
              {/* Step 1: Fetch and select offers */}
              <section className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-xl font-semibold mb-4 text-gray-900">Krok 1: Wybierz oferty</h2>

                <button
                  onClick={handleFetchOffers}
                  disabled={loadingOffers}
                  className="mb-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
                >
                  {loadingOffers ? 'Pobieranie...' : 'Pobierz aktywne oferty'}
                </button>

                {offersData && (
                  <OfferSelectionTable
                    offers={offersData.offers}
                    selectedOffers={selectedOffers}
                    onSelectionChange={setSelectedOffers}
                  />
                )}
              </section>

              {/* Step 2: Set scheduled price */}
              <section className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-xl font-semibold mb-4 text-gray-900">Krok 2: Ustaw cenę w harmonogramie</h2>

                <div className="max-w-xs">
                  <label className="block text-sm font-medium mb-2 text-gray-700">
                    Cena podczas harmonogramu (PLN)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={scheduledPrice}
                    onChange={e => setScheduledPrice(e.target.value)}
                    placeholder="np. 99.99"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Cena oryginalna zostanie automatycznie zapisana
                  </p>
                </div>
              </section>

              {/* Step 3: Configure schedule */}
              <section className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-xl font-semibold mb-4 text-gray-900">Krok 3: Zaznacz godziny</h2>

                <WeeklyScheduleGrid
                  value={weekSchedule}
                  onChange={setWeekSchedule}
                />
              </section>

              {/* Submit */}
              <div className="flex justify-end">
                <button
                  onClick={handleCreateSchedule}
                  disabled={selectedOffers.size === 0 || !scheduledPrice || createMutation.isPending}
                  className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium transition"
                >
                  {createMutation.isPending ? 'Tworzenie...' : 'Utwórz harmonogram'}
                </button>
              </div>
            </div>
          )}

          {/* Import Tab for Daily Schedules */}
          {activeTab === 'create' && scheduleType === 'daily' && (
            <FileImportSection
              accountId={current.id}
              onImportSuccess={() => {
                setActiveTab('manage')
                refetchSchedules()
              }}
            />
          )}

          {/* Manage Tab */}
          {activeTab === 'manage' && (
            <div className="bg-white p-6 rounded-lg shadow">
              {loadingSchedules && <div className="text-center py-8 text-gray-500">Ładowanie...</div>}

              {schedulesData && (
                <ScheduleList
                  schedules={schedulesData.schedules}
                  onDelete={handleDeleteSchedule}
                  onRefresh={refetchSchedules}
                />
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
