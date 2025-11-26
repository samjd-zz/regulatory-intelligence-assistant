import { useState, useRef, useCallback } from "react";
import { useChatStore } from "@/store/chatStore";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { ConfidenceBadge } from "@/components/shared/ConfidenceBadge";
import { CitationTag } from "@/components/shared/CitationTag";
import { formatDate } from "@/lib/utils";

export function Chat() {
	const { messages, loading, error, sendMessage } = useChatStore();
	const [input, setInput] = useState("");
	const containerRef = useRef<HTMLDivElement>(null);

	const scrollToBottom = useCallback(() => {
		if (containerRef.current) {
			containerRef.current.scrollTop = containerRef.current.scrollHeight;
		}
	}, []);

	const handleSend = async (e: React.FormEvent) => {
		e.preventDefault();
		if (input.trim() && !loading) {
			await sendMessage(input.trim());
			setInput("");
			setTimeout(scrollToBottom, 100);
		}
	};

	return (
		<div className="flex flex-col h-full animate-fade-in">
			{/* Messages Container */}
			<div
				ref={containerRef}
				className="flex-1 overflow-y-auto px-6 md:px-12 py-8 scroll-smooth"
			>
				{messages.length === 0 && (
					<div className="h-full flex flex-col items-center justify-center text-center animate-scale-in">
						<div className="relative mb-6 group cursor-default">
							<div className="absolute inset-0 bg-teal-100 rounded-full blur-xl opacity-20 group-hover:opacity-40 transition-opacity duration-500" />
							<span className="material-symbols-outlined text-6xl text-slate-300 relative z-10 transition-transform duration-500 group-hover:scale-110 group-hover:text-teal-500/50">
								forum
							</span>
						</div>
						<h2 className="text-2xl font-light text-slate-900 mb-3">
							Regulatory Assistant
						</h2>
						<p className="text-sm text-slate-400 max-w-md mx-auto leading-relaxed">
							Ask questions about specific mandates. Citations included
							automatically.
						</p>
					</div>
				)}

				{messages.map((message, idx) => (
					<div
						key={message.id}
						className={`flex mb-12 animate-slide-up ${
							message.role === "user" ? "justify-end" : "justify-start"
						}`}
						style={{ animationDelay: `${idx * 50}ms` }}
					>
						{message.role === "user" ? (
							<div className="flex gap-6 max-w-3xl justify-end w-full">
								<div className="text-right">
									<div className="text-2xl md:text-3xl font-light text-slate-900 leading-tight">
										{message.content}
									</div>
									<p className="text-[10px] font-bold text-slate-300 uppercase tracking-widest mt-3">
										You • {formatDate(message.timestamp)}
									</p>
								</div>
								<div className="w-1 h-full min-h-6 bg-slate-200 shrink-0" />
							</div>
						) : (
							<div className="flex gap-6 max-w-3xl">
								<div className="w-1 h-full min-h-6 bg-teal-600 shrink-0" />
								<div>
									{message.confidence !== undefined && (
										<div className="mb-4">
											<ConfidenceBadge score={message.confidence} size="sm" />
										</div>
									)}
									<p className="text-lg text-slate-700 leading-relaxed mb-6">
										{message.content}
									</p>
									{message.citations && message.citations.length > 0 && (
										<div className="space-y-3 mb-4">
											{message.citations.map((citation) => (
												<div
													key={`${citation.title}-${citation.section}`}
													className="flex items-center gap-2"
												>
													<CitationTag
														citation={`${citation.title}, ${citation.section}`}
														variant="compact"
													/>
												</div>
											))}
										</div>
									)}
									<p className="text-[10px] font-bold text-slate-300 uppercase tracking-widest">
										{formatDate(message.timestamp)}
									</p>
								</div>
							</div>
						)}
					</div>
				))}

				{loading && (
					<div className="flex justify-start mb-12 animate-slide-up">
						<div className="flex gap-6 max-w-3xl">
							<div className="w-1 h-full min-h-6 bg-teal-600 shrink-0 animate-pulse" />
							<div>
								<LoadingSpinner size="sm" message="Thinking..." />
							</div>
						</div>
					</div>
				)}

				{error && (
					<div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800 animate-scale-in max-w-3xl mx-auto mb-8 flex items-start gap-3">
						<span className="material-symbols-outlined text-red-500 mt-0.5">
							error
						</span>
						<div>
							<p className="font-medium text-red-900">Error</p>
							<p className="text-sm text-red-700">{error}</p>
						</div>
					</div>
				)}
			</div>

			{/* Input Area */}
			<div className="px-6 md:px-12 py-10 border-t border-slate-100 bg-white z-10 animate-slide-up delay-100">
				<div className="max-w-4xl mx-auto flex items-end gap-6">
					<div className="flex-1">
						<input
							type="text"
							id="chat-input"
							value={input}
							onChange={(e) => setInput(e.target.value)}
							onKeyDown={(e) => {
								if (e.key === "Enter" && !e.shiftKey) {
									e.preventDefault();
									handleSend(e);
								}
							}}
							placeholder="Type your question here..."
							className="w-full text-xl font-light text-slate-900 border-b border-slate-200 pb-4 px-2 outline-none focus:border-teal-600 placeholder-slate-300 bg-transparent transition-colors duration-300"
							disabled={loading}
							aria-label="Question input"
						/>
					</div>
					<button
						type="button"
						onClick={handleSend}
						disabled={loading || !input.trim()}
						className="text-slate-400 hover:text-teal-600 transition-transform hover:scale-110 active:scale-95 disabled:opacity-50 mb-2"
					>
						<span className="material-symbols-outlined text-3xl">send</span>
					</button>
				</div>
			</div>
		</div>
	);
}
