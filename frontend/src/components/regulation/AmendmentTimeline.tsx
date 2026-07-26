import { useTranslation } from "react-i18next";
import { formatDate } from "@/lib/utils";

interface Amendment {
	id: string;
	date: string;
	type: "amended" | "added" | "repealed";
	description: string;
	citation?: string;
}

interface AmendmentTimelineProps {
	amendments?: Amendment[];
	effectiveDate?: string | null;
}

export function AmendmentTimeline({
	amendments = [],
	effectiveDate,
}: AmendmentTimelineProps) {
	const { t } = useTranslation();

	// If no amendments and no effective date, don't render
	if (amendments.length === 0 && !effectiveDate) {
		return null;
	}

	// Combine effective date with amendments for the timeline
	const timelineEvents: Array<{
		date: string;
		type: string;
		description: string;
		citation?: string;
	}> = [];

	if (effectiveDate) {
		timelineEvents.push({
			date: effectiveDate,
			type: "added",
			description: "Original enactment",
			citation: undefined,
		});
	}

	timelineEvents.push(...amendments);

	// Sort by date (newest first)
	timelineEvents.sort(
		(a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
	);

	const getTypeColor = (type: string) => {
		switch (type) {
			case "added":
				return "bg-green-100 dark:bg-green-900/20 border-green-300 dark:border-green-700 text-green-700 dark:text-green-300";
			case "amended":
				return "bg-amber-100 dark:bg-amber-900/20 border-amber-300 dark:border-amber-700 text-amber-700 dark:text-amber-300";
			case "repealed":
				return "bg-red-100 dark:bg-red-900/20 border-red-300 dark:border-red-700 text-red-700 dark:text-red-300";
			default:
				return "bg-slate-100 dark:bg-zinc-800 border-slate-300 dark:border-zinc-700 text-slate-700 dark:text-zinc-300";
		}
	};

	const getTypeIcon = (type: string) => {
		switch (type) {
			case "added":
				return "add_circle";
			case "amended":
				return "edit_note";
			case "repealed":
				return "cancel";
			default:
				return "history";
		}
	};

	return (
		<div className="bg-white dark:bg-zinc-900 rounded-lg border border-slate-200 dark:border-zinc-700 overflow-hidden">
			<div className="bg-gradient-to-r from-slate-50 to-slate-100 dark:from-zinc-800 dark:to-zinc-900 p-6 border-b border-slate-200 dark:border-zinc-700">
				<h2 className="text-2xl font-light text-slate-800 dark:text-zinc-200 mb-2 flex items-center gap-2">
					<span className="material-symbols-outlined text-slate-500 dark:text-zinc-400">
						history
					</span>
					{t("regulation.amendmentHistory")}
				</h2>
				<p className="text-sm text-slate-600 dark:text-zinc-400">
					{t("regulation.amendmentHistoryDesc")}
				</p>
			</div>

			<div className="p-6">
				{timelineEvents.length === 0 ? (
					<div className="text-center py-8">
						<span className="material-symbols-outlined text-4xl text-slate-300 dark:text-zinc-600 mb-3 block">
							event_busy
						</span>
						<p className="text-sm text-slate-500 dark:text-zinc-500">
							{t("regulation.noAmendments")}
						</p>
					</div>
				) : (
					<div className="relative">
						{/* Timeline Line */}
						<div className="absolute left-6 top-0 bottom-0 w-0.5 bg-slate-200 dark:bg-zinc-700" />

						<div className="space-y-6">
							{timelineEvents.map((event, index) => (
								<div
									key={index}
									className="relative pl-16 animate-slide-up"
									style={{ animationDelay: `${index * 50}ms` }}
								>
									{/* Timeline Dot */}
									<div
										className={`absolute left-3 w-6 h-6 rounded-full border-4 ${getTypeColor(
											event.type
										)} flex items-center justify-center`}
									>
										<span
											className={`material-symbols-outlined text-xs ${
												event.type === "added"
													? "text-green-600 dark:text-green-400"
													: event.type === "amended"
														? "text-amber-600 dark:text-amber-400"
														: "text-red-600 dark:text-red-400"
											}`}
										>
											{getTypeIcon(event.type)}
										</span>
									</div>

									{/* Event Card */}
									<div
										className={`rounded-lg border-2 p-4 ${getTypeColor(
											event.type
										)} hover:shadow-md transition-shadow`}
									>
										<div className="flex items-start justify-between gap-4 mb-2">
											<div className="flex-1">
												<div className="flex items-center gap-2 mb-1">
													<span className="text-xs font-bold uppercase tracking-wide">
														{t(`regulation.${event.type}`)}
													</span>
													<span className="text-xs opacity-75">•</span>
													<span className="text-xs">
														{formatDate(event.date)}
													</span>
												</div>
												<p className="text-sm font-medium">
													{event.description}
												</p>
											</div>
										</div>

										{event.citation && (
											<div className="mt-3 pt-3 border-t border-current opacity-50">
												<div className="flex items-center gap-2">
													<span className="material-symbols-outlined text-xs">
														gavel
													</span>
													<span className="text-xs font-mono">
														{event.citation}
													</span>
												</div>
											</div>
										)}
									</div>
								</div>
							))}
						</div>
					</div>
				)}
			</div>
		</div>
	);
}
