import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { CheckCircle, AlertCircle, XCircle } from "lucide-react";
import { useComplianceStore } from "@/store/complianceStore";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";

// Validation schema
const complianceSchema = z.object({
	full_name: z
		.string()
		.min(2, "Name must be at least 2 characters")
		.max(100, "Name must be less than 100 characters"),
	sin: z
		.string()
		.regex(/^\d{3}-\d{3}-\d{3}$/, "SIN must be in format: 123-456-789")
		.length(11, "SIN must be exactly 11 characters including dashes"),
	residency_status: z.enum(
		["citizen", "permanent_resident", "temporary_resident"],
		{
			message: "Please select a valid residency status",
		},
	),
	hours_worked: z
		.number()
		.int("Hours must be a whole number")
		.min(420, "Minimum 420 hours required for eligibility")
		.max(10000, "Hours worked seems unreasonably high"),
});

type ComplianceFormData = z.infer<typeof complianceSchema>;

export function Compliance() {
	const { report, checking, error, checkCompliance } = useComplianceStore();
	const [programId] = useState("employment-insurance");

	const {
		register,
		handleSubmit,
		formState: { errors, isValid },
		watch,
	} = useForm<ComplianceFormData>({
		resolver: zodResolver(complianceSchema),
		mode: "onBlur",
		defaultValues: {
			full_name: "",
			sin: "",
			residency_status: undefined,
			hours_worked: undefined,
		},
	});

	const hoursWorked = watch("hours_worked");
	const residencyStatus = watch("residency_status");

	const onSubmit = async () => {
		await checkCompliance(programId);
	};

	const getResidencyLabel = (status: string) => {
		const labels: Record<string, string> = {
			citizen: "Citizen",
			permanent_resident: "Permanent Resident",
			temporary_resident: "Temporary Resident",
		};
		return labels[status] || status;
	};

	return (
		<div className="flex flex-col px-12 py-10 h-full animate-fade-in">
			<div className="grid grid-cols-2 gap-24 h-full">
				{/* Left: Form */}
				<div className="flex flex-col justify-center animate-slide-up">
					<div className="mb-10">
						<h2 className="text-xl font-semibold text-slate-900">
							Compliance Check
						</h2>
						<p className="text-sm text-slate-400 mt-1">
							Employment Insurance Application
						</p>
					</div>
					<form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
						{/* Full Name */}
						<div className="group">
							<label
								htmlFor="comp-name"
								className="label-kpi block group-focus-within:text-teal-600 transition-colors"
							>
								Full Legal Name
							</label>
							<input
								type="text"
								id="comp-name"
								{...register("full_name")}
								placeholder="John Doe"
								className={`input-minimal ${errors.full_name ? "border-red-500" : ""}`}
							/>
							{errors.full_name && (
								<p className="mt-1 text-sm text-red-600">
									{errors.full_name.message}
								</p>
							)}
						</div>

						{/* SIN */}
						<div className="group">
							<label
								htmlFor="comp-sin"
								className="label-kpi block group-focus-within:text-teal-600 transition-colors"
							>
								Social Insurance Number (SIN)
							</label>
							<input
								type="text"
								id="comp-sin"
								{...register("sin")}
								placeholder="000-000-000"
								maxLength={11}
								className={`input-minimal ${errors.sin ? "border-red-500" : ""}`}
							/>
							{errors.sin && (
								<p className="mt-1 text-sm text-red-600">
									{errors.sin.message}
								</p>
							)}
						</div>

						{/* Residency Status */}
						<div className="group">
							<label
								htmlFor="comp-residency"
								className="label-kpi block group-focus-within:text-teal-600 transition-colors"
							>
								Residency Status
							</label>
							<div className="relative">
								<select
									id="comp-residency"
									{...register("residency_status")}
									className={`input-minimal appearance-none cursor-pointer bg-transparent ${errors.residency_status ? "border-red-500" : ""}`}
								>
									<option value="" disabled>
										Select status...
									</option>
									<option value="citizen">Canadian Citizen</option>
									<option value="permanent_resident">Permanent Resident</option>
									<option value="temporary_resident">
										Temporary Resident (Work Permit)
									</option>
								</select>
								<span className="material-symbols-outlined absolute right-0 top-3 pointer-events-none text-slate-400 text-sm group-hover:text-teal-600 transition-colors">
									expand_more
								</span>
							</div>
							{errors.residency_status && (
								<p className="mt-1 text-sm text-red-600">
									{errors.residency_status.message}
								</p>
							)}
						</div>

						{/* Hours Worked */}
						<div className="group">
							<label
								htmlFor="comp-hours"
								className="label-kpi block group-focus-within:text-teal-600 transition-colors"
							>
								Hours Worked (Last 52 Weeks)
							</label>
							<div className="flex items-center gap-4">
								<input
									type="number"
									id="comp-hours"
									{...register("hours_worked", { valueAsNumber: true })}
									placeholder="e.g. 600"
									min="0"
									className={`input-minimal ${errors.hours_worked ? "border-red-500" : ""}`}
								/>
								<span className="text-xs text-slate-400 whitespace-nowrap pt-3">
									Min. 420 hrs
								</span>
							</div>
							{errors.hours_worked && (
								<p className="mt-1 text-sm text-red-600">
									{errors.hours_worked.message}
								</p>
							)}
						</div>

						<div className="pt-8">
							<button
								type="submit"
								disabled={checking || !isValid}
								className="w-full bg-slate-900 text-white py-4 text-xs font-bold uppercase tracking-widest hover:bg-teal-700 hover:shadow-lg transition-all transform hover:-translate-y-1 active:translate-y-0 disabled:opacity-50 disabled:cursor-not-allowed"
							>
								{checking ? "Analyzing..." : "Analyze Compliance"}
							</button>
						</div>

						{!isValid && Object.keys(errors).length > 0 && (
							<p className="text-sm text-amber-600 text-center animate-slide-up">
								Please fix validation errors before submitting
							</p>
						)}
					</form>
				</div>

				{/* Right: Results */}
				<div className="flex flex-col justify-center border-l border-slate-50 pl-24 relative overflow-hidden h-full">
					{/* Loading State */}
					{checking && (
						<div className="flex justify-center py-12 animate-scale-in">
							<LoadingSpinner message="Checking compliance..." />
						</div>
					)}

					{/* Error State */}
					{error && (
						<div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800 animate-scale-in">
							<div className="flex items-start gap-2">
								<XCircle className="w-5 h-5 mt-0.5 shrink-0" />
								<div>
									<p className="font-medium">Error</p>
									<p className="text-sm">{error}</p>
								</div>
							</div>
						</div>
					)}

					{/* Empty State */}
					{!checking && !error && !report && (
						<div className="flex flex-col items-center justify-center text-center animate-scale-in h-full">
							<div className="relative mb-6 group cursor-default">
								<div className="absolute inset-0 bg-teal-100 rounded-full blur-xl opacity-20 group-hover:opacity-40 transition-opacity duration-500" />
								<span className="material-symbols-outlined text-6xl text-slate-300 relative z-10 transition-transform duration-500 group-hover:scale-110 group-hover:text-teal-500/50">
									fact_check
								</span>
							</div>
							<h3 className="text-lg font-medium text-slate-700 mb-2">
								Ready for Analysis
							</h3>
							<p className="text-sm text-slate-400 max-w-[200px] leading-relaxed">
								Fill out the applicant details to generate a real-time
								compliance report.
							</p>
						</div>
					)}

					{/* Result State */}
					{!checking && !error && report && (
						<div className="animate-scale-in">
							<p className="label-kpi mb-4 text-teal-600">Evaluation Result</p>

							{/* Status Header */}
							<div className="mb-10">
								{report.compliant ? (
									<>
										<h3 className="text-4xl font-semibold text-teal-700 mb-2 animate-slide-up">
											Likely Eligible
										</h3>
										<p className="text-sm text-teal-600 animate-slide-up delay-100">
											Meets regional requirements
										</p>
									</>
								) : (
									<>
										<h3 className="text-4xl font-semibold text-red-600 mb-2 animate-slide-up">
											Not Eligible
										</h3>
										<p className="text-sm text-red-500 animate-slide-up delay-100">
											Issues found in application
										</p>
									</>
								)}
							</div>

							{/* Result Details */}
							<div className="space-y-6">
								<div className="flex justify-between border-b border-slate-100 pb-2 animate-slide-up delay-100">
									<span className="text-sm text-slate-500">
										Hours Threshold
									</span>
									<span className="text-sm font-mono text-slate-900">
										{hoursWorked || 0} / 420
										{(hoursWorked ?? 0) >= 420 ? (
											<span className="text-teal-600 font-bold ml-2">✓</span>
										) : (
											<span className="text-red-600 font-bold ml-2">✕</span>
										)}
									</span>
								</div>
								<div className="flex justify-between border-b border-slate-100 pb-2 animate-slide-up delay-200">
									<span className="text-sm text-slate-500">
										Residency Status
									</span>
									<span className="text-sm font-mono text-slate-900">
										{residencyStatus
											? getResidencyLabel(residencyStatus)
											: "Not Selected"}
									</span>
								</div>
								<div className="flex justify-between border-b border-slate-100 pb-2 animate-slide-up delay-300">
									<span className="text-sm text-slate-500">
										Confidence Score
									</span>
									<span className="text-sm font-mono text-teal-600 flex items-center gap-2">
										{Math.round(report.confidence * 100)}%
										<span className="material-symbols-outlined text-sm">
											check_circle
										</span>
									</span>
								</div>
							</div>

							{/* Issues Section */}
							{report.issues.length > 0 && (
								<div className="mt-8 animate-slide-up delay-300">
									<h3 className="font-semibold text-slate-900 mb-3 flex items-center gap-2 text-sm">
										<XCircle className="w-4 h-4 text-red-600" />
										Issues ({report.issues.length})
									</h3>
									<div className="space-y-2 max-h-40 overflow-y-auto">
										{report.issues.map((issue) => (
											<div
												key={issue.id}
												className={`rounded p-3 border-l-4 text-xs ${
													issue.severity === "critical"
														? "bg-red-50 border-red-500"
														: issue.severity === "high"
															? "bg-orange-50 border-orange-500"
															: issue.severity === "medium"
																? "bg-yellow-50 border-yellow-500"
																: "bg-blue-50 border-blue-500"
												}`}
											>
												<div className="flex items-start gap-2">
													<AlertCircle
														className={`w-4 h-4 shrink-0 ${
															issue.severity === "critical"
																? "text-red-600"
																: issue.severity === "high"
																	? "text-orange-600"
																	: issue.severity === "medium"
																		? "text-yellow-600"
																		: "text-blue-600"
														}`}
													/>
													<div>
														<p className="font-medium text-slate-900">
															{issue.description}
														</p>
														<p className="text-slate-600 mt-1">
															💡 {issue.suggestion}
														</p>
													</div>
												</div>
											</div>
										))}
									</div>
								</div>
							)}

							{/* Passed Checks */}
							{report.passed_checks.length > 0 && (
								<div className="mt-6 animate-slide-up delay-300">
									<h3 className="font-semibold text-slate-900 mb-3 flex items-center gap-2 text-sm">
										<CheckCircle className="w-4 h-4 text-green-600" />
										Passed ({report.passed_checks.length})
									</h3>
									<div className="bg-green-50 border border-green-200 rounded p-3">
										<ul className="text-xs text-green-800 space-y-1">
											{report.passed_checks.slice(0, 3).map((check) => (
												<li key={check} className="flex items-start gap-2">
													<CheckCircle className="w-3 h-3 mt-0.5 shrink-0" />
													<span>{check}</span>
												</li>
											))}
											{report.passed_checks.length > 3 && (
												<li className="text-slate-600 pl-5">
													+{report.passed_checks.length - 3} more
												</li>
											)}
										</ul>
									</div>
								</div>
							)}

							<div className="mt-12 animate-slide-up delay-300">
								<button
									type="button"
									className="text-xs font-bold text-slate-400 hover:text-teal-600 flex items-center gap-2 uppercase tracking-wide group transition-colors"
								>
									<span className="material-symbols-outlined text-lg group-hover:scale-110 transition-transform">
										description
									</span>
									Generate Official Letter
								</button>
							</div>
						</div>
					)}
				</div>
			</div>
		</div>
	);
}
