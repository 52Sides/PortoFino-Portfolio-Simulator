import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import HistoryPage from '../../src/pages/HistoryPage'
import api from '../../src/api/client'
import { useAuthStore } from '../../src/store/auth'
import { vi, MockedFunction } from 'vitest'

vi.mock('../../src/api/client')
const mockedApiGet = api.get as MockedFunction<typeof api.get>

describe('HistoryPage', () => {
  beforeEach(() => {
    useAuthStore.setState({ accessToken: 'token', refreshToken: 'refresh' })
  })

  it('renders empty state if no simulations', async () => {
    mockedApiGet.mockResolvedValueOnce({ data: { root: [], total: 0 } })

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
    mockedApiGet.mockResolvedValueOnce({
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
      expect(screen.getByText('View')).toBeInTheDocument()
      expect(screen.getByText('Download')).toBeInTheDocument()
    })
  })
})
