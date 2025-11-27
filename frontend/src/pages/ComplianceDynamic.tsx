import { zodResolver } from "@hookform/resolvers/zod";
import { AlertCircle, CheckCircle, XCircle } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { PROGRAMS, type ProgramId, type FieldConfig } from "@/config/programs";
import { useComplianceStore } from "@/store/complianceStore";

export function ComplianceDynamic() {
	const { report, checking, error, checkCompliance } = useComplianceStore();
	const [selectedProgramId, setSelectedProgramId] = useState<ProgramId>(
		"employment-insurance"
	);

	const selectedProgram = PROGRAMS[selectedProgramId];

	const {
		register,
		handleSubmit,
		formState: { errors, isValid },
		reset,
	} = useForm({
		resolver: zodResolver(selectedProgram.validationSchema),
		mode: "onBlur",
	});

	const handleProgramChange = (newProgramId: ProgramId) => {
		setSelectedProgramId(newProgramId);
		reset(); // Reset form when program changes
		useComplianceStore.getState().reset(); // Clear previous results
	};

	const onSubmit = async (data: Record<string, unknown>) => {
		useComplianceStore.getState().setFormData(data);
		await checkCompliance(selectedProgramId);
	};

	const renderField = (field: FieldConfig) => {
		const fieldError = errors[field.name];

		switch (field.type) {
			case "text":
				return (
					<div key={field.name} className="group">
						<label
							htmlFor={field.name}
							className="label-kpi block group-focus-within:text-teal-600 dark:group-focus-within:text-teal-400 transition-colors"
						>
							{field.label}
						</label>
						<input
							type="text"
							id={field.name}
							{...register(field.name)}
							placeholder={field.placeholder}
							className={`input-minimal ${fieldError ? "border-red-500 dark:border-red-500" : ""}`}
						/>
						{fieldError && (
							<p className="mt-1 text-sm text-red-600 dark:text-red-400">
								{fieldError.message as string}
							</p>
						)}
						{field.helpText && !fieldError && (
							<p className="mt-1 text-xs text-slate-400 dark:text-zinc-400">
								{field.helpText}
							</p>
						)}
					</div>
				);

			case "number":
				return (
					<div key={field.name} className="group">
						<label
							htmlFor={field.name}
							className="label-kpi block group-focus-within:text-teal-600 dark:group-focus-within:text-teal-400 transition-colors"
						>
							{field.label}
						</label>
						<div className="flex items-center gap-4">
							<input
								type="number"
								id={field.name}
								{...register(field.name, { valueAsNumber: true })}
								placeholder={field.placeholder}
								min={field.min}
								max={field.max}
								className={`input-minimal ${fieldError ? "border-red-500 dark:border-red-500" : ""}`}
							/>
							{field.helpText && (
								<span className="text-xs text-slate-400 dark:text-zinc-400 whitespace-nowrap pt-3">
									{field.helpText}
								</span>
							)}
						</div>
						{fieldError && (
							<p className="mt-1 text-sm text-red-600 dark:text-red-400">
								{fieldError.message as string}
							</p>
						)}
					</div>
				);

			case "select":
				return (
					<div key={field.name} className="group">
						<label
							htmlFor={field.name}
							className="label-kpi block group-focus-within:text-teal-600 dark:group-focus-within:text-teal-400 transition-colors"
						>
							{field.label}
						</label>
						<div className="relative">
							<select
								id={field.name}
								{...register(field.name)}
								className={`input-minimal appearance-none cursor-pointer bg-transparent ${fieldError ? "border-red-500 dark:border-red-500" : ""}`}
							>
								<option value="">Select {field.label}...</option>
								{field.options?.map((opt) => (
									<option key={opt.value} value={opt.value}>
										{opt.label}
									</option>
								))}
							</select>
							<span className="material-symbols-outlined absolute right-0 top-3 pointer-events-none text-slate-400 dark:text-zinc-400 text-sm group-hover:text-teal-600 dark:group-hover:text-teal-400 transition-colors">
								expand_more
							</span>
						</div>
						{fieldError && (
							<p className="mt-1 text-sm text-red-600 dark:text-red-400">
								{fieldError.message as string}
							</p>
						)}
					</div>
				);

			case "file":
				return (
					<div key={field.name} className="group">
						<label
							htmlFor={field.name}
							className="label-kpi block group-focus-within:text-teal-600 dark:group-focus-within:text-teal-400 transition-colors"
						>
							{field.label}
						</label>
						<input
							type="file"
							id={field.name}
							{...register(field.name)}
							className={`input-minimal ${fieldError ? "border-red-500 dark:border-red-500" : ""}`}
							accept=".pdf,.jpg,.jpeg,.png"
						/>
						{field.helpText && !fieldError && (
							<p className="mt-1 text-xs text-slate-400 dark:text-zinc-400">
								{field.helpText}
							</p>
						)}
						{fieldError && (
							<p className="mt-1 text-sm text-red-600 dark:text-red-400">
								{fieldError.message as string}
							</p>
						)}
					</div>
				);

			default:
				return null;
		}
	};

	return (
		<div className="flex flex-col px-12 py-10 h-full animate-fade-in">
			{/* Program Selector */}
			<div className="mb-8">
				<h1 className="text-2xl font-bold text-slate-900 dark:text-zinc-100 mb-2">
					Compliance Checker
				</h1>
				<p className="text-sm text-slate-400 dark:text-zinc-400 mb-4">
					Select a government program to check your eligibility
				</p>
				<div className="flex gap-2 overflow-x-auto">
					{Object.values(PROGRAMS).map((program) => (
						<button
							key={program.id}
							onClick={() => handleProgramChange(program.id)}
							className={`px-4 py-2 text-xs font-medium rounded transition-all ${
								selectedProgramId === program.id
									? "bg-teal-600 text-white dark:bg-teal-500"
									: "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
							}`}
						>
							{program.name}
						</button>
					))}
				</div>
			</div>

			<div className="grid grid-cols-2 gap-24 flex-1">
				{/* Left: Form */}
				<div className="flex flex-col justify-center animate-slide-up">
					<div className="mb-6">
						<h2 className="text-xl font-semibold text-slate-900 dark:text-zinc-100">
							{selectedProgram.name}
						</h2>
						<p className="text-sm text-slate-400 dark:text-zinc-400 mt-1">
							{selectedProgram.description}
						</p>
					</div>
					<form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
						{selectedProgram.fields.map((field) => renderField(field))}

						<div className="pt-6">
							<button
								type="submit"
								disabled={checking || !isValid}
								className="w-full bg-slate-900 dark:bg-zinc-100 text-white dark:text-zinc-900 py-4 text-xs font-bold uppercase tracking-widest hover:bg-teal-700 dark:hover:bg-teal-400 hover:shadow-lg transition-all transform hover:-translate-y-1 active:translate-y-0 disabled:opacity-50 disabled:cursor-not-allowed"
							>
								{checking ? "Analyzing..." : "Analyze Compliance"}
							</button>
						</div>

						{!isValid && Object.keys(errors).length > 0 && (
							<p className="text-sm text-amber-600 dark:text-amber-500 text-center animate-slide-up">
								Please fix validation errors before submitting
							</p>
						)}
					</form>
				</div>

				{/* Right: Results */}
				<div className="flex flex-col justify-center border-l border-slate-50 dark:border-zinc-800 pl-24 relative overflow-hidden">
					{checking && (
						<div className="flex justify-center py-12 animate-scale-in">
							<LoadingSpinner message="Checking compliance..." />
						</div>
					)}

					{error && (
						<div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-800 dark:text-red-200 animate-scale-in">
							<div className="flex items-start gap-2">
								<XCircle className="w-5 h-5 mt-0.5 shrink-0" />
								<div>
									<p className="font-medium">Error</p>
									<p className="text-sm">{error}</p>
								</div>
							</div>
						</div>
					)}

					{!checking && !error && !report && (
						<div className="flex flex-col items-center justify-center text-center animate-scale-in h-full">
							<div className="relative mb-6 group cursor-default">
								<div className="absolute inset-0 bg-teal-100 dark:bg-teal-900/20 rounded-full blur-xl opacity-20 group-hover:opacity-40 transition-opacity duration-500" />
								<span className="material-symbols-outlined text-6xl text-slate-300 dark:text-zinc-600 relative z-10 transition-transform duration-500 group-hover:scale-110 group-hover:text-teal-500/50 dark:group-hover:text-teal-400/50">
									fact_check
								</span>
							</div>
							<h3 className="text-lg font-medium text-slate-700 dark:text-zinc-300 mb-2">
								Ready for Analysis
							</h3>
							<p className="text-sm text-slate-400 dark:text-zinc-400 max-w-[200px] leading-relaxed">
								Complete the form to generate a compliance report
							</p>
						</div>
					)}

					{!checking && !error && report && (
						<div className="animate-scale-in">
							<p className="label-kpi mb-4 text-teal-600 dark:text-teal-400">
								Evaluation Result
							</p>

							<div className="mb-10">
								{report.compliant ? (
									<>
										<h3 className="text-4xl font-semibold text-teal-700 dark:text-teal-400 mb-2 animate-slide-up">
											Likely Eligible
										</h3>
										<p className="text-sm text-teal-600 dark:text-teal-500 animate-slide-up delay-100">
											Meets program requirements
										</p>
									</>
								) : (
									<>
										<h3 className="text-4xl font-semibold text-red-600 dark:text-red-400 mb-2 animate-slide-up">
											Not Eligible
										</h3>
										<p className="text-sm text-red-500 dark:text-red-400 animate-slide-up delay-100">
											Issues found in application
										</p>
									</>
								)}
							</div>

							<div className="space-y-6">
								<div className="flex justify-between border-b border-slate-100 dark:border-zinc-800 pb-2 animate-slide-up delay-300">
									<span className="text-sm text-slate-500 dark:text-zinc-300">
										Confidence Score
									</span>
									<span className="text-sm font-mono text-teal-600 dark:text-teal-400 flex items-center gap-2">
										{Math.round(report.confidence * 100)}%
										<span className="material-symbols-outlined text-sm">
											check_circle
										</span>
									</span>
								</div>
							</div>

							{report.issues.length > 0 && (
								<div className="mt-8 animate-slide-up delay-300">
									<h3 className="font-semibold text-slate-900 dark:text-zinc-100 mb-3 flex items-center gap-2 text-sm">
										<XCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
										Issues ({report.issues.length})
									</h3>
									<div className="space-y-2 max-h-60 overflow-y-auto">
										{report.issues.map((issue) => (
											<div
												key={issue.issue_id}
												className={`rounded p-3 border-l-4 text-xs ${
													issue.severity === "critical"
														? "bg-red-50 dark:bg-red-900/20 border-red-500"
														: "bg-orange-50 dark:bg-orange-900/20 border-orange-500"
												}`}
											>
												<div className="flex items-start gap-2">
													<AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-red-600 dark:text-red-400" />
													<div className="flex-1">
														<p className="font-bold text-slate-900 dark:text-zinc-100 mb-1">
															{issue.requirement}
														</p>
														<p className="text-slate-700 dark:text-zinc-200">
															{issue.description}
														</p>
														{issue.suggestion && (
															<p className="text-slate-600 dark:text-zinc-300 mt-1.5 flex items-start gap-1">
																<span className="text-amber-600 dark:text-amber-400">
																	💡
																</span>
																<span>{issue.suggestion}</span>
															</p>
														)}
													</div>
												</div>
											</div>
										))}
									</div>
								</div>
							)}

							{report.passed_requirements > 0 && (
								<div className="mt-6 animate-slide-up delay-300">
									<h3 className="font-semibold text-slate-900 dark:text-zinc-100 mb-3 flex items-center gap-2 text-sm">
										<CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
										Requirements Met ({report.passed_requirements}/
										{report.total_requirements})
									</h3>
									<div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded p-3">
										<p className="text-xs text-green-800 dark:text-green-200">
											{report.passed_requirements} of {report.total_requirements}{" "}
											compliance requirements have been met.
										</p>
									</div>
								</div>
							)}
						</div>
					)}
				</div>
			</div>
		</div>
	);
}
