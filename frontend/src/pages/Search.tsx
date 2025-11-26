import { useState } from "react";
import { useSearchStore } from "@/store/searchStore";
import { ConfidenceBadge } from "@/components/shared/ConfidenceBadge";
import { SearchSkeleton } from "@/components/shared/SearchSkeleton";
import { formatDate } from "@/lib/utils";

export function Search() {
	const { query, results, loading, error, search, total, processingTime } =
		useSearchStore();
	const [localQuery, setLocalQuery] = useState("");
	const [showFilters, setShowFilters] = useState(false);

	const handleSearch = (e: React.FormEvent) => {
		e.preventDefault();
		if (localQuery.trim()) {
			search(localQuery);
			setShowFilters(false);
		}
	};

	return (
		<div className="flex flex-col h-full animate-fade-in">
			<div className="max-w-4xl mx-auto w-full pt-16 px-12">
				{/* Search Input */}
				<div
					className={`animate-slide-up transition-all duration-500 ease-[cubic-bezier(0.19,1,0.22,1)] ${
						showFilters ? "mb-12" : "mb-8"
					}`}
				>
					<p className="label-kpi mb-4">Semantic Search</p>
					<form onSubmit={handleSearch} className="relative group">
						<input
							type="text"
							id="search-input"
							value={localQuery}
							onChange={(e) => setLocalQuery(e.target.value)}
							placeholder="e.g. eligibility requirements for employment insurance..."
							className="w-full text-3xl font-light text-slate-900 dark:text-zinc-100 border-b border-slate-200 dark:border-zinc-800 pb-4 px-2 outline-none focus:border-teal-600 dark:focus:border-teal-500 placeholder-slate-300 dark:placeholder-zinc-600 bg-transparent transition-colors duration-300"
							aria-label="Search regulations"
						/>
						<button
							type="submit"
							disabled={loading || !localQuery.trim()}
							className="absolute right-2 bottom-4 text-slate-400 dark:text-zinc-500 hover:text-teal-600 dark:hover:text-teal-400 transition-transform hover:scale-110 active:scale-95 disabled:opacity-50"
						>
							<span className="material-symbols-outlined text-3xl">search</span>
						</button>
					</form>
				</div>

				{/* Filters */}
				<div
					className={`grid transition-[grid-template-rows] duration-500 ease-[cubic-bezier(0.19,1,0.22,1)] ${
						showFilters
							? "grid-rows-[1fr] opacity-100"
							: "grid-rows-[0fr] opacity-0"
					}`}
				>
					<div className="overflow-hidden">
						<div className="grid grid-cols-2 gap-16 mb-12">
							<div>
								<p className="label-kpi mb-4">Jurisdiction</p>
								<div className="space-y-3">
									<label className="checkbox-wrapper group">
										<input
											type="checkbox"
											defaultChecked
											className="checkbox-custom"
										/>
										<span className="text-sm text-slate-600 dark:text-zinc-400 group-hover:text-slate-900 dark:group-hover:text-zinc-200 transition-colors">
											Federal
										</span>
									</label>
									<label className="checkbox-wrapper group">
										<input type="checkbox" className="checkbox-custom" />
										<span className="text-sm text-slate-600 dark:text-zinc-400 group-hover:text-slate-900 dark:group-hover:text-zinc-200 transition-colors">
											Provincial
										</span>
									</label>
									<label className="checkbox-wrapper group">
										<input type="checkbox" className="checkbox-custom" />
										<span className="text-sm text-slate-600 dark:text-zinc-400 group-hover:text-slate-900 dark:group-hover:text-zinc-200 transition-colors">
											Municipal
										</span>
									</label>
								</div>
							</div>
							<div>
								<p className="label-kpi mb-4">Document Type</p>
								<div className="space-y-3">
									<label className="checkbox-wrapper group">
										<input
											type="checkbox"
											defaultChecked
											className="checkbox-custom"
										/>
										<span className="text-sm text-slate-600 dark:text-zinc-400 group-hover:text-slate-900 dark:group-hover:text-zinc-200 transition-colors">
											Act
										</span>
									</label>
									<label className="checkbox-wrapper group">
										<input
											type="checkbox"
											defaultChecked
											className="checkbox-custom"
										/>
										<span className="text-sm text-slate-600 dark:text-zinc-400 group-hover:text-slate-900 dark:group-hover:text-zinc-200 transition-colors">
											Regulation
										</span>
									</label>
									<label className="checkbox-wrapper group">
										<input type="checkbox" className="checkbox-custom" />
										<span className="text-sm text-slate-600 dark:text-zinc-400 group-hover:text-slate-900 dark:group-hover:text-zinc-200 transition-colors">
											Policy
										</span>
									</label>
								</div>
							</div>
						</div>
					</div>
				</div>

				{/* Toggle Filters Button */}
				<div className="flex justify-center mb-8 animate-fade-in">
					<button
						type="button"
						onClick={() => setShowFilters(!showFilters)}
						className="text-xs font-bold text-teal-600 dark:text-teal-400 uppercase tracking-wide hover:text-teal-700 dark:hover:text-teal-300 flex items-center gap-2 transition-colors"
					>
						{showFilters ? "Hide Filters" : "Show Filters"}
						<span
							className="material-symbols-outlined text-sm transition-transform duration-300"
							style={{
								transform: showFilters ? "rotate(180deg)" : "rotate(0deg)",
							}}
						>
							expand_more
						</span>
					</button>
				</div>

				{/* Results */}
				<div className="border-t border-slate-100 dark:border-zinc-800 pt-8 animate-slide-up delay-200">
					{/* Results Count */}
					{!loading && !error && results.length > 0 && (
						<div className="mb-6 text-xs text-slate-500 dark:text-zinc-500 uppercase tracking-wide">
							Found{" "}
							<span className="font-semibold text-slate-700 dark:text-zinc-300">
								{total}
							</span>{" "}
							results for "
							<span className="font-semibold text-slate-700 dark:text-zinc-300">
								{query}
							</span>
							" in{" "}
							<span className="font-semibold text-teal-600 dark:text-teal-400">
								{processingTime}ms
							</span>
						</div>
					)}

					{/* Loading State */}
					{loading && <SearchSkeleton />}

					{/* Error State */}
					{error && (
						<div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-800 dark:text-red-200 animate-scale-in flex items-start gap-3 mb-8">
							<span className="material-symbols-outlined text-red-500 dark:text-red-400 mt-0.5">
								error
							</span>
							<div>
								<p className="font-medium text-red-900 dark:text-red-100">
									Error
								</p>
								<p className="text-sm text-red-700 dark:text-red-300">
									{error}
								</p>
							</div>
						</div>
					)}

					{/* Results */}
					{!loading && !error && results.length > 0 && (
						<div className="grid grid-cols-1 gap-8">
							{results.map((result, idx) => (
								<div
									key={result.id}
									className="group cursor-pointer animate-slide-up"
									style={{ animationDelay: `${idx * 100}ms` }}
								>
									<div className="flex items-center gap-3 mb-2">
										<span className="text-[10px] font-bold bg-slate-100 dark:bg-zinc-800 text-slate-500 dark:text-zinc-400 px-1 py-0.5 rounded transition-colors group-hover:bg-teal-50 dark:group-hover:bg-teal-900/30 group-hover:text-teal-600 dark:group-hover:text-teal-400 uppercase">
											{result.jurisdiction} {result.document_type}
										</span>
										<h3 className="text-lg font-medium text-teal-700 dark:text-teal-400 group-hover:underline transition-all">
											{result.title}
										</h3>
										<ConfidenceBadge score={result.confidence} />
									</div>
									<p className="text-sm text-slate-500 dark:text-zinc-400 leading-relaxed max-w-3xl transition-colors group-hover:text-slate-600 dark:group-hover:text-zinc-300">
										{result.snippet}
									</p>
									<p className="text-xs text-slate-400 dark:text-zinc-500 mt-2">
										{result.citation} • {formatDate(result.effective_date)}
									</p>
								</div>
							))}
						</div>
					)}

					{/* No Results */}
					{!loading && !error && query && results.length === 0 && (
						<div className="flex flex-col items-center justify-center text-center py-12 animate-scale-in">
							<div className="relative mb-6 group cursor-default">
								<div className="absolute inset-0 bg-slate-100 dark:bg-zinc-800 rounded-full blur-xl opacity-40 group-hover:opacity-60 transition-opacity duration-500" />
								<span className="material-symbols-outlined text-6xl text-slate-300 dark:text-zinc-600 relative z-10 transition-transform duration-500 group-hover:scale-110">
									search_off
								</span>
							</div>
							<h3 className="text-lg font-medium text-slate-700 dark:text-zinc-300 mb-2">
								No results found
							</h3>
							<p className="text-sm text-slate-400 dark:text-zinc-500 max-w-[300px] leading-relaxed">
								We couldn't find any regulations matching "{query}". Try
								refining your search terms.
							</p>
						</div>
					)}

					{/* Initial State */}
					{!loading && !error && !query && results.length === 0 && (
						<div className="flex flex-col items-center justify-center text-center py-12 animate-scale-in">
							<div className="relative mb-6 group cursor-default">
								<div className="absolute inset-0 bg-teal-100 dark:bg-teal-900/20 rounded-full blur-xl opacity-20 group-hover:opacity-40 transition-opacity duration-500" />
								<span className="material-symbols-outlined text-6xl text-slate-300 dark:text-zinc-600 relative z-10 transition-transform duration-500 group-hover:scale-110 group-hover:text-teal-500/50 dark:group-hover:text-teal-400/50">
									manage_search
								</span>
							</div>
							<h3 className="text-lg font-medium text-slate-700 dark:text-zinc-300 mb-2">
								Ready to Search
							</h3>
							<p className="text-sm text-slate-400 dark:text-zinc-500 max-w-[250px] leading-relaxed">
								Enter keywords above to search through thousands of regulatory
								documents.
							</p>
						</div>
					)}
				</div>
			</div>
		</div>
	);
}
