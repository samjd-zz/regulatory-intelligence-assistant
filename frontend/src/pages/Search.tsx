import { useState } from 'react'
import { Search as SearchIcon } from 'lucide-react'
import { useSearchStore } from '@/store/searchStore'
import { ConfidenceBadge } from '@/components/shared/ConfidenceBadge'
import { FilterPanel } from '@/components/search/FilterPanel'
import { SearchSkeleton } from '@/components/shared/SearchSkeleton'
import { formatDate } from '@/lib/utils'

export function Search() {
  const { query, results, loading, error, search, total, processingTime } =
    useSearchStore()
  const [localQuery, setLocalQuery] = useState('')

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (localQuery.trim()) {
      search(localQuery)
    }
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">
        Search Regulations
      </h1>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="mb-8">
        <div className="flex gap-2">
          <input
            type="text"
            value={localQuery}
            onChange={(e) => setLocalQuery(e.target.value)}
            placeholder="Enter your question in plain language..."
            className="flex-1 rounded-lg border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Search regulations"
          />
          <button
            type="submit"
            disabled={loading || !localQuery.trim()}
            className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <SearchIcon className="w-5 h-5" />
            Search
          </button>
        </div>
      </form>

      {/* Grid Layout: Filters + Results */}
      <div className="grid grid-cols-12 gap-6">
        {/* Filter Sidebar - 3 columns */}
        <aside className="col-span-3">
          <FilterPanel />
        </aside>

        {/* Results Section - 9 columns */}
        <main className="col-span-9">
          {/* Results Count */}
          {!loading && !error && results.length > 0 && (
            <div className="mb-4 text-sm text-gray-600">
              Found <span className="font-semibold">{total}</span> results for "
              <span className="font-semibold">{query}</span>" in{' '}
              <span className="font-semibold">{processingTime}ms</span>
            </div>
          )}

          {/* Loading State */}
          {loading && <SearchSkeleton />}

          {/* Error State */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
              {error}
            </div>
          )}

          {/* Results */}
          {!loading && !error && results.length > 0 && (
            <div className="space-y-4">
              {results.map((result) => (
                <div
                  key={result.id}
                  className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-all duration-200 border border-transparent hover:border-blue-200"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {result.title}
                    </h3>
                    <ConfidenceBadge score={result.confidence} />
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{result.citation}</p>
                  <p className="text-gray-700 mb-4">{result.snippet}</p>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span className="font-medium">{result.jurisdiction}</span>
                      <span>•</span>
                      <span>{formatDate(result.effective_date)}</span>
                      <span>•</span>
                      <span className="capitalize">{result.document_type}</span>
                    </div>
                    <button
                      className="text-sm text-blue-600 hover:text-blue-700 font-medium hover:underline"
                      onClick={() => {
                        // TODO: Implement view details functionality
                        console.log('View details for:', result.id)
                      }}
                    >
                      View Details →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* No Results */}
          {!loading && !error && query && results.length === 0 && (
            <div className="text-center py-12 text-gray-600">
              No results found for "{query}". Try refining your search.
            </div>
          )}

          {/* Initial State */}
          {!loading && !error && !query && results.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <SearchIcon className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p className="text-lg font-medium mb-2">Search Regulations</p>
              <p className="text-sm">
                Enter a question or keywords to search across laws, regulations, and
                policies.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
