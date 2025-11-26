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
				className="flex-1 overflow-y-auto px-12 py-8 scroll-smooth"
			>
				{messages.length === 0 && (
					<div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto animate-scale-in">
						<h2 className="text-2xl font-light text-slate-900 mb-3">
							Regulatory Assistant
						</h2>
						<p className="text-sm text-slate-400">
							Ask questions about specific mandates. Citations included
							automatically.
						</p>
					</div>
				)}

				{messages.map((message, idx) => (
					<div
						key={message.id}
						className={`flex mb-8 animate-slide-up ${
							message.role === "user" ? "justify-end" : "justify-start"
						}`}
						style={{ animationDelay: `${idx * 50}ms` }}
					>
						{message.role === "user" ? (
							<div className="bg-slate-50 border border-slate-100 text-slate-800 px-6 py-4 text-sm max-w-lg leading-relaxed message-bubble">
								{message.content}
							</div>
						) : (
							<div className="flex gap-4 max-w-lg">
								<div className="w-6 h-6 bg-teal-600 shrink-0 mt-1 rounded-full" />
								<div>
									{message.confidence !== undefined && (
										<div className="mb-2">
											<ConfidenceBadge score={message.confidence} size="sm" />
										</div>
									)}
									<p className="text-sm text-slate-600 leading-relaxed mb-3">
										{message.content}
									</p>
									{message.citations && message.citations.length > 0 && (
										<div className="space-y-2 mb-3">
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
									<p className="text-[10px] font-bold text-slate-400 uppercase">
										{formatDate(message.timestamp)}
									</p>
								</div>
							</div>
						)}
					</div>
				))}

				{loading && (
					<div className="flex justify-start mb-8 animate-slide-up">
						<div className="flex gap-4 max-w-lg">
							<div className="w-6 h-6 bg-teal-600 shrink-0 mt-1 rounded-full animate-pulse" />
							<div>
								<LoadingSpinner size="sm" message="Thinking..." />
							</div>
						</div>
					</div>
				)}

				{error && (
					<div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800 animate-scale-in">
						{error}
					</div>
				)}
			</div>

			{/* Input Area */}
			<div className="px-12 py-10 border-t border-slate-50 bg-white z-10 animate-slide-up delay-100">
				<div className="max-w-3xl mx-auto flex items-end gap-4">
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
							className="input-minimal"
							disabled={loading}
							aria-label="Question input"
						/>
					</div>
					<button
						type="button"
						onClick={handleSend}
						disabled={loading || !input.trim()}
						className="bg-teal-600 text-white px-6 py-3 text-xs font-bold uppercase tracking-wide hover:bg-teal-700 hover:shadow-lg hover:-translate-y-0.5 transition-all active:translate-y-0 disabled:opacity-50 disabled:cursor-not-allowed"
					>
						Send
					</button>
				</div>
			</div>
		</div>
	);
}
