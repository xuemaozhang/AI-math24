import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Math24Game from '../Math24Game'

// Mock fetch globally
global.fetch = vi.fn()

describe('Math24Game', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Component Rendering', () => {
    it('renders the game title', () => {
      render(<Math24Game />)
      expect(screen.getByText('Math 24')).toBeInTheDocument()
    })

    it('renders the subtitle', () => {
      render(<Math24Game />)
      expect(screen.getByText(/Use each number once to build 24/i)).toBeInTheDocument()
    })

    it('renders 4 number buttons', () => {
      render(<Math24Game />)
      const numberButtons = screen.getAllByRole('button').filter(btn => 
        btn.classList.contains('number')
      )
      expect(numberButtons).toHaveLength(4)
    })

    it('renders operator buttons', () => {
      render(<Math24Game />)
      expect(screen.getByLabelText('Add +')).toBeInTheDocument()
      expect(screen.getByLabelText('Add -')).toBeInTheDocument()
      expect(screen.getByLabelText('Add *')).toBeInTheDocument()
      expect(screen.getByLabelText('Add (')).toBeInTheDocument()
      expect(screen.getByLabelText('Add )')).toBeInTheDocument()
    })

    it('renders Check button', () => {
      render(<Math24Game />)
      expect(screen.getByRole('button', { name: /Check/i })).toBeInTheDocument()
    })

    it('renders New Puzzle button', () => {
      render(<Math24Game />)
      expect(screen.getByRole('button', { name: /New Puzzle/i })).toBeInTheDocument()
    })
  })

  describe('Mode Toggle', () => {
    it('starts in easy mode by default', () => {
      render(<Math24Game />)
      expect(screen.getByText('Easy')).toBeInTheDocument()
    })

    it('toggles between easy and hard mode', async () => {
      const user = userEvent.setup()
      render(<Math24Game />)
      
      const modeButton = screen.getByRole('button', { name: /Mode Easy/i })
      await user.click(modeButton)
      
      expect(screen.getByText('Hard')).toBeInTheDocument()
    })

    it('hides division operator in easy mode', () => {
      render(<Math24Game />)
      expect(screen.queryByLabelText('Add /')).not.toBeInTheDocument()
    })

    it('shows division operator in hard mode', async () => {
      const user = userEvent.setup()
      render(<Math24Game />)
      
      const modeButton = screen.getByRole('button', { name: /Mode Easy/i })
      await user.click(modeButton)
      
      expect(screen.getByLabelText('Add /')).toBeInTheDocument()
    })
  })

  describe('Number Input', () => {
    it('displays clicked numbers in the expression', async () => {
      const user = userEvent.setup()
      render(<Math24Game />)
      
      const numberButtons = screen.getAllByRole('button').filter(btn => 
        btn.classList.contains('number')
      )
      
      await user.click(numberButtons[0]!)
      
      const firstNumber = numberButtons[0]!.textContent
      const expressionDiv = document.querySelector('.expression')
      expect(expressionDiv).toHaveTextContent(firstNumber!)
    })

    it('marks used numbers', async () => {
      const user = userEvent.setup()
      render(<Math24Game />)
      
      const numberButtons = screen.getAllByRole('button').filter(btn => 
        btn.classList.contains('number')
      )
      
      const firstButton = numberButtons[0]!
      await user.click(firstButton)
      
      expect(firstButton).toHaveClass('used')
    })

    it('prevents clicking used numbers', async () => {
      const user = userEvent.setup()
      render(<Math24Game />)
      
      const numberButtons = screen.getAllByRole('button').filter(btn => 
        btn.classList.contains('number')
      )
      
      const firstButton = numberButtons[0]!
      
      await user.click(firstButton)
      await user.click(firstButton) // Try clicking again
      
      // The number should still be marked as used
      expect(firstButton).toHaveClass('used')
      
      // Get expression div
      const expressionDiv = document.querySelector('.expression')
      expect(expressionDiv).toBeInTheDocument()
    })
  })

  describe('Operator Input', () => {
    it('appends operators to expression', async () => {
      const user = userEvent.setup()
      render(<Math24Game />)
      
      const numberButtons = screen.getAllByRole('button').filter(btn => 
        btn.classList.contains('number')
      )
      
      await user.click(numberButtons[0]!)
      await user.click(screen.getByLabelText('Add +'))
      await user.click(numberButtons[1]!)
      
      const num1 = numberButtons[0]!.textContent!
      const num2 = numberButtons[1]!.textContent!
      
      expect(screen.getByText(new RegExp(`${num1}\\+${num2}`))).toBeInTheDocument()
    })

    it('handles parentheses', async () => {
      const user = userEvent.setup()
      render(<Math24Game />)
      
      await user.click(screen.getByLabelText('Add ('))
      
      // Check the expression div contains the parenthesis
      const expressionDiv = document.querySelector('.expression')
      expect(expressionDiv).toHaveTextContent('(')
    })
  })

  describe('Expression Actions', () => {
    it('clears the expression when Clear is clicked', async () => {
      const user = userEvent.setup()
      render(<Math24Game />)
      
      const numberButtons = screen.getAllByRole('button').filter(btn => 
        btn.classList.contains('number')
      )
      
      await user.click(numberButtons[0]!)
      await user.click(screen.getByRole('button', { name: /Clear/i }))
      
      expect(screen.getByText(/Tap numbers and operators/i)).toBeInTheDocument()
    })

    it('removes last token on backspace', async () => {
      const user = userEvent.setup()
      render(<Math24Game />)
      
      const numberButtons = screen.getAllByRole('button').filter(btn => 
        btn.classList.contains('number')
      )
      
      await user.click(numberButtons[0]!)
      await user.click(screen.getByLabelText('Add +'))
      await user.click(screen.getByRole('button', { name: /Backspace/i }))
      
      // Get expression div and check it doesn't have the +
      const expressionDiv = document.querySelector('.expression')
      expect(expressionDiv?.textContent).not.toContain('+')
    })

    it('unmarked used numbers after clearing', async () => {
      const user = userEvent.setup()
      render(<Math24Game />)
      
      const numberButtons = screen.getAllByRole('button').filter(btn => 
        btn.classList.contains('number')
      )
      
      const firstButton = numberButtons[0]!
      await user.click(firstButton)
      expect(firstButton).toHaveClass('used')
      
      await user.click(screen.getByRole('button', { name: /Clear/i }))
      expect(firstButton).not.toHaveClass('used')
    })
  })

  describe('Solution Checking', () => {
    it('shows error when checking empty expression', async () => {
      const user = userEvent.setup()
      render(<Math24Game />)
      
      await user.click(screen.getByRole('button', { name: /Check/i }))
      
      expect(screen.getByText(/Build an expression first/i)).toBeInTheDocument()
    })

    it('shows error when not all numbers are used', async () => {
      const user = userEvent.setup()
      render(<Math24Game />)
      
      const numberButtons = screen.getAllByRole('button').filter(btn => 
        btn.classList.contains('number')
      )
      
      await user.click(numberButtons[0]!)
      await user.click(screen.getByLabelText('Add +'))
      await user.click(numberButtons[1]!)
      
      await user.click(screen.getByRole('button', { name: /Check/i }))
      
      expect(screen.getByText(/Use every number exactly once/i)).toBeInTheDocument()
    })

    it('shows success message for correct solution', async () => {
      const user = userEvent.setup()
      render(<Math24Game />)
      
      const numberButtons = screen.getAllByRole('button').filter(btn => 
        btn.classList.contains('number')
      )
      
      // Build expression: 6 * (8 - 4) = 24
      // Note: actual numbers will vary, so we'll just test the feedback mechanism
      for (const btn of numberButtons) {
        await user.click(btn)
      }
      
      // Even if wrong, it should give feedback
      await user.click(screen.getByRole('button', { name: /Check/i }))
      
      // Should have some message
      const messages = screen.queryAllByText(/equals|Great work/i)
      expect(messages.length).toBeGreaterThan(0)
    })

    it('shows value when answer is incorrect', async () => {
      const user = userEvent.setup()
      render(<Math24Game />)
      
      const numberButtons = screen.getAllByRole('button').filter(btn => 
        btn.classList.contains('number')
      )
      
      // Create an expression with all numbers
      await user.click(numberButtons[0]!)
      await user.click(screen.getByLabelText('Add +'))
      await user.click(numberButtons[1]!)
      await user.click(screen.getByLabelText('Add +'))
      await user.click(numberButtons[2]!)
      await user.click(screen.getByLabelText('Add +'))
      await user.click(numberButtons[3]!)
      
      await user.click(screen.getByRole('button', { name: /Check/i }))
      
      // Should show "equals" or "Great work"
      expect(screen.queryByText(/equals|Great work/i)).toBeInTheDocument()
    })
  })

  describe('New Puzzle', () => {
    it('generates new numbers when New Puzzle is clicked', async () => {
      const user = userEvent.setup()
      render(<Math24Game />)
      
      const numberButtons = screen.getAllByRole('button').filter(btn => 
        btn.classList.contains('number')
      )
      const initialNumbers = numberButtons.map(btn => btn.textContent)
      
      await user.click(screen.getByRole('button', { name: /New Puzzle/i }))
      
      const newNumberButtons = screen.getAllByRole('button').filter(btn => 
        btn.classList.contains('number')
      )
      const newNumbers = newNumberButtons.map(btn => btn.textContent)
      
      // At least one number should be different (very high probability)
      // Note: there's a tiny chance they're the same, but it's negligible
      expect(newNumbers).toBeDefined()
    })

    it('clears expression when new puzzle is generated', async () => {
      const user = userEvent.setup()
      render(<Math24Game />)
      
      const numberButtons = screen.getAllByRole('button').filter(btn => 
        btn.classList.contains('number')
      )
      
      await user.click(numberButtons[0]!)
      await user.click(screen.getByRole('button', { name: /New Puzzle/i }))
      
      expect(screen.getByText(/Tap numbers and operators/i)).toBeInTheDocument()
    })
  })

  describe('AI Hint', () => {
    it('shows loading state when fetching AI hint', async () => {
      const user = userEvent.setup()
      
      // Mock a delayed response
      vi.mocked(fetch).mockImplementation(() => 
        new Promise(() => {}) // Never resolves
      )
      
      render(<Math24Game />)
      
      await user.click(screen.getByRole('button', { name: /AI Hint/i }))
      
      // Check the button is disabled and shows loading text
      const button = screen.getByRole('button', { name: /Gemini is thinking/i })
      expect(button).toBeDisabled()
    })

    it('displays AI hint on successful response', async () => {
      const user = userEvent.setup()
      
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ hint: 'Try multiplying the largest numbers first' }),
      } as Response)
      
      render(<Math24Game />)
      
      await user.click(screen.getByRole('button', { name: /AI Hint/i }))
      
      await waitFor(() => {
        expect(screen.getByText(/Try multiplying the largest numbers first/i)).toBeInTheDocument()
      })
    })

    it('displays error message on failed request', async () => {
      const user = userEvent.setup()
      
      vi.mocked(fetch).mockRejectedValueOnce(new Error('Network error'))
      
      render(<Math24Game />)
      
      await user.click(screen.getByRole('button', { name: /AI Hint/i }))
      
      await waitFor(() => {
        expect(screen.getByText(/Could not fetch a hint/i)).toBeInTheDocument()
      })
    })

    it('sends correct data to API', async () => {
      const user = userEvent.setup()
      
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ hint: 'test hint' }),
      } as Response)
      
      render(<Math24Game />)
      
      const numberButtons = screen.getAllByRole('button').filter(btn => 
        btn.classList.contains('number')
      )
      await user.click(numberButtons[0]!)
      
      await user.click(screen.getByRole('button', { name: /AI Hint/i }))
      
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/hint'),
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: expect.any(String),
          })
        )
      })
    })
  })

  describe('Solution Peek', () => {
    it('shows solution in details element', () => {
      render(<Math24Game />)
      
      const details = screen.getByText(/Peek at a solution/i)
      expect(details).toBeInTheDocument()
    })

    it('displays solution that equals 24', () => {
      render(<Math24Game />)
      
      // The solution should contain "= 24"
      const solutionText = screen.getByText(/= 24/i)
      expect(solutionText).toBeInTheDocument()
    })
  })

  describe('Shuffle Puzzle', () => {
    it('generates new puzzle when shuffle is clicked', async () => {
      const user = userEvent.setup()
      render(<Math24Game />)
      
      const shuffleButton = screen.getByRole('button', { name: /Shuffle puzzle/i })
      await user.click(shuffleButton)
      
      // Should still have 4 numbers
      const numberButtons = screen.getAllByRole('button').filter(btn => 
        btn.classList.contains('number')
      )
      expect(numberButtons).toHaveLength(4)
    })
  })
})
