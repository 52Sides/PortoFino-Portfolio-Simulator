import { useState, useEffect } from 'react'
import api from '../api/client'
import { useAuthStore } from '../store/auth'

export default function LoginForm({ onClose }: { onClose: () => void }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const setTokens = useAuthStore((s) => s.setTokens)
  const [error, setError] = useState('')

  useEffect(() => {
    return () => {
      setEmail('')
      setPassword('')
      setError('')
      setLoading(false)
    }
  }, [])

  const validate = () => {
    if (!email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
      setError('Invalid email address')
      return false
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters')
      return false
    }
    setError('')
    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.append('grant_type', 'password')
      params.append('username', email)
      params.append('password', password)

      const resp = await api.post('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })

      const { access_token, refresh_token } = resp.data
      setTokens(access_token, refresh_token)
      onClose()
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Login failed. Check your credentials.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50 bg-black/50 backdrop-blur-sm">
      <form
        onSubmit={handleSubmit}
        className="w-96 bg-[var(--surface)] text-[var(--text)] rounded-2xl shadow-xl p-8 flex flex-col transition-colors duration-300"
      >
        <h2 className="text-2xl font-bold mb-4 text-center">Log in</h2>

        {error && <p className="text-red-500 mb-3 text-center">{error}</p>}

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full mb-3 p-3 rounded-lg border border-[var(--border)] bg-[var(--surface)] text-[var(--text)] placeholder:text-[var(--text-muted)] focus:ring-2 focus:ring-[var(--accent)] transition-all"
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full mb-4 p-3 rounded-lg border border-[var(--border)] bg-[var(--surface)] text-[var(--text)] placeholder:text-[var(--text-muted)] focus:ring-2 focus:ring-[var(--accent)] transition-all"
          required
        />

        <button
          type="submit"
          data-testid="signup-submit"
          disabled={loading}
          className="mt-4 w-full py-3 font-medium rounded-lg shadow-md disabled:opacity-50 hover:bg-[var(--accent-hover)] transition-colors text-[var(--btn-accent-text)] bg-[var(--accent)]"
        >
          {loading && <span className="animate-spin mr-2 border-2 border-[var(--btn-accent-text)] border-t-transparent rounded-full w-5 h-5"></span>}
          {loading ? 'Logging in...' : 'Log in'}
        </button>

        <button
          type="button"
          onClick={onClose}
          className="w-full mt-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] font-medium hover:bg-[var(--btn-default-hover)] transition-colors"
        >
          Cancel
        </button>

        <a
          href={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/auth/google/login`}
          className="w-full mt-4 py-3 text-center border border-[var(--border)] rounded-lg hover:bg-[var(--btn-default-hover)] transition-colors"
        >
          Continue with Google
        </a>
      </form>
    </div>
  )
}
