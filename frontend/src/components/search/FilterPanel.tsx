import { useSearchStore } from '@/store/searchStore'
import { X } from 'lucide-react'

export function FilterPanel() {
  const { filters, updateFilters, clearFilters, search, query } = useSearchStore()

  const jurisdictions = [
    { value: 'federal', label: 'Federal' },
    { value: 'provincial', label: 'Provincial' },
    { value: 'municipal', label: 'Municipal' },
  ]

  const handleJurisdictionChange = (value: string, checked: boolean) => {
    const currentJurisdictions = filters.jurisdiction || []
    const newJurisdictions = checked
      ? [...currentJurisdictions, value]
      : currentJurisdictions.filter((j) => j !== value)

    updateFilters({ jurisdiction: newJurisdictions })
    
    // Re-search with new filters if there's an active query
    if (query) {
      search(query)
    }
  }


  const handleClearFilters = () => {
    clearFilters()
    
    // Re-search with cleared filters if there's an active query
    if (query) {
      search(query)
    }
  }

  const hasActiveFilters = 
    (filters.jurisdiction && filters.jurisdiction.length > 0) ||
    (filters.document_type && filters.document_type.length > 0)

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
        {hasActiveFilters && (
          <button
            onClick={handleClearFilters}
            className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            <X className="w-4 h-4" />
            Clear All
          </button>
        )}
      </div>

      {/* Jurisdiction Filters */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Jurisdiction</h3>
        <div className="space-y-2">
          {jurisdictions.map((jurisdiction) => (
            <label
              key={jurisdiction.value}
              className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-2 rounded"
            >
              <input
                type="checkbox"
                checked={filters.jurisdiction?.includes(jurisdiction.value) || false}
                onChange={(e) =>
                  handleJurisdictionChange(jurisdiction.value, e.target.checked)
                }
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">{jurisdiction.label}</span>
            </label>
          ))}
        </div>
      </div>

    </div>
  )
}
