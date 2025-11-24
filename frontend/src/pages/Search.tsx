import { useState } from 'react'
import { Search as SearchIcon } from 'lucide-react'
import { useSearchStore } from '@/store/searchStore'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { ConfidenceBadge } from '@/components/shared/ConfidenceBadge'
import { formatDate } from '@/lib/utils'

export function Search() {
  const { query, results, loading, error, search, setQuery } = useSearchStore()
  const [localQuery, setLocalQuery] = useState('')

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (localQuery.trim()) {
      search(localQuery)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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

        {/* Results */}
        {loading && (
          <div className="flex justify-center py-12">
            <LoadingSpinner message="Searching regulations..." />
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
            {error}
          </div>
        )}

        {!loading && !error && results.length > 0 && (
          <div className="space-y-4">
            <p className="text-gray-600">
              Found {results.length} results for "{query}"
            </p>
            {results.map((result) => (
              <div
                key={result.id}
                className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {result.title}
                  </h3>
                  <ConfidenceBadge score={result.confidence} />
                </div>
                <p className="text-sm text-gray-600 mb-2">{result.citation}</p>
                <p className="text-gray-700 mb-4">{result.snippet}</p>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span>{result.jurisdiction}</span>
                  <span>•</span>
                  <span>{formatDate(result.effective_date)}</span>
                  <span>•</span>
                  <span className="capitalize">{result.document_type}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && !error && query && results.length === 0 && (
          <div className="text-center py-12 text-gray-600">
            No results found for "{query}". Try refining your search.
          </div>
        )}
      </div>
    </div>
  )
}
