import { Link, useLocation } from 'react-router-dom';

export default function Layout({ children }) {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="flex items-center gap-2">
                <span className="text-2xl font-bold bg-gradient-to-r from-primary-600 to-accent-500 bg-clip-text text-transparent">
                  AI Resume ATS
                </span>
                <span className="text-sm text-slate-500 hidden sm:inline">Scanner</span>
              </Link>
            </div>
            <div className="flex items-center gap-4">
              <Link
                to="/"
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  location.pathname === '/' ? 'bg-primary-100 text-primary-700' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                Home
              </Link>
              <Link
                to="/results"
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  location.pathname === '/results' ? 'bg-primary-100 text-primary-700' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                Results
              </Link>
              <Link
                to="/history"
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  location.pathname === '/history' ? 'bg-primary-100 text-primary-700' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                History
              </Link>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}
