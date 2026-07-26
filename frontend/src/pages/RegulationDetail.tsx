import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";

import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { KnowledgeGraphVisualization } from "@/components/regulation/KnowledgeGraphVisualization";
import { AmendmentTimeline } from "@/components/regulation/AmendmentTimeline";
import { formatDate } from "@/lib/utils";
import { getRegulationDetail, getRegulationRelationships, getRegulationAmendments } from "@/services/api";
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

interface AmendmentData {
	id: string;
	amendment_type: string;
	effective_date: string | null;
	description: string;
	created_at: string;
}

export function RegulationDetail() {
	const { t } = useTranslation();
	const { id } = useParams<{ id: string }>();
	const [regulation, setRegulation] = useState<RegulationData | null>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [relationships, setRelationships] = useState<RegulationRelationships | null>(null);
	const [amendments, setAmendments] = useState<AmendmentData[]>([]);

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
			const data = await getRegulationRelationships(id!);
			if (!cancelled) {
				setRelationships(data);
			}
		} catch (err) {
			if (!cancelled) {
				console.error("Error fetching relationships:", err);
				// Non-critical error - don't show error to user
			}
		}
	}

		fetchRelationships();

		return () => {
			cancelled = true;
		};
	}, [id, regulation]);

	// Fetch regulation amendments
	useEffect(() => {
		if (!id) return;

		let cancelled = false;

		async function fetchAmendments() {
			try {
				const data = await getRegulationAmendments(id!);
				if (!cancelled) {
					setAmendments(data.amendments || []);
				}
			} catch (err) {
				if (!cancelled) {
					console.error("Error fetching amendments:", err);
					// Non-critical error - don't show error to user
				}
			}
		}

		fetchAmendments();

		return () => {
			cancelled = true;
		};
	}, [id]);

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
				<h1 className="text-4xl font-light text-slate-900 dark:text-zinc-100 mb-6">
					{regulation.title}
				</h1>

				{/* Metadata Cards */}
				<div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
					{/* Citation Card */}
					{regulation.citation && regulation.citation.trim() !== "" && (
						<div className="bg-white dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 rounded-lg p-4 hover:shadow-md transition-shadow">
							<div className="flex items-start gap-3">
								<span className="material-symbols-outlined text-teal-500 dark:text-teal-400 mt-0.5">
									gavel
								</span>
								<div className="flex-1 min-w-0">
									<p className="text-xs text-slate-500 dark:text-zinc-400 uppercase tracking-wide mb-1">
										{t('regulation.citation')}
									</p>
									<p className="text-sm font-medium text-slate-900 dark:text-zinc-100 font-mono break-words">
										{regulation.citation}
									</p>
								</div>
							</div>
						</div>
					)}

					{/* Authority Card */}
					{regulation.authority && regulation.authority.trim() !== "" && (
						<div className="bg-white dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 rounded-lg p-4 hover:shadow-md transition-shadow">
							<div className="flex items-start gap-3">
								<span className="material-symbols-outlined text-blue-500 dark:text-blue-400 mt-0.5">
									account_balance
								</span>
								<div className="flex-1 min-w-0">
									<p className="text-xs text-slate-500 dark:text-zinc-400 uppercase tracking-wide mb-1">
										{t('regulation.authority')}
									</p>
									<p className="text-sm font-medium text-slate-900 dark:text-zinc-100 break-words">
										{regulation.authority}
									</p>
								</div>
							</div>
						</div>
					)}

					{/* Effective Date Card */}
					{regulation.effective_date && (
						<div className="bg-white dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 rounded-lg p-4 hover:shadow-md transition-shadow">
							<div className="flex items-start gap-3">
								<span className="material-symbols-outlined text-purple-500 dark:text-purple-400 mt-0.5">
									event
								</span>
								<div className="flex-1 min-w-0">
									<p className="text-xs text-slate-500 dark:text-zinc-400 uppercase tracking-wide mb-1">
										{t('regulation.effectiveDate')}
									</p>
									<p className="text-sm font-medium text-slate-900 dark:text-zinc-100">
										{formatDate(regulation.effective_date)}
									</p>
								</div>
							</div>
						</div>
					)}
				</div>
			</div>

			{/* Knowledge Graph Section */}
			{relationships && (
				<div className="mb-12">
					<KnowledgeGraphVisualization
						relationships={relationships}
						currentRegulationTitle={regulation.title}
					/>
				</div>
			)}

			{/* Amendment Timeline Section */}
			<div className="mb-12">
				<AmendmentTimeline
					amendments={amendments.map(a => ({
						id: a.id,
						date: a.effective_date || a.created_at,
						type: (a.amendment_type.toLowerCase().includes('repeal') ? 'repealed' :
							   a.amendment_type.toLowerCase().includes('add') ? 'added' : 'amended') as 'amended' | 'added' | 'repealed',
						description: a.description || a.amendment_type,
						citation: undefined
					}))}
					effectiveDate={regulation.effective_date}
				/>
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

			</div>
		</div>
	);
}
