export function SearchSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-white rounded-lg shadow p-6">
          {/* Title skeleton */}
          <div className="flex items-start justify-between mb-2">
            <div className="h-6 bg-gray-200 rounded w-3/4"></div>
            <div className="h-6 bg-gray-200 rounded w-16"></div>
          </div>

          {/* Citation skeleton */}
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>

          {/* Snippet skeleton */}
          <div className="space-y-2 mb-4">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>

          {/* Metadata skeleton */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="h-4 bg-gray-200 rounded w-20"></div>
              <div className="h-4 bg-gray-200 rounded w-24"></div>
              <div className="h-4 bg-gray-200 rounded w-16"></div>
            </div>
            <div className="h-4 bg-gray-200 rounded w-24"></div>
          </div>
        </div>
      ))}
    </div>
  )
}
