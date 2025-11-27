import React from 'react'
import { render, screen } from '@testing-library/react'
import App from '../../src/App'
import { describe, it, expect } from 'vitest'

describe('App component', () => {
  it('renders the main title', () => {
    render(<App />)
    expect(screen.getByText(/PortoFino Portfolio Simulator/i)).toBeInTheDocument()
  })
})
