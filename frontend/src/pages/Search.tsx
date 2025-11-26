import { useState } from "react";
import { useSearchStore } from "@/store/searchStore";
import { ConfidenceBadge } from "@/components/shared/ConfidenceBadge";
import { SearchSkeleton } from "@/components/shared/SearchSkeleton";
import { formatDate } from "@/lib/utils";

export function Search() {
	const { query, results, loading, error, search, total, processingTime } =
		useSearchStore();
	const [localQuery, setLocalQuery] = useState("");

	const handleSearch = (e: React.FormEvent) => {
		e.preventDefault();
		if (localQuery.trim()) {
			search(localQuery);
		}
	};

	return (
		<div className="flex flex-col h-full animate-fade-in">
			<div className="max-w-4xl mx-auto w-full pt-16 px-12">
				{/* Search Input */}
				<div className="mb-12 animate-slide-up">
					<p className="label-kpi mb-4">Semantic Search</p>
					<form onSubmit={handleSearch} className="relative group">
						<input
							type="text"
							id="search-input"
							value={localQuery}
							onChange={(e) => setLocalQuery(e.target.value)}
							placeholder="e.g. eligibility requirements for employment insurance..."
							className="w-full text-3xl font-light text-slate-900 border-b border-slate-200 pb-4 outline-none focus:border-teal-600 placeholder-slate-300 bg-transparent transition-all"
							aria-label="Search regulations"
						/>
						<button
							type="submit"
							disabled={loading || !localQuery.trim()}
							className="absolute right-0 bottom-4 text-slate-400 hover:text-teal-600 transition-transform hover:scale-110 active:scale-95 disabled:opacity-50"
						>
							<span className="material-symbols-outlined text-3xl">search</span>
						</button>
					</form>
				</div>

				{/* Filters */}
				<div className="grid grid-cols-2 gap-16 mb-16 animate-slide-up delay-100">
					<div>
						<p className="label-kpi mb-4">Jurisdiction</p>
						<div className="space-y-3">
							<label className="checkbox-wrapper group">
								<input
									type="checkbox"
									defaultChecked
									className="checkbox-custom"
								/>
								<span className="text-sm text-slate-600 group-hover:text-slate-900 transition-colors">
									Federal
								</span>
							</label>
							<label className="checkbox-wrapper group">
								<input type="checkbox" className="checkbox-custom" />
								<span className="text-sm text-slate-600 group-hover:text-slate-900 transition-colors">
									Provincial
								</span>
							</label>
							<label className="checkbox-wrapper group">
								<input type="checkbox" className="checkbox-custom" />
								<span className="text-sm text-slate-600 group-hover:text-slate-900 transition-colors">
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
								<span className="text-sm text-slate-600 group-hover:text-slate-900 transition-colors">
									Act
								</span>
							</label>
							<label className="checkbox-wrapper group">
								<input
									type="checkbox"
									defaultChecked
									className="checkbox-custom"
								/>
								<span className="text-sm text-slate-600 group-hover:text-slate-900 transition-colors">
									Regulation
								</span>
							</label>
							<label className="checkbox-wrapper group">
								<input type="checkbox" className="checkbox-custom" />
								<span className="text-sm text-slate-600 group-hover:text-slate-900 transition-colors">
									Policy
								</span>
							</label>
						</div>
					</div>
				</div>

				{/* Results */}
				<div className="border-t border-slate-100 pt-8 animate-slide-up delay-200">
					{/* Results Count */}
					{!loading && !error && results.length > 0 && (
						<div className="mb-6 text-xs text-slate-500 uppercase tracking-wide">
							Found{" "}
							<span className="font-semibold text-slate-700">{total}</span>{" "}
							results for "
							<span className="font-semibold text-slate-700">{query}</span>" in{" "}
							<span className="font-semibold text-teal-600">
								{processingTime}ms
							</span>
						</div>
					)}

					{/* Loading State */}
					{loading && <SearchSkeleton />}

					{/* Error State */}
					{error && (
						<div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800 animate-scale-in">
							{error}
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
										<span className="text-[10px] font-bold bg-slate-100 text-slate-500 px-1 py-0.5 rounded transition-colors group-hover:bg-teal-50 group-hover:text-teal-600 uppercase">
											{result.jurisdiction} {result.document_type}
										</span>
										<h3 className="text-lg font-medium text-teal-700 group-hover:underline transition-all">
											{result.title}
										</h3>
										<ConfidenceBadge score={result.confidence} />
									</div>
									<p className="text-sm text-slate-500 leading-relaxed max-w-3xl transition-colors group-hover:text-slate-600">
										{result.snippet}
									</p>
									<p className="text-xs text-slate-400 mt-2">
										{result.citation} • {formatDate(result.effective_date)}
									</p>
								</div>
							))}
						</div>
					)}

					{/* No Results */}
					{!loading && !error && query && results.length === 0 && (
						<div className="text-center py-12 text-slate-600 animate-scale-in">
							No results found for "{query}". Try refining your search.
						</div>
					)}

					{/* Initial State */}
					{!loading && !error && !query && results.length === 0 && (
						<div className="text-center py-12 opacity-40 animate-scale-in">
							<span className="material-symbols-outlined text-4xl text-slate-300 mb-2 animate-bounce">
								manage_search
							</span>
							<p className="text-sm text-slate-400">Awaiting query...</p>
						</div>
					)}
				</div>
			</div>
		</div>
	);
}
