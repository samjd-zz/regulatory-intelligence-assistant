import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { LoadingSpinnerProps } from "@/types";

export function LoadingSpinner({ size = "md", message }: LoadingSpinnerProps) {
	const sizeClasses = {
		sm: "w-4 h-4",
		md: "w-8 h-8",
		lg: "w-12 h-12",
	};

	return (
		<output
			className="flex flex-col items-center justify-center gap-3"
			aria-live="polite"
			aria-busy="true"
		>
			<Loader2
				className={cn("animate-spin text-teal-600", sizeClasses[size])}
				aria-hidden="true"
			/>
			{message && <p className="text-sm text-slate-500">{message}</p>}
			<span className="sr-only">Loading...</span>
		</output>
	);
}
