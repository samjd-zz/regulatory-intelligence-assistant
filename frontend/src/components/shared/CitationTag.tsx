import { Copy, Check } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import type { CitationTagProps } from "@/types";

export function CitationTag({
	citation,
	onClick,
	variant = "default",
}: CitationTagProps) {
	const [copied, setCopied] = useState(false);

	const handleCopy = async (e: React.MouseEvent) => {
		e.stopPropagation();
		await navigator.clipboard.writeText(citation);
		setCopied(true);
		setTimeout(() => setCopied(false), 2000);
	};

	const baseClasses = cn(
		"inline-flex items-center gap-1 rounded font-mono text-xs",
		variant === "compact" ? "px-1.5 py-0.5" : "px-2 py-1",
		"bg-slate-100 text-slate-700 border border-slate-200 dark:bg-zinc-800 dark:text-zinc-300 dark:border-zinc-700",
		"transition-colors",
	);

	const content = (
		<>
			<span className="select-all">{citation}</span>
			<button
				onClick={handleCopy}
				className="ml-1 p-0.5 rounded hover:bg-slate-300 dark:hover:bg-zinc-600 transition-colors"
				aria-label="Copy citation"
				title="Copy citation"
				type="button"
			>
				{copied ? (
					<Check className="w-3 h-3 text-teal-600 dark:text-teal-400" aria-label="Copied" />
				) : (
					<Copy className="w-3 h-3" aria-hidden="true" />
				)}
			</button>
		</>
	);

	if (onClick) {
		return (
			<button
				type="button"
				className={cn(
					baseClasses,
					"cursor-pointer hover:bg-slate-200 hover:border-slate-300",
				)}
				onClick={onClick}
				aria-label={`Citation: ${citation}`}
			>
				{content}
			</button>
		);
	}

	return (
		<span className={baseClasses} title={citation}>
			{content}
		</span>
	);
}
