import { Target } from "lucide-react";
import { cn, getConfidenceLabel } from "@/lib/utils";
import type { ConfidenceBadgeProps } from "@/types";

export function ConfidenceBadge({
	score,
	showLabel = true,
	size = "md",
}: ConfidenceBadgeProps) {
	const label = getConfidenceLabel(score);

	const sizeClasses = {
		sm: "text-[10px] px-1.5 py-0.5",
		md: "text-xs px-2 py-0.5",
		lg: "text-sm px-2.5 py-1",
	};

	const iconSizes = {
		sm: "w-2.5 h-2.5",
		md: "w-3 h-3",
		lg: "w-4 h-4",
	};

	const bgClass =
		score >= 0.8
			? "bg-teal-50 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400"
			: score >= 0.5
				? "bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
				: "bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400";

	return (
		<output
			className={cn(
				"inline-flex items-center gap-1 rounded-sm font-semibold uppercase tracking-wide",
				sizeClasses[size],
				bgClass,
			)}
			aria-label={`Confidence score: ${Math.round(score * 100)}%`}
			title={`Confidence: ${label} (${Math.round(score * 100)}%)`}
		>
			<Target className={iconSizes[size]} aria-hidden="true" />
			{showLabel && <span>{label}</span>}
		</output>
	);
}
