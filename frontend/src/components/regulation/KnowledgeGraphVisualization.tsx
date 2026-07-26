import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import type { RegulationRelationships } from "@/types";

interface KnowledgeGraphVisualizationProps {
	relationships: RegulationRelationships;
	currentRegulationTitle: string;
}

export function KnowledgeGraphVisualization({
	relationships,
	currentRegulationTitle,
}: KnowledgeGraphVisualizationProps) {
	const { t } = useTranslation();
	const [hoveredRelationship, setHoveredRelationship] = useState<{
		type: string;
		title: string;
	} | null>(null);

	const hasParents = relationships.implements.length > 0;
	const hasSiblings = relationships.references.length > 0;
	const hasChildren = relationships.referenced_by.length > 0;
	const hasImplementedBy = relationships.implemented_by.length > 0;
	const hasAppliesTo = relationships.applies_to.length > 0;

	if (!hasParents && !hasSiblings && !hasChildren && !hasImplementedBy && !hasAppliesTo) {
		return null;
	}

	return (
		<div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-zinc-900 dark:to-zinc-800 rounded-lg p-8 border border-slate-200 dark:border-zinc-700">
			<div className="mb-6">
				<h2 className="text-2xl font-light text-slate-800 dark:text-zinc-200 mb-2 flex items-center gap-2">
					<span className="material-symbols-outlined text-teal-500">
						account_tree
					</span>
					{t("regulation.knowledgeGraph")}
				</h2>
				<p className="text-sm text-slate-600 dark:text-zinc-400">
					{t("regulation.knowledgeGraphDesc")}
				</p>
				<p className="text-xs text-slate-500 dark:text-zinc-500 mt-1 italic">
					{t("regulation.hoverForDetails")}
				</p>
			</div>

			{/* Graph Visualization */}
			<div className="relative min-h-[400px] flex items-center justify-center">
				{/* Parent Nodes (Top) */}
				{hasParents && (
					<div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-md">
						<div className="text-center mb-3">
							<span className="text-xs font-medium text-blue-600 dark:text-blue-400 uppercase tracking-wide">
								{t("regulation.parent")}
							</span>
						</div>
						<div className="flex flex-col gap-2">
							{relationships.implements.map((doc) => (
								<div key={doc.id} className="relative">
									<Link
										to={`/regulation/${doc.id}`}
										className="block bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/30 border-2 border-blue-200 dark:border-blue-800 rounded-lg p-3 transition-all hover:shadow-md group"
										onMouseEnter={() =>
											setHoveredRelationship({
												type: t("regulation.implements"),
												title: doc.title,
											})
										}
										onMouseLeave={() => setHoveredRelationship(null)}
									>
										<div className="flex items-center gap-2">
											<span className="material-symbols-outlined text-blue-500 dark:text-blue-400 text-sm">
												account_balance
											</span>
											<span className="text-sm font-medium text-blue-900 dark:text-blue-100 line-clamp-1">
												{doc.title}
											</span>
											<span className="text-xs bg-blue-200 dark:bg-blue-800 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded ml-auto">
												{doc.type}
											</span>
										</div>
									</Link>
									{/* Connection Line */}
									<div className="absolute top-full left-1/2 w-0.5 h-8 bg-blue-300 dark:bg-blue-700 -translate-x-1/2" />
								</div>
							))}
						</div>
					</div>
				)}

				{/* Current Regulation (Center) */}
				<div
					className={`absolute ${hasParents ? "top-32" : "top-8"} left-1/2 -translate-x-1/2 w-full max-w-md`}
				>
					<div className="bg-white dark:bg-zinc-800 border-4 border-teal-400 dark:border-teal-600 rounded-lg p-4 shadow-lg">
						<div className="flex items-center gap-3">
							<span className="material-symbols-outlined text-teal-500 dark:text-teal-400 text-2xl">
								description
							</span>
							<div className="flex-1 min-w-0">
								<p className="text-xs text-slate-500 dark:text-zinc-400 uppercase tracking-wide mb-1">
									{t("regulation.details")}
								</p>
								<p className="text-sm font-medium text-slate-900 dark:text-zinc-100 line-clamp-2">
									{currentRegulationTitle}
								</p>
							</div>
						</div>
					</div>
				</div>

				{/* Sibling Nodes (Left) */}
				{hasSiblings && (
					<div
						className={`absolute ${hasParents ? "top-40" : "top-16"} left-4 w-64`}
					>
						<div className="text-center mb-3">
							<span className="text-xs font-medium text-teal-600 dark:text-teal-400 uppercase tracking-wide">
								{t("regulation.siblings")}
							</span>
						</div>
						<div className="flex flex-col gap-2 max-h-48 overflow-y-auto pr-2">
							{relationships.references.slice(0, 3).map((doc) => (
								<div key={doc.id} className="relative">
									{/* Connection Line */}
									<div className="absolute top-1/2 -right-4 w-12 h-0.5 bg-teal-300 dark:bg-teal-700" />
									<Link
										to={`/regulation/${doc.id}`}
										className="block bg-teal-50 dark:bg-teal-900/20 hover:bg-teal-100 dark:hover:bg-teal-900/30 border border-teal-200 dark:border-teal-800 rounded-lg p-2 transition-all hover:shadow-md text-xs group"
										onMouseEnter={() =>
											setHoveredRelationship({
												type: t("regulation.references"),
												title: doc.title,
											})
										}
										onMouseLeave={() => setHoveredRelationship(null)}
									>
										<div className="flex items-center gap-2">
											<span className="material-symbols-outlined text-teal-500 dark:text-teal-400 text-sm">
												link
											</span>
											<span className="text-teal-900 dark:text-teal-100 line-clamp-1 flex-1">
												{doc.title}
											</span>
										</div>
									</Link>
								</div>
							))}
							{relationships.references.length > 3 && (
								<p className="text-xs text-slate-500 dark:text-zinc-500 text-center">
									+{relationships.references.length - 3} more
								</p>
							)}
						</div>
					</div>
				)}

				{/* Children Nodes (Bottom) */}
				{(hasChildren || hasImplementedBy) && (
					<div
						className={`absolute ${hasParents ? "top-56" : "top-32"} left-1/2 -translate-x-1/2 w-full max-w-md`}
					>
						{/* Connection Line */}
						<div className="w-0.5 h-8 bg-purple-300 dark:bg-purple-700 mx-auto mb-2" />
						<div className="text-center mb-3">
							<span className="text-xs font-medium text-purple-600 dark:text-purple-400 uppercase tracking-wide">
								{t("regulation.children")}
							</span>
						</div>
						<div className="grid grid-cols-2 gap-2">
							{/* Referenced By */}
							{relationships.referenced_by.slice(0, 2).map((doc) => (
								<Link
									key={doc.id}
									to={`/regulation/${doc.id}`}
									className="block bg-purple-50 dark:bg-purple-900/20 hover:bg-purple-100 dark:hover:bg-purple-900/30 border border-purple-200 dark:border-purple-800 rounded-lg p-2 transition-all hover:shadow-md text-xs group"
									onMouseEnter={() =>
										setHoveredRelationship({
											type: t("regulation.referencedBy"),
											title: doc.title,
										})
									}
									onMouseLeave={() => setHoveredRelationship(null)}
								>
									<div className="flex items-center gap-2">
										<span className="material-symbols-outlined text-purple-500 dark:text-purple-400 text-sm">
											published_with_changes
										</span>
										<span className="text-purple-900 dark:text-purple-100 line-clamp-1 flex-1">
											{doc.title}
										</span>
									</div>
								</Link>
							))}
							{/* Implemented By */}
							{relationships.implemented_by.slice(0, 2).map((doc) => (
								<Link
									key={doc.id}
									to={`/regulation/${doc.id}`}
									className="block bg-orange-50 dark:bg-orange-900/20 hover:bg-orange-100 dark:hover:bg-orange-900/30 border border-orange-200 dark:border-orange-800 rounded-lg p-2 transition-all hover:shadow-md text-xs group"
									onMouseEnter={() =>
										setHoveredRelationship({
											type: t("regulation.implementedBy"),
											title: doc.title,
										})
									}
									onMouseLeave={() => setHoveredRelationship(null)}
								>
									<div className="flex items-center gap-2">
										<span className="material-symbols-outlined text-orange-500 dark:text-orange-400 text-sm">
											engineering
										</span>
										<span className="text-orange-900 dark:text-orange-100 line-clamp-1 flex-1">
											{doc.title}
										</span>
									</div>
								</Link>
							))}
							{(relationships.referenced_by.length + relationships.implemented_by.length > 4) && (
								<div className="col-span-2 text-xs text-slate-500 dark:text-zinc-500 text-center">
									+{(relationships.referenced_by.length + relationships.implemented_by.length) - 4} more
								</div>
							)}
						</div>
					</div>
				)}
				{/* Applies To Nodes (Right) */}
				{hasAppliesTo && (
					<div
						className={`absolute ${hasParents ? "top-40" : "top-16"} right-4 w-64`}
					>
						<div className="text-center mb-3">
							<span className="text-xs font-medium text-green-600 dark:text-green-400 uppercase tracking-wide">
								{t("regulation.appliesTo")}
							</span>
						</div>
						<div className="flex flex-col gap-2 max-h-48 overflow-y-auto pr-2">
							{relationships.applies_to.slice(0, 3).map((doc) => (
								<div key={doc.id} className="relative">
									{/* Connection Line */}
									<div className="absolute top-1/2 -left-4 w-12 h-0.5 bg-green-300 dark:bg-green-700" />
									<div className="block bg-green-50 dark:bg-green-900/20 hover:bg-green-100 dark:hover:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-lg p-2 transition-all hover:shadow-md text-xs group">
										<div className="flex items-center gap-2">
											<span className="material-symbols-outlined text-green-500 dark:text-green-400 text-sm">
												business
											</span>
											<span className="text-green-900 dark:text-green-100 line-clamp-1 flex-1">
												{doc.title || `Program ${doc.id.slice(0, 8)}`}
											</span>
										</div>
									</div>
								</div>
							))}
							{relationships.applies_to.length > 3 && (
								<p className="text-xs text-slate-500 dark:text-zinc-500 text-center">
									+{relationships.applies_to.length - 3} more
								</p>
							)}
						</div>
					</div>
				)}
			</div>

			{/* Hover Tooltip */}
			{hoveredRelationship && (
				<div className="mt-6 p-4 bg-white dark:bg-zinc-800 border-l-4 border-teal-400 dark:border-teal-600 rounded-r-lg shadow-sm">
					<div className="flex items-start gap-3">
						<span className="material-symbols-outlined text-teal-500 dark:text-teal-400">
							info
						</span>
						<div>
							<p className="text-xs text-slate-500 dark:text-zinc-400 uppercase tracking-wide mb-1">
								{t("regulation.relationshipType")}
							</p>
							<p className="text-sm font-medium text-slate-700 dark:text-zinc-300">
								{hoveredRelationship.type}
							</p>
							<p className="text-xs text-slate-600 dark:text-zinc-400 mt-2 line-clamp-2">
								{hoveredRelationship.title}
							</p>
						</div>
					</div>
				</div>
			)}
		</div>
	);
}
