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
    "px-3 py-1.5 text-sm font-medium flex items-center gap-1 rounded-lg hover:bg-[var(--surface)] transition-colors"

  return (
    <header className="w-full border-b shadow-sm transition-colors bg-[var(--navbar-bg)] border-[var(--border)]">
      <div className="max-w-6xl mx-auto flex justify-between items-center py-3 px-6">
        <div
          className="text-xl font-bold cursor-pointer text-[var(--accent)] transition-colors"
          onClick={() => navigate('/')}
        >
          PortoFino
        </div>

        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/')} className={navButton}>
            <Home size={16} /> Dashboard
          </button>
          {accessToken && (
            <button onClick={() => navigate('/history')} className={navButton}>
              <History size={16} /> History
            </button>
          )}
        </div>

        <div className="flex items-center gap-3">
          {!accessToken ? (
            <>
              <button
                onClick={onShowLogin}
                className="px-3 py-1.5 font-medium rounded-lg shadow-md disabled:opacity-50 hover:bg-[var(--accent-hover)] transition-colors text-[var(--btn-accent-text)] bg-[var(--accent)]"
              >
                Log in
              </button>
              <button
                onClick={onShowSignup}
                className="px-3 py-1.5 text-sm font-medium rounded-lg bg-[var(--btn-accent)] hover:bg-[var(--btn-accent-hover)] text-[var(--text)] transition-colors"
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
            className="ml-2 p-2 rounded-full hover:bg-[var(--surface)] transition-colors"
          >
            {dark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
      </div>
    </header>
  )
}
