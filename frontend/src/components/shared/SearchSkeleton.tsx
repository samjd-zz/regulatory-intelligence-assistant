export function SearchSkeleton() {
	return (
		<div className="space-y-4 animate-pulse">
			{[1, 2, 3].map((i) => (
				<div key={i} className="border-b border-slate-100 dark:border-zinc-800 pb-6">
					{/* Title skeleton */}
					<div className="flex items-center gap-3 mb-2">
						<div className="h-5 bg-slate-100 dark:bg-zinc-800 rounded w-20"></div>
						<div className="h-6 bg-slate-100 dark:bg-zinc-800 rounded w-2/3"></div>
					</div>

					{/* Snippet skeleton */}
					<div className="space-y-2 mb-2">
						<div className="h-4 bg-slate-100 dark:bg-zinc-800 rounded w-full"></div>
						<div className="h-4 bg-slate-100 dark:bg-zinc-800 rounded w-5/6"></div>
					</div>

					{/* Metadata skeleton */}
					<div className="h-3 bg-slate-100 dark:bg-zinc-800 rounded w-1/3"></div>
				</div>
			))}
		</div>
	);
}
