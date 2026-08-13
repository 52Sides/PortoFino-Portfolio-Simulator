import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Moon, Sun, LogOut, History, Home } from 'lucide-react'
import { useAuthStore } from '../store/auth'
import api from '../api/client'

interface NavbarProps {
  dark: boolean
  setDark: (v: boolean) => void
  onShowLogin: () => void
  onShowSignup: () => void
}

export default function Navbar({ dark, setDark, onShowLogin, onShowSignup }: NavbarProps) {
  const { accessToken, refreshToken, clear } = useAuthStore()
  const navigate = useNavigate()
  const [loadingLogout, setLoadingLogout] = useState(false)

  const toggleTheme = () => {
    setDark(!dark)
    document.documentElement.classList.toggle('dark', !dark)
  }

  const handleLogout = async () => {
    if (!accessToken) return
    setLoadingLogout(true)
    try {
      if (refreshToken) await api.post('/auth/logout', { refresh_token: refreshToken })
      clear()
      navigate('/')
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingLogout(false)
    }
  }

  const navButton =
    "px-2 py-1.5 sm:px-3 text-sm font-medium flex items-center gap-1 rounded-lg hover:bg-[var(--surface)] transition-colors whitespace-nowrap"

  return (
    <header className="w-full border-b shadow-sm transition-colors bg-[var(--navbar-bg)] border-[var(--border)]">
      <div className="max-w-6xl mx-auto flex justify-between items-center gap-2 py-3 px-3 sm:px-6">
        <div
          className="text-lg sm:text-xl font-bold cursor-pointer text-[var(--accent)] transition-colors whitespace-nowrap"
          onClick={() => navigate('/')}
        >
          PortoFino
        </div>

        <div className="flex items-center gap-1 sm:gap-3">
          <button onClick={() => navigate('/')} className={navButton} aria-label="Dashboard">
            <Home size={16} />
            <span className="hidden sm:inline">Dashboard</span>
          </button>
          {accessToken && (
            <button onClick={() => navigate('/history')} className={navButton} aria-label="History">
              <History size={16} />
              <span className="hidden sm:inline">History</span>
            </button>
          )}
        </div>

        <div className="flex items-center gap-1 sm:gap-3">
          {!accessToken ? (
            <>
              <button
                onClick={onShowLogin}
                className="px-2.5 py-1.5 sm:px-3 text-sm font-medium rounded-lg shadow-md disabled:opacity-50 hover:bg-[var(--accent-hover)] transition-colors text-[var(--btn-accent-text)] bg-[var(--accent)] whitespace-nowrap"
              >
                Log in
              </button>
              <button
                onClick={onShowSignup}
                className="px-2.5 py-1.5 sm:px-3 text-sm font-medium rounded-lg bg-[var(--btn-accent)] hover:bg-[var(--btn-accent-hover)] text-[var(--text)] transition-colors whitespace-nowrap"
              >
                Sign up
              </button>
            </>
          ) : (
            <button
              onClick={handleLogout}
              disabled={loadingLogout}
              className={`${navButton} hover:text-red-500`}
            >
              {loadingLogout ? 'Logging out...' : <><LogOut size={16} /> Logout</>}
            </button>
          )}

          <button
            onClick={toggleTheme}
            className="p-2 rounded-full hover:bg-[var(--surface)] transition-colors shrink-0"
            aria-label="Toggle theme"
          >
            {dark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
      </div>
    </header>
  )
}
