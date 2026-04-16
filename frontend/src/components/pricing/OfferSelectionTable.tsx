import { useState } from 'react'

interface Offer {
  id: string;
  name: string;
  price: string;
}

interface Props {
  offers: Offer[];
  selectedOffers: Set<string>;
  onSelectionChange: (selected: Set<string>) => void;
}

export default function OfferSelectionTable({ offers, selectedOffers, onSelectionChange }: Props) {
  const [searchTerm, setSearchTerm] = useState('')

  const filteredOffers = offers.filter(offer =>
    offer.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    offer.id.includes(searchTerm)
  )

  const toggleOffer = (offerId: string) => {
    const newSelected = new Set(selectedOffers)
    if (newSelected.has(offerId)) {
      newSelected.delete(offerId)
    } else {
      newSelected.add(offerId)
    }
    onSelectionChange(newSelected)
  }

  const toggleAll = () => {
    if (selectedOffers.size === filteredOffers.length) {
      onSelectionChange(new Set())
    } else {
      onSelectionChange(new Set(filteredOffers.map(o => o.id)))
    }
  }

  return (
    <div>
      <div className="flex items-center gap-4 mb-4">
        <input
          type="text"
          placeholder="Szukaj oferty..."
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={toggleAll}
          className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition"
        >
          {selectedOffers.size === filteredOffers.length ? 'Odznacz wszystkie' : 'Zaznacz wszystkie'}
        </button>
      </div>

      <div className="border border-gray-300 rounded-lg overflow-hidden">
        <div className="max-h-96 overflow-y-auto">
          <table className="w-full">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="p-3 text-left w-10 border-b border-gray-300"></th>
                <th className="p-3 text-left border-b border-gray-300 font-semibold text-gray-700">Nazwa oferty</th>
                <th className="p-3 text-left border-b border-gray-300 font-semibold text-gray-700">ID</th>
                <th className="p-3 text-right border-b border-gray-300 font-semibold text-gray-700">Aktualna cena</th>
              </tr>
            </thead>
            <tbody>
              {filteredOffers.length === 0 && (
                <tr>
                  <td colSpan={4} className="p-8 text-center text-gray-500">
                    Brak ofert do wyświetlenia
                  </td>
                </tr>
              )}
              {filteredOffers.map(offer => (
                <tr
                  key={offer.id}
                  className={`border-t border-gray-200 cursor-pointer hover:bg-gray-50 transition ${
                    selectedOffers.has(offer.id) ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => toggleOffer(offer.id)}
                >
                  <td className="p-3">
                    <input
                      type="checkbox"
                      checked={selectedOffers.has(offer.id)}
                      onChange={() => toggleOffer(offer.id)}
                      className="w-4 h-4 cursor-pointer"
                    />
                  </td>
                  <td className="p-3">{offer.name}</td>
                  <td className="p-3 text-gray-500 text-sm">{offer.id}</td>
                  <td className="p-3 text-right font-medium">{offer.price} PLN</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-2 text-sm text-gray-600">
        Wybrano: <strong>{selectedOffers.size}</strong> / {filteredOffers.length}
      </div>
    </div>
  )
}
