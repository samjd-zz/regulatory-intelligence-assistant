import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";

import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { formatDate } from "@/lib/utils";
import { getRegulationDetail, getRegulationRelationships } from "@/services/api";
import type { RegulationRelationships } from "@/types";

interface RegulationData {
	id: string;
	title: string;
	citation: string;
	jurisdiction: string;
	authority: string;
	effective_date: string | null;
	status: string;
	full_text: string;
	sections: Array<{
		id: string;
		number: string;
		title: string;
		content: string;
	}>;
}

export function RegulationDetail() {
	const { t } = useTranslation();
	const { id } = useParams<{ id: string }>();
	const [regulation, setRegulation] = useState<RegulationData | null>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [relationships, setRelationships] = useState<RegulationRelationships | null>(null);
	const [relationshipsLoading, setRelationshipsLoading] = useState(false);

	useEffect(() => {
		if (!id) return;

		let cancelled = false;

		async function fetchRegulation() {
			try {
				setLoading(true);
				const data = await getRegulationDetail(id!); // id is checked above
				if (!cancelled) {
					setRegulation(data);
					setError(null);
				}
			} catch (err) {
				if (!cancelled) {
					console.error("Error fetching regulation:", err);
					setError("Failed to load regulation details. Please try again.");
				}
			} finally {
				if (!cancelled) {
					setLoading(false);
				}
			}
		}

		fetchRegulation();

		// Cleanup function to prevent state updates on unmounted component
		return () => {
			cancelled = true;
		};
	}, [id]);

	// Fetch regulation relationships from Neo4j graph
	useEffect(() => {
		if (!id || !regulation) return;

		let cancelled = false;

		async function fetchRelationships() {
			try {
				setRelationshipsLoading(true);
				const data = await getRegulationRelationships(id!);
				if (!cancelled) {
					setRelationships(data);
				}
			} catch (err) {
				if (!cancelled) {
					console.error("Error fetching relationships:", err);
					// Non-critical error - don't show error to user
				}
			} finally {
				if (!cancelled) {
					setRelationshipsLoading(false);
				}
			}
		}

		fetchRelationships();

		return () => {
			cancelled = true;
		};
	}, [id, regulation]);

	if (loading) {
		return (
			<div className="flex items-center justify-center h-full">
				<LoadingSpinner />
			</div>
		);
	}

	if (error) {
		return (
			<div className="flex flex-col items-center justify-center h-full animate-fade-in">
				<div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 max-w-lg text-center">
					<span className="material-symbols-outlined text-4xl text-red-500 dark:text-red-400 mb-4">
						error
					</span>
					<h2 className="text-lg font-medium text-red-900 dark:text-red-100 mb-2">
						{t('regulation.errorLoading')}
					</h2>
					<p className="text-sm text-red-700 dark:text-red-300 mb-4">
						{error}
					</p>
					<Link
						to="/search"
						className="inline-flex items-center gap-2 text-sm font-medium text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
					>
						<span className="material-symbols-outlined text-base">
							arrow_back
						</span>
						{t('regulation.backToSearch')}
					</Link>
				</div>
			</div>
		);
	}

	if (!regulation) {
		return (
			<div className="flex flex-col items-center justify-center h-full animate-fade-in">
				<div className="text-center">
					<span className="material-symbols-outlined text-6xl text-slate-300 dark:text-zinc-600 mb-4">
						description
					</span>
					<h2 className="text-lg font-medium text-slate-700 dark:text-zinc-300 mb-2">
						{t('regulation.notFound')}
					</h2>
					<Link
						to="/search"
						className="inline-flex items-center gap-2 text-sm font-medium text-teal-600 dark:text-teal-400 hover:text-teal-700 dark:hover:text-teal-300"
					>
						<span className="material-symbols-outlined text-base">
							arrow_back
						</span>
						{t('regulation.backToSearch')}
					</Link>
				</div>
			</div>
		);
	}

	return (
		<div className="flex flex-col h-full animate-fade-in">
			<div className="max-w-5xl mx-auto w-full pt-8 px-12 pb-16">
				{/* Back Button */}
				<Link
					to="/search"
					className="inline-flex items-center gap-2 text-sm font-medium text-teal-600 dark:text-teal-400 hover:text-teal-700 dark:hover:text-teal-300 mb-8 transition-colors"
				>
					<span className="material-symbols-outlined text-base">
						arrow_back
					</span>
					{t('regulation.backToSearch')}
				</Link>

				{/* Header */}
				<div className="mb-12 animate-slide-up">
					<div className="flex items-center gap-3 mb-4">
						<span className="text-xs font-bold bg-slate-100 dark:bg-zinc-800 text-slate-500 dark:text-zinc-300 px-2 py-1 rounded uppercase">
							{regulation.jurisdiction} • {regulation.status}
						</span>
					</div>
					<h1 className="text-4xl font-light text-slate-900 dark:text-zinc-100 mb-4">
						{regulation.title}
					</h1>
					<div className="flex flex-wrap gap-6 text-sm text-slate-600 dark:text-zinc-400">
						<div className="flex items-center gap-2">
							<span className="material-symbols-outlined text-base">
								gavel
							</span>
							<span>
								<span className="font-medium">{t('regulation.citation')}:</span>{" "}
								{regulation.citation}
							</span>
						</div>
						<div className="flex items-center gap-2">
							<span className="material-symbols-outlined text-base">
								account_balance
							</span>
							<span>
								<span className="font-medium">{t('regulation.authority')}:</span>{" "}
								{regulation.authority}
							</span>
						</div>
						{regulation.effective_date && (
							<div className="flex items-center gap-2">
								<span className="material-symbols-outlined text-base">
									event
								</span>
								<span>
									<span className="font-medium">{t('regulation.effectiveDate')}:</span>{" "}
									{formatDate(regulation.effective_date)}
								</span>
							</div>
						)}
					</div>
				</div>

				{/* Content */}
				<div className="border-t border-slate-100 dark:border-zinc-800/60 pt-8">
					{regulation.sections && regulation.sections.length > 0 ? (
						<div className="space-y-8">
							<h2 className="text-2xl font-light text-slate-800 dark:text-zinc-200 mb-6">
								{t('regulation.sections')}
							</h2>
							{regulation.sections.map((section, idx) => (
								<div
									key={section.id}
									className="animate-slide-up border-l-2 border-teal-200 dark:border-teal-800 pl-6 py-2"
									style={{ animationDelay: `${idx * 50}ms` }}
								>
									<h3 className="text-lg font-medium text-slate-700 dark:text-zinc-300 mb-2">
										{t('regulation.section')} {section.number}
										{section.title && `: ${section.title}`}
									</h3>
									<div className="prose prose-slate dark:prose-invert max-w-none text-sm text-slate-600 dark:text-zinc-400 leading-relaxed">
										<p className="whitespace-pre-wrap">{section.content}</p>
									</div>
								</div>
							))}
						</div>
					) : (
						<div className="animate-slide-up">
							<h2 className="text-2xl font-light text-slate-800 dark:text-zinc-200 mb-6">
								{t('regulation.fullText')}
							</h2>
							<div className="prose prose-slate dark:prose-invert max-w-none text-sm text-slate-600 dark:text-zinc-400 leading-relaxed">
								<p className="whitespace-pre-wrap">{regulation.full_text}</p>
							</div>
						</div>
					)}
				</div>

				{/* Related Regulations Section */}
				{relationships && (relationships.counts.references > 0 || relationships.counts.referenced_by > 0 || relationships.counts.implements > 0) && (
					<div className="border-t border-slate-100 dark:border-zinc-800/60 pt-8 mt-12">
						<h2 className="text-2xl font-light text-slate-800 dark:text-zinc-200 mb-6">
							Related Regulations
						</h2>

						<div className="space-y-6">
							{/* Implements */}
							{relationships.implements.length > 0 && (
								<div className="bg-blue-50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-900/30 rounded-lg p-6">
									<h3 className="text-lg font-medium text-blue-900 dark:text-blue-100 mb-4 flex items-center gap-2">
										<span className="material-symbols-outlined text-base">account_balance</span>
										Implements ({relationships.counts.implements})
									</h3>
									<p className="text-sm text-blue-700 dark:text-blue-300 mb-4">
										Parent legislation that this regulation implements
									</p>
									<div className="space-y-2">
										{relationships.implements.map((doc) => (
											<Link
												key={doc.id}
												to={`/regulation/${doc.id}`}
												className="block bg-white dark:bg-zinc-800 rounded-md p-3 hover:shadow-md transition-shadow border border-blue-200 dark:border-blue-800"
											>
												<div className="flex items-start gap-3">
													<span className="material-symbols-outlined text-blue-500 dark:text-blue-400 mt-0.5">description</span>
													<div className="flex-1 min-w-0">
														<p className="font-medium text-slate-900 dark:text-zinc-100 truncate">{doc.title}</p>
														<p className="text-xs text-slate-500 dark:text-zinc-400 mt-1">{doc.type}</p>
													</div>
													<span className="material-symbols-outlined text-slate-400 dark:text-zinc-500">arrow_forward</span>
												</div>
											</Link>
										))}
									</div>
								</div>
							)}

							{/* References */}
							{relationships.references.length > 0 && (
								<div className="bg-teal-50 dark:bg-teal-900/10 border border-teal-100 dark:border-teal-900/30 rounded-lg p-6">
									<h3 className="text-lg font-medium text-teal-900 dark:text-teal-100 mb-4 flex items-center gap-2">
										<span className="material-symbols-outlined text-base">link</span>
										References ({relationships.counts.references})
									</h3>
									<p className="text-sm text-teal-700 dark:text-teal-300 mb-4">
										Documents that this regulation cites
									</p>
									<div className="space-y-2">
										{relationships.references.map((doc) => (
											<Link
												key={doc.id}
												to={`/regulation/${doc.id}`}
												className="block bg-white dark:bg-zinc-800 rounded-md p-3 hover:shadow-md transition-shadow border border-teal-200 dark:border-teal-800"
											>
												<div className="flex items-start gap-3">
													<span className="material-symbols-outlined text-teal-500 dark:text-teal-400 mt-0.5">description</span>
													<div className="flex-1 min-w-0">
														<p className="font-medium text-slate-900 dark:text-zinc-100 truncate">{doc.title}</p>
														<p className="text-xs text-slate-500 dark:text-zinc-400 mt-1">{doc.type}</p>
													</div>
													<span className="material-symbols-outlined text-slate-400 dark:text-zinc-500">arrow_forward</span>
												</div>
											</Link>
										))}
									</div>
								</div>
							)}

							{/* Referenced By */}
							{relationships.referenced_by.length > 0 && (
								<div className="bg-purple-50 dark:bg-purple-900/10 border border-purple-100 dark:border-purple-900/30 rounded-lg p-6">
									<h3 className="text-lg font-medium text-purple-900 dark:text-purple-100 mb-4 flex items-center gap-2">
										<span className="material-symbols-outlined text-base">published_with_changes</span>
										Referenced By ({relationships.counts.referenced_by})
									</h3>
									<p className="text-sm text-purple-700 dark:text-purple-300 mb-4">
										Documents that cite this regulation
									</p>
									<div className="space-y-2">
										{relationships.referenced_by.map((doc) => (
											<Link
												key={doc.id}
												to={`/regulation/${doc.id}`}
												className="block bg-white dark:bg-zinc-800 rounded-md p-3 hover:shadow-md transition-shadow border border-purple-200 dark:border-purple-800"
											>
												<div className="flex items-start gap-3">
													<span className="material-symbols-outlined text-purple-500 dark:text-purple-400 mt-0.5">description</span>
													<div className="flex-1 min-w-0">
														<p className="font-medium text-slate-900 dark:text-zinc-100 truncate">{doc.title}</p>
														<p className="text-xs text-slate-500 dark:text-zinc-400 mt-1">{doc.type}</p>
													</div>
													<span className="material-symbols-outlined text-slate-400 dark:text-zinc-500">arrow_forward</span>
												</div>
											</Link>
										))}
									</div>
								</div>
							)}
						</div>

						{relationshipsLoading && (
							<div className="flex items-center justify-center py-8">
								<LoadingSpinner size="sm" message="Loading relationships..." />
							</div>
						)}
					</div>
				)}
			</div>
		</div>
	);
}
