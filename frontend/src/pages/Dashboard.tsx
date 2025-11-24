import { Search, MessageSquare, CheckCircle } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export function Dashboard() {
  const navigate = useNavigate()

  const quickActions = [
    {
      icon: Search,
      title: 'Search Regulations',
      description: 'Find relevant regulations using natural language search',
      path: '/search',
      color: 'bg-blue-500',
    },
    {
      icon: MessageSquare,
      title: 'Ask Questions',
      description: 'Get answers about regulations with AI assistance',
      path: '/chat',
      color: 'bg-green-500',
    },
    {
      icon: CheckCircle,
      title: 'Check Compliance',
      description: 'Validate forms and applications against regulations',
      path: '/compliance',
      color: 'bg-purple-500',
    },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            Regulatory Intelligence Assistant
          </h1>
          <p className="mt-2 text-gray-600">
            Navigate complex regulations with AI-powered assistance
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Welcome Section */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            Welcome to the Regulatory Intelligence Assistant
          </h2>
          <p className="text-gray-600">
            This AI-powered platform helps public servants and citizens navigate complex
            laws, policies, and regulations. Get started by choosing an action below.
          </p>
        </div>

        {/* Quick Actions Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {quickActions.map((action) => (
            <button
              key={action.path}
              onClick={() => navigate(action.path)}
              className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 text-left group"
            >
              <div
                className={`${action.color} w-12 h-12 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}
              >
                <action.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {action.title}
              </h3>
              <p className="text-gray-600">{action.description}</p>
            </button>
          ))}
        </div>

        {/* Stats Section */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-3xl font-bold text-blue-600 mb-2">1,245</div>
            <div className="text-gray-600">Regulations Indexed</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-3xl font-bold text-green-600 mb-2">&lt;3s</div>
            <div className="text-gray-600">Average Response Time</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-3xl font-bold text-purple-600 mb-2">95%</div>
            <div className="text-gray-600">Search Accuracy</div>
          </div>
        </div>
      </main>
    </div>
  )
}
