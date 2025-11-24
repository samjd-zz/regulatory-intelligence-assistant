import { useState } from 'react'
import { Send } from 'lucide-react'
import { useChatStore } from '@/store/chatStore'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { ConfidenceBadge } from '@/components/shared/ConfidenceBadge'
import { CitationTag } from '@/components/shared/CitationTag'
import { formatDate } from '@/lib/utils'

export function Chat() {
  const { messages, loading, error, sendMessage } = useChatStore()
  const [input, setInput] = useState('')

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !loading) {
      await sendMessage(input.trim())
      setInput('')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <div className="bg-white border-b border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-900">
            Ask Questions About Regulations
          </h1>
          <p className="text-gray-600 mt-1">
            Get AI-powered answers with legal citations
          </p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-600 mb-4">
                No messages yet. Ask a question to get started!
              </p>
              <p className="text-sm text-gray-500">
                Example: "Can a temporary resident apply for employment insurance?"
              </p>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-3xl rounded-lg p-4 ${
                  message.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-white shadow'
                }`}
              >
                {message.role === 'assistant' && (
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-semibold text-gray-900">
                      AI Assistant
                    </span>
                    {message.confidence !== undefined && (
                      <ConfidenceBadge score={message.confidence} size="sm" />
                    )}
                  </div>
                )}

                <p
                  className={
                    message.role === 'user' ? 'text-white' : 'text-gray-900'
                  }
                >
                  {message.content}
                </p>

                {message.citations && message.citations.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <p className="text-sm font-semibold text-gray-700 mb-2">
                      📚 Sources:
                    </p>
                    <div className="space-y-2">
                      {message.citations.map((citation, idx) => (
                        <div key={idx} className="flex items-center gap-2">
                          <span className="text-sm text-gray-600">
                            [{idx + 1}]
                          </span>
                          <CitationTag
                            citation={`${citation.title}, ${citation.section}`}
                            variant="compact"
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <p className="text-xs text-gray-400 mt-2">
                  {formatDate(message.timestamp)}
                </p>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-white shadow rounded-lg p-4">
                <LoadingSpinner size="sm" message="Thinking..." />
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSend} className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your question here..."
              className="flex-1 rounded-lg border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
              aria-label="Question input"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Send className="w-5 h-5" />
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
