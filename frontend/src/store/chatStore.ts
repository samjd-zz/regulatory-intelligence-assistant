import { create } from "zustand";
import type { Message, QAResponse } from "@/types";
import { askQuestion } from "@/services/api";

interface ChatState {
	messages: Message[];
	currentQuestion: string;
	loading: boolean;
	error: string | null;

	// Actions
	setCurrentQuestion: (question: string) => void;
	sendMessage: (
		content: string,
		context?: Record<string, unknown>,
	) => Promise<void>;
	addMessage: (message: Message) => void;
	clearChat: () => void;
	setLoading: (loading: boolean) => void;
	setError: (error: string | null) => void;
}

export const useChatStore = create<ChatState>((set, _get) => ({
	messages: [],
	currentQuestion: "",
	loading: false,
	error: null,

	setCurrentQuestion: (question) => set({ currentQuestion: question }),

	sendMessage: async (content: string, context?: Record<string, unknown>) => {
		// Add user message
		const userMessage: Message = {
			id: `user-${Date.now()}`,
			role: "user",
			content,
			timestamp: new Date(),
		};

		set((state) => ({
			messages: [...state.messages, userMessage],
			loading: true,
			error: null,
			currentQuestion: "",
		}));

		try {
			const response: QAResponse = await askQuestion({
				question: content,
				context,
			});

			// Add assistant message
			const assistantMessage: Message = {
				id: `assistant-${Date.now()}`,
				role: "assistant",
				content: response.answer,
				citations: (response.sources || []).map((source) => ({
					regulation_id: "",
					title: source.regulation,
					section: source.section,
					citation_text: source.citation,
				})),
				confidence:
					response.confidence === "high"
						? 0.9
						: response.confidence === "medium"
							? 0.7
							: 0.5,
				timestamp: new Date(),
			};

			set((state) => ({
				messages: [...state.messages, assistantMessage],
				loading: false,
			}));
		} catch (error) {
			set({
				error:
					error instanceof Error ? error.message : "Failed to get response",
				loading: false,
			});
		}
	},

	addMessage: (message) =>
		set((state) => ({
			messages: [...state.messages, message],
		})),

	clearChat: () =>
		set({
			messages: [],
			currentQuestion: "",
			error: null,
		}),

	setLoading: (loading) => set({ loading }),

	setError: (error) => set({ error }),
}));
