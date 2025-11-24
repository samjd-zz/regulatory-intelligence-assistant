import { Link, useLocation } from 'react-router-dom'
import { Search, MessageSquare, CheckCircle, LayoutDashboard } from 'lucide-react'

export function Header() {
  const location = useLocation()

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/search', label: 'Search', icon: Search },
    { path: '/chat', label: 'Q&A Chat', icon: MessageSquare },
    { path: '/compliance', label: 'Compliance', icon: CheckCircle },
  ]

  const isActive = (path: string) => {
    return location.pathname === path
  }

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo/Title */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">R</span>
              </div>
              <span className="text-xl font-semibold text-gray-900">
                Regulatory Intelligence
              </span>
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className="flex space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const active = isActive(item.path)
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`
                    flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors
                    ${active 
                      ? 'bg-blue-50 text-blue-700' 
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }
                  `}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </nav>
        </div>
      </div>
    </header>
  )
}
