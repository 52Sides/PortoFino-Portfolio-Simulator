import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import HistoryPage from '../../src/pages/HistoryPage'
import api from '../../src/api/client'
import { useAuthStore } from '../../src/store/auth'
import { vi } from 'vitest'

vi.mock('../../src/api/client')

describe('HistoryPage', () => {
  beforeEach(() => {
    useAuthStore.setState({ accessToken: 'token', refreshToken: 'refresh' })
  })

  it('renders empty state if no simulations', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: { root: [], total: 0 } })

    render(
      <MemoryRouter>
        <HistoryPage />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/No simulations yet/i)).toBeInTheDocument()
    })
  })

  it('renders simulation rows correctly', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: {
        root: [
          {
            id: 1,
            command: 'TSLA-L',
            created_at: new Date().toISOString(),
            cagr: 0.12,
            sharpe: 1.3,
            max_drawdown: 0.2,
            portfolio_value: { '2020-01-01': 100, '2021-01-01': 120 },
          },
        ],
        total: 1,
      },
    })

    render(
      <MemoryRouter>
        <HistoryPage />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('TSLA-L')).toBeInTheDocument()
      expect(screen.getByTitle('View Details')).toBeInTheDocument()
      expect(screen.getByTitle('Download Report')).toBeInTheDocument()
    })
  })
})
