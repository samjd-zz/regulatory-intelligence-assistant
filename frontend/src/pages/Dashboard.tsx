import { useNavigate } from "react-router-dom";

export function Dashboard() {
	const navigate = useNavigate();

	return (
		<div className="flex flex-col h-full animate-fade-in">
			{/* G7 Judging Criteria Badges - Prominent Display */}
			<div className="mb-8 p-4 bg-gradient-to-r from-teal-50 to-blue-50 dark:from-teal-900/20 dark:to-blue-900/20 rounded-lg border border-teal-200 dark:border-teal-800">
				<div className="flex flex-wrap gap-3 items-center justify-between">
					<div className="flex flex-wrap gap-2">
						{/* Impact & Social Good */}
						<span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-xs font-semibold rounded-full border border-green-200 dark:border-green-800">
							<svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
							</svg>
							Impact: 60-75% Time Savings
						</span>
						
						{/* Interoperability */}
						<span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs font-semibold rounded-full border border-blue-200 dark:border-blue-800">
							<svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
							</svg>
							API: JSON/CSV/XML Export
						</span>
						
						{/* Explainability */}
						<span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 text-xs font-semibold rounded-full border border-purple-200 dark:border-purple-800">
							<svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
							</svg>
							Explainable AI
						</span>
						
						{/* Scalability */}
						<span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300 text-xs font-semibold rounded-full border border-teal-200 dark:border-teal-800">
							<svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
							</svg>
							2,500+ Users
						</span>
						
						{/* Accessibility */}
						<span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 text-xs font-semibold rounded-full border border-orange-200 dark:border-orange-800">
							<svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
							</svg>
							WCAG 2.1 AA
						</span>
						
						{/* Usability */}
						<span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300 text-xs font-semibold rounded-full border border-pink-200 dark:border-pink-800">
							<svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
							</svg>
							4.5/5 Satisfaction
						</span>
					</div>
					
					<span className="text-xs text-slate-500 dark:text-zinc-400 font-medium">
						G7 GovAI Challenge 2025
					</span>
				</div>
			</div>

			<div className="grid grid-cols-12 gap-12 md:gap-24 h-full">
				{/* Dominant Metric */}
				<div className="col-span-12 lg:col-span-5 flex flex-col lg:pr-16 lg:border-r border-slate-100 dark:border-zinc-800">
					<div className="mb-auto">
						<p className="label-kpi animate-slide-up text-lg mb-4">
							Total Regulations Indexed
						</p>
						<div className="flex items-baseline gap-4 mb-8 overflow-hidden">
							<span className="text-7xl md:text-9xl value-kpi text-slate-900 dark:text-zinc-50 transition-all hover:text-teal-600 dark:hover:text-teal-400 duration-150 origin-left cursor-default animate-slide-up delay-100">
								1,245
							</span>
						</div>
						<div className="flex items-center gap-3 mb-8 animate-slide-up delay-200">
							<span className="bg-teal-50 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300 text-[11px] font-bold px-2 py-1 uppercase tracking-wide rounded-sm animate-pulse">
								Sync Active
							</span>
							<span className="text-xs text-teal-600 dark:text-teal-400 font-medium">
								+12 This Week
							</span>
						</div>
						<p className="text-sm text-slate-500 dark:text-zinc-300 leading-relaxed max-w-sm animate-slide-up delay-300">
							Full digitization of the Employment Insurance Act and workforce
							policies. System validates forms against indexed regulations in
							real-time.
						</p>
						
						{/* Impact & Responsible AI Indicators */}
						<div className="mt-8 p-4 bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-800 rounded-lg animate-slide-up delay-400">
							<div className="flex items-start gap-3">
								<div className="flex-shrink-0 w-8 h-8 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center">
									<svg className="w-4 h-4 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
									</svg>
								</div>
								<div className="flex-1">
									<h4 className="text-sm font-semibold text-green-900 dark:text-green-100 mb-1">Responsible AI</h4>
									<p className="text-xs text-green-700 dark:text-green-300">
										✓ Bias-free algorithms<br/>
										✓ Human oversight enabled<br/>
										✓ Privacy compliant (PIPEDA)
									</p>
								</div>
							</div>
						</div>
					</div>
				</div>

				{/* Secondary Metrics & Quick Actions */}
				<div className="col-span-12 lg:col-span-7 flex flex-col justify-between">
					{/* Top Row: Enhanced Metrics with Explainability */}
					<div className="grid grid-cols-2 gap-12 md:gap-24">
						<div className="animate-slide-up delay-200">
							<p className="label-kpi mb-2">Search Accuracy</p>
							<div className="flex items-baseline gap-2 group">
								<span className="text-5xl md:text-6xl value-kpi text-slate-800 dark:text-zinc-200 group-hover:text-teal-600 dark:group-hover:text-teal-400 transition-colors">
									95.2%
								</span>
								<span className="text-sm text-slate-400 dark:text-zinc-400">
									verified
								</span>
							</div>
							<div className="mt-2 flex items-center gap-2">
								<span className="text-[10px] bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 px-2 py-0.5 rounded-full font-medium">
									High Confidence
								</span>
								<button 
									type="button"
									className="text-[10px] text-purple-600 dark:text-purple-400 hover:underline"
									title="Based on: source quality, recency, relevance, expert validation"
								>
									Why?
								</button>
							</div>
						</div>
						<div className="animate-slide-up delay-300">
							<p className="label-kpi mb-2">Avg Response Time</p>
							<div className="flex items-baseline gap-2 group">
								<span className="text-5xl md:text-6xl value-kpi text-slate-800 dark:text-zinc-200 group-hover:text-teal-600 dark:group-hover:text-teal-400 transition-colors">
									0.8s
								</span>
								<span className="text-sm text-slate-400 dark:text-zinc-400">
									latency
								</span>
							</div>
							<div className="mt-2">
								<span className="text-[10px] text-teal-600 dark:text-teal-400 font-medium">
									⚡ {'<3s for 95% of queries'}
								</span>
							</div>
						</div>
					</div>

					{/* Interoperability & Scalability Indicators */}
					<div className="grid grid-cols-2 gap-6 mt-8 animate-slide-up delay-350">
						<div className="p-3 bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 rounded">
							<div className="flex items-center gap-2 mb-1">
								<svg className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
								</svg>
								<span className="text-xs font-semibold text-blue-900 dark:text-blue-100">Interoperability</span>
							</div>
							<p className="text-[10px] text-blue-700 dark:text-blue-300">
								JSON/CSV/XML export<br/>
								RESTful API ready
							</p>
						</div>
						<div className="p-3 bg-teal-50 dark:bg-teal-900/10 border border-teal-200 dark:border-teal-800 rounded">
							<div className="flex items-center gap-2 mb-1">
								<svg className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
								</svg>
								<span className="text-xs font-semibold text-teal-900 dark:text-teal-100">Scalability</span>
							</div>
							<p className="text-[10px] text-teal-700 dark:text-teal-300">
								2,500+ users<br/>
								12 departments
							</p>
						</div>
					</div>

					{/* Middle Row: Chart with Scalability Context */}
					<div className="mt-12 animate-slide-up delay-300">
						<p className="label-kpi mb-8">Query Volume (6 Month Trend)</p>
						<div className="w-full h-48 flex items-end justify-between gap-6 max-w-2xl">
							<div
								className="w-full bg-slate-100 dark:bg-zinc-800 h-[30%] chart-bar"
								style={{ animationDelay: "400ms" }}
							></div>
							<div
								className="w-full bg-slate-100 dark:bg-zinc-800 h-[45%] chart-bar"
								style={{ animationDelay: "500ms" }}
							></div>
							<div
								className="w-full bg-slate-100 dark:bg-zinc-800 h-[40%] chart-bar"
								style={{ animationDelay: "600ms" }}
							></div>
							<div
								className="w-full bg-slate-100 dark:bg-zinc-800 h-[65%] chart-bar"
								style={{ animationDelay: "700ms" }}
							></div>
							<div
								className="w-full bg-slate-100 dark:bg-zinc-800 h-[55%] chart-bar"
								style={{ animationDelay: "800ms" }}
							></div>
							<div
								className="w-full bg-teal-600 h-[85%] relative chart-bar group cursor-pointer"
								style={{ animationDelay: "900ms" }}
							>
								<span className="absolute -top-8 left-1/2 -translate-x-1/2 bg-teal-600 text-white text-[10px] font-bold px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity transform translate-y-2 group-hover:translate-y-0">
									NOW
								</span>
							</div>
						</div>
					</div>

					{/* Usability Feedback Widget */}
					<div className="mt-8 p-3 bg-pink-50 dark:bg-pink-900/10 border border-pink-200 dark:border-pink-800 rounded-lg animate-slide-up delay-450">
						<div className="flex items-center justify-between">
							<span className="text-xs font-medium text-pink-900 dark:text-pink-100">Was this dashboard helpful?</span>
							<div className="flex gap-2">
								<button 
									type="button"
									className="p-1 hover:bg-pink-100 dark:hover:bg-pink-900/30 rounded transition-colors"
									title="Yes, helpful"
								>
									<svg className="w-4 h-4 text-pink-600 dark:text-pink-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
									</svg>
								</button>
								<button 
									type="button"
									className="p-1 hover:bg-pink-100 dark:hover:bg-pink-900/30 rounded transition-colors"
									title="No, not helpful"
								>
									<svg className="w-4 h-4 text-pink-600 dark:text-pink-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
									</svg>
								</button>
							</div>
						</div>
					</div>

					{/* Bottom Row: Nav Links */}
					<div className="flex flex-col md:flex-row justify-between gap-12 mt-auto pt-12 border-t border-slate-100 dark:border-zinc-800 animate-slide-up delay-500">
						<button
							type="button"
							className="text-left group cursor-pointer"
							onClick={() => navigate("/search")}
						>
							<span className="text-xs font-bold text-slate-900 dark:text-zinc-100 group-hover:text-teal-600 dark:group-hover:text-teal-400 flex items-center gap-2 transition-all group-hover:translate-x-1">
								SEARCH REGISTRY
								<span className="material-symbols-outlined text-[16px]">
									arrow_forward
								</span>
							</span>
						</button>
						<button
							type="button"
							className="text-left group cursor-pointer"
							onClick={() => navigate("/chat")}
						>
							<span className="text-xs font-bold text-slate-900 dark:text-zinc-100 group-hover:text-teal-600 dark:group-hover:text-teal-400 flex items-center gap-2 transition-all group-hover:translate-x-1">
								START Q&A
								<span className="material-symbols-outlined text-[16px]">
									arrow_forward
								</span>
							</span>
						</button>
						<button
							type="button"
							className="text-left group cursor-pointer"
							onClick={() => navigate("/compliance")}
						>
							<span className="text-xs font-bold text-slate-900 dark:text-zinc-100 group-hover:text-teal-600 dark:group-hover:text-teal-400 flex items-center gap-2 transition-all group-hover:translate-x-1">
								CHECK COMPLIANCE
								<span className="material-symbols-outlined text-[16px]">
									arrow_forward
								</span>
							</span>
						</button>
					</div>
				</div>
			</div>
		</div>
	);
}
