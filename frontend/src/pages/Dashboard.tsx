import { useNavigate } from "react-router-dom";

export function Dashboard() {
	const navigate = useNavigate();

	return (
		<div className="flex flex-col h-full animate-fade-in">
			<div className="grid grid-cols-12 gap-12 md:gap-24 h-full">
				{/* Dominant Metric */}
				<div className="col-span-12 lg:col-span-5 flex flex-col lg:pr-16 lg:border-r border-slate-100">
					<div className="mb-auto">
						<p className="label-kpi animate-slide-up text-lg mb-4">
							Total Regulations Indexed
						</p>
						<div className="flex items-baseline gap-4 mb-8 overflow-hidden">
							<span className="text-7xl md:text-9xl value-kpi text-slate-900 transition-all hover:text-teal-600 duration-150 origin-left cursor-default animate-slide-up delay-100">
								1,245
							</span>
						</div>
						<div className="flex items-center gap-3 mb-8 animate-slide-up delay-200">
							<span className="bg-teal-50 text-teal-700 text-[11px] font-bold px-2 py-1 uppercase tracking-wide rounded-sm animate-pulse">
								Sync Active
							</span>
							<span className="text-xs text-teal-600 font-medium">
								+12 This Week
							</span>
						</div>
						<p className="text-sm text-slate-500 leading-relaxed max-w-sm animate-slide-up delay-300">
							Full digitization of the Employment Insurance Act and workforce
							policies. System validates forms against indexed regulations in
							real-time.
						</p>
					</div>
				</div>

				{/* Secondary Metrics & Quick Actions */}
				<div className="col-span-12 lg:col-span-7 flex flex-col justify-between">
					{/* Top Row: Metrics */}
					<div className="grid grid-cols-2 gap-12 md:gap-24">
						<div className="animate-slide-up delay-200">
							<p className="label-kpi mb-2">Search Accuracy</p>
							<div className="flex items-baseline gap-2 group">
								<span className="text-5xl md:text-6xl value-kpi text-slate-800 group-hover:text-teal-600 transition-colors">
									95.2%
								</span>
								<span className="text-sm text-slate-400">verified</span>
							</div>
						</div>
						<div className="animate-slide-up delay-300">
							<p className="label-kpi mb-2">Avg Response Time</p>
							<div className="flex items-baseline gap-2 group">
								<span className="text-5xl md:text-6xl value-kpi text-slate-800 group-hover:text-teal-600 transition-colors">
									0.8s
								</span>
								<span className="text-sm text-slate-400">latency</span>
							</div>
						</div>
					</div>

					{/* Middle Row: Chart */}
					<div className="mt-24 animate-slide-up delay-300">
						<p className="label-kpi mb-8">Query Volume (6 Month Trend)</p>
						<div className="w-full h-48 flex items-end justify-between gap-6 max-w-2xl">
							<div
								className="w-full bg-slate-100 h-[30%] chart-bar"
								style={{ animationDelay: "400ms" }}
							></div>
							<div
								className="w-full bg-slate-100 h-[45%] chart-bar"
								style={{ animationDelay: "500ms" }}
							></div>
							<div
								className="w-full bg-slate-100 h-[40%] chart-bar"
								style={{ animationDelay: "600ms" }}
							></div>
							<div
								className="w-full bg-slate-100 h-[65%] chart-bar"
								style={{ animationDelay: "700ms" }}
							></div>
							<div
								className="w-full bg-slate-100 h-[55%] chart-bar"
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

					{/* Bottom Row: Nav Links */}
					<div className="grid grid-cols-1 md:grid-cols-3 gap-12 mt-auto pt-12 border-t border-slate-100 animate-slide-up delay-500">
						<button
							type="button"
							className="text-left group cursor-pointer"
							onClick={() => navigate("/search")}
						>
							<span className="text-xs font-bold text-slate-900 group-hover:text-teal-600 flex items-center gap-2 transition-all group-hover:translate-x-1">
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
							<span className="text-xs font-bold text-slate-900 group-hover:text-teal-600 flex items-center gap-2 transition-all group-hover:translate-x-1">
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
							<span className="text-xs font-bold text-slate-900 group-hover:text-teal-600 flex items-center gap-2 transition-all group-hover:translate-x-1">
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
