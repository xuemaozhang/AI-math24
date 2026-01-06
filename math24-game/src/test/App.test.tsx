import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from '../App'

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    expect(screen.getByText('Math 24')).toBeInTheDocument()
  })

  it('renders the Math24Game component', () => {
    render(<App />)
    expect(screen.getByText(/Use each number once to build 24/i)).toBeInTheDocument()
  })

  it('has the app-shell wrapper', () => {
    const { container } = render(<App />)
    expect(container.querySelector('.app-shell')).toBeInTheDocument()
  })
})
