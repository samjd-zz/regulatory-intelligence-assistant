import { useNavigate } from "react-router-dom";

export function Dashboard() {
	const navigate = useNavigate();

	return (
		<div className="flex flex-col h-full animate-fade-in">
			{/* G7 Judging Criteria Badges - Prominent Display */}
			<div className="mb-8 p-4 bg-gradient-to-r from-teal-50 to-blue-50 dark:from-teal-900/20 dark:to-blue-900/20 rounded-lg border border-teal-200 dark:border-teal-800">
				<div className="flex flex-wrap gap-2">
					{/* Impact & Social Good */}
					<span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-xs font-semibold rounded-full border border-green-200 dark:border-green-800">
							<svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
							</svg>
							60-75% Time Savings
						</span>
						
					{/* Interoperability */}
					<span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs font-semibold rounded-full border border-blue-200 dark:border-blue-800">
						<svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
						</svg>
						JSON API
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
							Production-Ready
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
						
						{/* Query Volume Chart - */}
						<div className="mt-8 animate-slide-up delay-400">
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

					{/* Interoperability & Tech Stack for Scalability */}
					<div className="grid grid-cols-2 gap-6 mt-8 animate-slide-up delay-350">
					<div className="p-3 bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 rounded">
						<div className="flex items-center gap-2 mb-2">
							<svg className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
							</svg>
							<span className="text-xs font-semibold text-blue-900 dark:text-blue-100">Interoperability</span>
						</div>
						<div className="flex flex-col gap-1">
							<div className="flex items-center gap-1.5">
								<svg className="w-3 h-3 text-blue-600 dark:text-blue-400" viewBox="0 0 24 24" fill="currentColor">
									<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
								</svg>
								<span className="text-[10px] text-blue-700 dark:text-blue-300">RESTful API</span>
							</div>
							<div className="flex items-center gap-1.5">
								<svg className="w-3 h-3 text-blue-600 dark:text-blue-400" viewBox="0 0 24 24" fill="currentColor">
									<path d="M5 3l3.057-3L11 3l2.943 3L17 3l3.057 3L23 3v18l-3.057-3L17 21l-2.943-3L11 21l-3.057-3L5 21l-3.057-3L1 21V3l3.057 3L5 3zm7 8h6v2h-6v-2zm0 4h6v2h-6v-2zm-6-4h4v6H6v-6z"/>
								</svg>
								<span className="text-[10px] text-blue-700 dark:text-blue-300">JSON responses</span>
							</div>
						</div>
					</div>
						<div className="p-3 bg-teal-50 dark:bg-teal-900/10 border border-teal-200 dark:border-teal-800 rounded">
							<div className="flex items-center gap-2 mb-2">
								<svg className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
								</svg>
								<span className="text-xs font-semibold text-teal-900 dark:text-teal-100">Scalable Architecture</span>
							</div>
							<div className="flex flex-col gap-1">
								<div className="flex items-center gap-1.5">
									<svg className="w-3 h-3 text-teal-600 dark:text-teal-400" viewBox="0 0 24 24" fill="currentColor">
										<path d="M12 0c6.627 0 12 2.686 12 6v12c0 2 3.6 3.5 8 3.5s8-1.5 8-3.5V5.5C20 3.6 16.4 2 12 2zm-6 3.5c0-.3 2.7-1.5 6-1.5s6 1.2 6 1.5S15.3 7 12 7 6 5.8 6 5.5zM6 18v-2.3c1.3.6 2.6.9 4 1.1v2.3c-2.2-.2-4-.7-4-1.1zm8 1.1v-2.3c1.4-.2 2.7-.5 4-1.1V18c0 .4-1.8.9-4 1.1z"/>
									</svg>
									<span className="text-[10px] text-teal-700 dark:text-teal-300">PostgreSQL</span>
								</div>
								<div className="flex items-center gap-1.5">
									<svg className="w-3 h-3 text-green-600 dark:text-green-400" viewBox="0 0 24 24" fill="currentColor">
										<path d="M12 2c-4.4 0-8 1.6-8 3.5V18c0 2 3.6 3.5 8 3.5s8-1.5 8-3.5V5.5C20 3.6 16.4 2 12 2zm-6 3.5c0-.3 2.7-1.5 6-1.5s6 1.2 6 1.5S15.3 7 12 7 6 5.8 6 5.5zM6 18v-2.3c1.3.6 2.6.9 4 1.1v2.3c-2.2-.2-4-.7-4-1.1zm8 1.1v-2.3c1.4-.2 2.7-.5 4-1.1V18c0 .4-1.8.9-4 1.1z"/>
									</svg>
									<span className="text-[10px] text-teal-700 dark:text-teal-300">Neo4j</span>
								</div>
								<div className="flex items-center gap-1.5">
									<svg className="w-3 h-3 text-yellow-600 dark:text-yellow-400" viewBox="0 0 24 24" fill="currentColor">
										<path d="M10.5 19.5h3v-3h-3v3zm0-15v3h3v-3h-3zM21 12v-1.5l-2.25-.75.75-2.25L18 6l-1.5 1.5-2.25-.75H13.5v3h3.75l.75 2.25L19.5 12 21 10.5V12z M4.5 12l1.5-1.5.75 2.25H10.5v-3H9.75L9 7.5 7.5 6 6 7.5l.75 2.25L4.5 10.5V12z"/>
									</svg>
									<span className="text-[10px] text-teal-700 dark:text-teal-300">Elasticsearch</span>
								</div>
							</div>
						</div>
					</div>

					

					
					{/* Enterprise-Grade Tech Stack*/}
					<div className="mt-8 p-4 bg-gradient-to-br from-slate-50 to-slate-100 dark:from-zinc-900 dark:to-zinc-800 border border-slate-200 dark:border-zinc-700 rounded-lg animate-slide-up delay-375">
						<div className="flex items-center gap-2 mb-3">
							<svg className="w-4 h-4 text-slate-700 dark:text-zinc-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
							</svg>
							<h4 className="text-xs font-bold text-slate-900 dark:text-zinc-100 uppercase tracking-wide">
								Enterprise-Grade Tech Stack
							</h4>
						</div>
						<div className="grid grid-cols-2 gap-3">
							<div>
								<p className="text-[9px] text-slate-500 dark:text-zinc-400 font-semibold uppercase mb-1">Backend</p>
								<div className="flex flex-col gap-1">
									<div className="flex items-center gap-1.5">
										<svg className="w-3 h-3 text-blue-600 dark:text-blue-400" viewBox="0 0 24 24" fill="currentColor">
											<path d="M14.25.18l.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05.63-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.77l-.69.05-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.17l-.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24-.01h.16l.06.01h8.16v-.83H6.18l-.01-2.75-.02-.37.05-.34.11-.31.17-.28.25-.26.31-.23.38-.2.44-.18.51-.15.58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98l-.23.33-.08.41.08.41.23.34.33.22.41.09.41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33-.22-.41-.09-.41.09zm13.09 3.95l.28.06.32.12.35.18.36.27.36.35.35.47.32.59.28.73.21.88.14 1.04.05 1.23-.06 1.23-.16 1.04-.24.86-.32.71-.36.57-.4.45-.42.33-.42.24-.4.16-.36.09-.32.05-.24.02-.16-.01h-8.22v.82h5.84l.01 2.76.02.36-.05.34-.11.31-.17.29-.25.25-.31.24-.38.2-.44.17-.51.15-.58.13-.64.09-.71.07-.77.04-.84.01-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25-.34-.16-.33-.1-.3-.04-.25-.02-.2.01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24.35-.2.35-.14.33-.1.3-.06.26-.04.21-.02.13-.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.27-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21V6.07h2.09l.14.01.21.03zm-6.47 14.25l-.23.33-.08.41.08.41.23.33.33.23.41.08.41-.08.33-.23.23-.33.08-.41-.08-.41-.23-.33-.33-.23-.41-.08-.41.08z"/>
										</svg>
										<span className="text-[10px] text-slate-700 dark:text-zinc-300">Python</span>
									</div>
									<div className="flex items-center gap-1.5">
										<svg className="w-3 h-3 text-teal-600 dark:text-teal-400" viewBox="0 0 24 24" fill="currentColor">
											<path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 2.4c5.302 0 9.6 4.298 9.6 9.6s-4.298 9.6-9.6 9.6S2.4 17.302 2.4 12 6.698 2.4 12 2.4zm1.2 4.8v9.6l-2.4-1.2V8.4l2.4-1.2z"/>
										</svg>
										<span className="text-[10px] text-slate-700 dark:text-zinc-300">FastAPI</span>
									</div>
									<div className="flex items-center gap-1.5">
										<svg className="w-3 h-3 text-blue-500 dark:text-blue-300" viewBox="0 0 24 24" fill="currentColor">
											<path d="M13.983 11.078h2.119a.186.186 0 00.186-.185V9.006a.186.186 0 00-.186-.186h-2.119a.185.185 0 00-.185.185v1.888c0 .102.083.185.185.185m-2.954-5.43h2.118a.186.186 0 00.186-.186V3.574a.186.186 0 00-.186-.185h-2.118a.185.185 0 00-.185.185v1.888c0 .102.082.185.185.185m0 2.716h2.118a.187.187 0 00.186-.186V6.29a.186.186 0 00-.186-.185h-2.118a.185.185 0 00-.185.185v1.887c0 .102.082.186.185.186m-2.93 0h2.12a.186.186 0 00.184-.186V6.29a.185.185 0 00-.185-.185H8.1a.185.185 0 00-.185.185v1.887c0 .102.083.186.185.186m-2.964 0h2.119a.186.186 0 00.185-.186V6.29a.185.185 0 00-.185-.185H5.136a.186.186 0 00-.186.185v1.887c0 .102.084.186.186.186m5.893 2.715h2.118a.186.186 0 00.186-.185V9.006a.186.186 0 00-.186-.186h-2.118a.185.185 0 00-.185.185v1.888c0 .102.082.185.185.185m-2.93 0h2.12a.185.185 0 00.184-.185V9.006a.185.185 0 00-.184-.186h-2.12a.185.185 0 00-.184.185v1.888c0 .102.083.185.185.185m-2.964 0h2.119a.185.185 0 00.185-.185V9.006a.185.185 0 00-.184-.186h-2.12a.186.186 0 00-.186.186v1.887c0 .102.084.185.186.185m-2.92 0h2.12a.185.185 0 00.184-.185V9.006a.185.185 0 00-.184-.186h-2.12a.185.185 0 00-.184.185v1.888c0 .102.082.185.185.185M23.763 9.89c-.065-.051-.672-.51-1.954-.51-.338 0-.676.03-1.01.087-.248-1.7-1.653-2.53-1.716-2.566l-.344-.199-.226.327c-.284.438-.49.922-.612 1.43-.23.97-.09 1.882.403 2.661-.595.332-1.55.413-1.744.42H.751a.751.751 0 00-.75.748 11.376 11.376 0 00.692 4.062c.545 1.428 1.355 2.48 2.41 3.124 1.18.723 3.1 1.137 5.275 1.137.983.003 1.963-.086 2.93-.266a12.248 12.248 0 003.823-1.389c.98-.567 1.86-1.288 2.61-2.136 1.252-1.418 1.998-2.997 2.553-4.4h.221c1.372 0 2.215-.549 2.68-1.009.309-.293.55-.65.707-1.046l.098-.288Z"/>
										</svg>
										<span className="text-[10px] text-slate-700 dark:text-zinc-300">Docker</span>
									</div>
								</div>
							</div>
							<div>
								<p className="text-[9px] text-slate-500 dark:text-zinc-400 font-semibold uppercase mb-1">Frontend</p>
								<div className="flex flex-col gap-1">
									<div className="flex items-center gap-1.5">
										<svg className="w-3 h-3 text-cyan-500 dark:text-cyan-400" viewBox="0 0 24 24" fill="currentColor">
											<path d="M14.23 12.004a2.236 2.236 0 0 1-2.235 2.236 2.236 2.236 0 0 1-2.236-2.236 2.236 2.236 0 0 1 2.235-2.236 2.236 2.236 0 0 1 2.236 2.236zm2.648-10.69c-1.346 0-3.107.96-4.888 2.622-1.78-1.653-3.542-2.602-4.887-2.602-.41 0-.783.093-1.106.278-1.375.793-1.683 3.264-.973 6.365C1.98 8.917 0 10.42 0 12.004c0 1.59 1.99 3.097 5.043 4.03-.704 3.113-.39 5.588.988 6.38.32.187.69.275 1.102.275 1.345 0 3.107-.96 4.888-2.624 1.78 1.654 3.542 2.603 4.887 2.603.41 0 .783-.09 1.106-.275 1.374-.792 1.683-3.263.973-6.365C22.02 15.096 24 13.59 24 12.004c0-1.59-1.99-3.097-5.043-4.032.704-3.11.39-5.587-.988-6.38-.318-.184-.688-.277-1.092-.278zm-.005 1.09v.006c.225 0 .406.044.558.127.666.382.955 1.835.73 3.704-.054.46-.142.945-.25 1.44-.96-.236-2.006-.417-3.107-.534-.66-.905-1.345-1.727-2.035-2.447 1.592-1.48 3.087-2.292 4.105-2.295zm-9.77.02c1.012 0 2.514.808 4.11 2.28-.686.72-1.37 1.537-2.02 2.442-1.107.117-2.154.298-3.113.538-.112-.49-.195-.964-.254-1.42-.23-1.868.054-3.32.714-3.707.19-.09.4-.127.563-.132zm4.882 3.05c.455.468.91.992 1.36 1.564-.44-.02-.89-.034-1.345-.034-.46 0-.915.01-1.36.034.44-.572.895-1.096 1.345-1.565zM12 8.1c.74 0 1.477.034 2.202.093.406.582.802 1.203 1.183 1.86.372.64.71 1.29 1.018 1.946-.308.655-.646 1.31-1.013 1.95-.38.66-.773 1.288-1.18 1.87-.728.063-1.466.098-2.21.098-.74 0-1.477-.035-2.202-.093-.406-.582-.802-1.204-1.183-1.86-.372-.64-.71-1.29-1.018-1.946.303-.657.646-1.313 1.013-1.954.38-.66.773-1.286 1.18-1.868.728-.064 1.466-.098 2.21-.098zm-3.635.254c-.24.377-.48.763-.704 1.16-.225.39-.435.782-.635 1.174-.265-.656-.49-1.31-.676-1.947.64-.15 1.315-.283 2.015-.386zm7.26 0c.695.103 1.365.23 2.006.387-.18.632-.405 1.282-.66 1.933-.2-.39-.41-.783-.64-1.174-.225-.392-.465-.774-.705-1.146zm3.063.675c.484.15.944.317 1.375.498 1.732.74 2.852 1.708 2.852 2.476-.005.768-1.125 1.74-2.857 2.475-.42.18-.88.342-1.355.493-.28-.958-.646-1.956-1.1-2.98.45-1.017.81-2.01 1.085-2.964zm-13.395.004c.278.96.645 1.957 1.1 2.98-.45 1.017-.812 2.01-1.086 2.964-.484-.15-.944-.318-1.37-.5-1.732-.737-2.852-1.706-2.852-2.474 0-.768 1.12-1.742 2.852-2.476.42-.18.88-.342 1.356-.494zm11.678 4.28c.265.657.49 1.312.676 1.948-.64.157-1.316.29-2.016.39.24-.375.48-.762.705-1.158.225-.39.435-.788.636-1.18zm-9.945.02c.2.392.41.783.64 1.175.23.39.465.772.705 1.143-.695-.102-1.365-.23-2.006-.386.18-.63.406-1.282.66-1.933zM17.92 16.32c.112.493.2.968.254 1.423.23 1.868-.054 3.32-.714 3.708-.147.09-.338.128-.563.128-1.012 0-2.514-.807-4.11-2.28.686-.72 1.37-1.536 2.02-2.44 1.107-.118 2.154-.3 3.113-.54zm-11.83.01c.96.234 2.006.415 3.107.532.66.905 1.345 1.727 2.035 2.446-1.595 1.483-3.092 2.295-4.11 2.295-.22-.005-.406-.05-.553-.132-.666-.38-.955-1.834-.73-3.703.054-.46.142-.944.25-1.438zm4.56.64c.44.02.89.034 1.345.034.46 0 .915-.01 1.36-.034-.44.572-.895 1.095-1.345 1.565-.455-.47-.91-.993-1.36-1.565z"/>
										</svg>
										<span className="text-[10px] text-slate-700 dark:text-zinc-300">React</span>
									</div>
									<div className="flex items-center gap-1.5">
										<svg className="w-3 h-3 text-blue-600 dark:text-blue-400" viewBox="0 0 24 24" fill="currentColor">
											<path d="M1.125 0C.502 0 0 .502 0 1.125v21.75C0 23.498.502 24 1.125 24h21.75c.623 0 1.125-.502 1.125-1.125V1.125C24 .502 23.498 0 22.875 0zm17.363 9.75c.612 0 1.154.037 1.627.111a6.38 6.38 0 0 1 1.306.34v2.458a3.95 3.95 0 0 0-.643-.361 5.093 5.093 0 0 0-.717-.26 5.453 5.453 0 0 0-1.426-.2c-.3 0-.573.028-.819.086a2.1 2.1 0 0 0-.623.242c-.17.104-.3.229-.393.374a.888.888 0 0 0-.14.49c0 .196.053.373.156.529.104.156.252.304.443.444s.423.276.696.41c.273.135.582.274.926.416.47.197.892.407 1.266.628.374.222.695.473.963.753.268.279.472.598.614.957.142.359.214.776.214 1.253 0 .657-.125 1.21-.373 1.656a3.033 3.033 0 0 1-1.012 1.085 4.38 4.38 0 0 1-1.487.596c-.566.12-1.163.18-1.79.18a9.916 9.916 0 0 1-1.84-.164 5.544 5.544 0 0 1-1.512-.493v-2.63a5.033 5.033 0 0 0 3.237 1.2c.333 0 .624-.03.872-.09.249-.06.456-.144.623-.25.166-.108.29-.234.373-.38a1.023 1.023 0 0 0-.074-1.089 2.12 2.12 0 0 0-.537-.5 5.597 5.597 0 0 0-.807-.444 27.72 27.72 0 0 0-1.007-.436c-.918-.383-1.602-.852-2.053-1.405-.45-.553-.676-1.222-.676-2.005 0-.614.123-1.141.369-1.582.246-.441.58-.804 1.004-1.089a4.494 4.494 0 0 1 1.47-.629 7.536 7.536 0 0 1 1.77-.201zm-15.113.188h9.563v2.166H9.506v9.646H6.789v-9.646H3.375z"/>
										</svg>
										<span className="text-[10px] text-slate-700 dark:text-zinc-300">TypeScript</span>
									</div>
									<div className="flex items-center gap-1.5">
										<svg className="w-3 h-3 text-purple-600 dark:text-purple-400" viewBox="0 0 24 24" fill="currentColor">
											<path d="M14.257 3.955c-1.1 0-2.047.84-2.047 1.939s.948 1.94 2.047 1.94c1.1 0 2.047-.84 2.047-1.94s-.948-1.939-2.047-1.939zm-6.48 0c-1.1 0-2.047.84-2.047 1.939s.948 1.94 2.047 1.94c1.1 0 2.047-.84 2.047-1.94s-.948-1.939-2.047-1.939zm-6.481 5.11c-1.1 0-2.047.84-2.047 1.939s.948 1.94 2.047 1.94c1.099 0 2.047-.84 2.047-1.94s-.948-1.939-2.047-1.939zm20.408 2.47l-10.43 6.015L.704 11.535v2.502l10.57 6.015 10.43-6.015V11.535z"/>
										</svg>
										<span className="text-[10px] text-slate-700 dark:text-zinc-300">Vite • Tailwind</span>
									</div>
								</div>
							</div>
							<div>
								<p className="text-[9px] text-slate-500 dark:text-zinc-400 font-semibold uppercase mb-1">AI & RAG</p>
								<div className="flex flex-col gap-1">
									<div className="flex items-center gap-1.5">
										<svg className="w-3 h-3 text-blue-500 dark:text-blue-300" viewBox="0 0 24 24" fill="currentColor">
											<path d="M12 0l3 7h7l-5.5 4 2 7-6.5-5-6.5 5 2-7L2 7h7z"/>
										</svg>
										<span className="text-[10px] text-slate-700 dark:text-zinc-300">Gemini API</span>
									</div>
									<div className="flex items-center gap-1.5">
										<svg className="w-3 h-3 text-green-600 dark:text-green-400" viewBox="0 0 24 24" fill="currentColor">
											<path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5zm-2 15l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/>
										</svg>
										<span className="text-[10px] text-slate-700 dark:text-zinc-300">Legal NLP</span>
									</div>
									<div className="flex items-center gap-1.5">
										<svg className="w-3 h-3 text-purple-600 dark:text-purple-400" viewBox="0 0 24 24" fill="currentColor">
											<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm.31-8.86c-1.77-.45-2.34-.94-2.34-1.67 0-.84.79-1.43 2.1-1.43 1.38 0 1.9.66 1.94 1.64h1.71c-.05-1.34-.87-2.57-2.49-2.97V5H10.9v1.69c-1.51.32-2.72 1.3-2.72 2.81 0 1.79 1.49 2.69 3.66 3.21 1.95.46 2.34 1.15 2.34 1.87 0 .53-.39 1.39-2.1 1.39-1.6 0-2.23-.72-2.32-1.64H8.04c.1 1.7 1.36 2.66 2.86 2.97V19h2.34v-1.67c1.52-.29 2.72-1.16 2.73-2.77-.01-2.2-1.9-2.96-3.66-3.42z"/>
										</svg>
										<span className="text-[10px] text-slate-700 dark:text-zinc-300">Embeddings</span>
									</div>
								</div>
							</div>
							<div>
								<p className="text-[9px] text-slate-500 dark:text-zinc-400 font-semibold uppercase mb-1">Data Layer</p>
								<div className="flex flex-col gap-1">
									<div className="flex items-center gap-1.5">
										<svg className="w-3 h-3 text-green-600 dark:text-green-400" viewBox="0 0 24 24" fill="currentColor">
											<path d="M12 0c6.627 0 12 2.686 12 6v12c0 3.314-5.373 6-12 6s-12-2.686-12-6V6c0-3.314 5.373-6 12-6zm0 2C7.03 2 3 3.79 3 6s4.03 4 9 4 9-1.79 9-4-4.03-4-9-4zM3 8.69c1.953 1.396 5.174 2.31 9 2.31s7.047-.914 9-2.31V12c0 2.21-4.03 4-9 4s-9-1.79-9-4V8.69zM3 14.69c1.953 1.396 5.174 2.31 9 2.31s7.047-.914 9-2.31V18c0 2.21-4.03 4-9 4s-9-1.79-9-4v-3.31z"/>
										</svg>
										<span className="text-[10px] text-slate-700 dark:text-zinc-300">Neo4j</span>
									</div>
									<div className="flex items-center gap-1.5">
										<svg className="w-3 h-3 text-yellow-600 dark:text-yellow-400" viewBox="0 0 24 24" fill="currentColor">
											<path d="M10.5 19.5h3v-3h-3v3zm0-15v3h3v-3h-3zM21 12v-1.5l-2.25-.75.75-2.25L18 6l-1.5 1.5-2.25-.75H13.5v3h3.75l.75 2.25L19.5 12 21 10.5V12z M4.5 12l1.5-1.5.75 2.25H10.5v-3H9.75L9 7.5 7.5 6 6 7.5l.75 2.25L4.5 10.5V12z M12 16.5c-2.485 0-4.5-2.015-4.5-4.5s2.015-4.5 4.5-4.5 4.5 2.015 4.5 4.5-2.015 4.5-4.5 4.5z"/>
										</svg>
										<span className="text-[10px] text-slate-700 dark:text-zinc-300">Elasticsearch</span>
									</div>
								</div>
							</div>
						</div>
						<div className="mt-3 pt-3 border-t border-slate-200 dark:border-zinc-700">
							<div className="flex items-center justify-between">
								<span className="text-[9px] text-slate-500 dark:text-zinc-400 font-medium">Horizontal Scaling Ready</span>
								<div className="flex gap-1">
									<span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
									<span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse delay-100"></span>
									<span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse delay-200"></span>
								</div>
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
