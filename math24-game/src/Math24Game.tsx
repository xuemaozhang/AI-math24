import { useEffect, useMemo, useRef, useState } from 'react'
import './Math24Game.css'

type Mode = 'easy' | 'hard'

type Puzzle = {
  nums: number[]
  hints: string[]
  solution: string
}

type FeedbackTone = 'neutral' | 'success' | 'error'

type Token =
  | { type: 'num'; text: string; index: number }
  | { type: 'op'; text: string }

const OPERATORS = ['+', '-', '*', '/', '(', ')'] as const
const NUMBER_COLORS = ['#ff6b6b', '#f7c266', '#5dd39e', '#6a8dff']
const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

type HintStatus = 'idle' | 'loading' | 'error'

type ExprNode = { val: number; expr: string }

function findSolution(nums: number[], mode: Mode): string | null {
  const ops = [
    {
      symbol: '+',
      calc: (a: ExprNode, b: ExprNode) => ({ val: a.val + b.val, expr: `(${a.expr}+${b.expr})` }),
    },
    {
      symbol: '-',
      calc: (a: ExprNode, b: ExprNode) => ({ val: a.val - b.val, expr: `(${a.expr}-${b.expr})` }),
    },
    {
      symbol: '*',
      calc: (a: ExprNode, b: ExprNode) => ({ val: a.val * b.val, expr: `(${a.expr}*${b.expr})` }),
    },
    {
      symbol: '/',
      calc: (a: ExprNode, b: ExprNode) => (Math.abs(b.val) < 1e-9 ? null : {
        val: a.val / b.val,
        expr: `(${a.expr}/${b.expr})`,
      }),
    },
  ] as const

  const search = (arr: ExprNode[]): string | null => {
    if (arr.length === 1) {
      return Math.abs(arr[0]!.val - 24) < 1e-6 ? arr[0]!.expr : null
    }

    for (let i = 0; i < arr.length; i += 1) {
      for (let j = 0; j < arr.length; j += 1) {
        if (i === j) continue
        const rest = arr.filter((_, idx) => idx !== i && idx !== j)

        for (const op of ops) {
          if (mode === 'easy' && op.symbol === '/') continue
          const result = op.calc(arr[i]!, arr[j]!)
          if (!result) continue
          const found = search([...rest, result])
          if (found) return found
        }
      }
    }
    return null
  }

  const seeds = nums.map((n) => ({ val: n, expr: n.toString() }))
  return search(seeds)
}

function generateSolvablePuzzle(mode: Mode = 'hard'): Puzzle {
  const shuffle = (arr: number[]) => [...arr].sort(() => Math.random() - 0.5)

  // Keep generating until a solvable set is found.
  // eslint-disable-next-line no-constant-condition
  while (true) {
    const nums = Array.from({ length: 4 }, () => Math.floor(Math.random() * 9) + 1)
    const solution = findSolution(nums, mode)
    if (solution) {
      return {
        nums: shuffle(nums),
        hints: [],
        solution,
      }
    }
  }
}

function evaluateExpression(expression: string): number {
  const sanitized = expression.replace(/[^0-9+\-*/(). ]/g, '')
  const evaluator = Function(`"use strict"; return (${sanitized});`) as () => number
  return evaluator()
}

export default function Math24Game() {
  const [mode, setMode] = useState<Mode>('easy')
  const [puzzle, setPuzzle] = useState<Puzzle>(() => generateSolvablePuzzle('easy'))
  const [tokens, setTokens] = useState<Token[]>([])
  const [message, setMessage] = useState<string>('')
  const [tone, setTone] = useState<FeedbackTone>('neutral')
  const [hintLevel, setHintLevel] = useState<number>(0)
  const [aiHint, setAiHint] = useState<string>('')
  const [aiStatus, setAiStatus] = useState<HintStatus>('idle')
  const [aiError, setAiError] = useState<string>('')
  const solutionRef = useRef<HTMLDetailsElement>(null)

  useEffect(() => {
    setHintLevel(puzzle.hints.length)
  }, [puzzle])

  const input = useMemo(() => tokens.map((t) => t.text).join(''), [tokens])
  const usedIndices = useMemo(
    () => tokens.filter((t): t is Extract<Token, { type: 'num' }> => t.type === 'num').map((t) => t.index),
    [tokens],
  )
  const usedSet = useMemo(() => new Set(usedIndices), [usedIndices])

  const operatorList = useMemo(
    () => (mode === 'easy' ? OPERATORS.filter((op) => op !== '/') : OPERATORS),
    [mode],
  )

  const setFeedback = (text: string, nextTone: FeedbackTone = 'neutral') => {
    setMessage(text)
    setTone(nextTone)
  }

  const resetAi = () => {
    setAiHint('')
    setAiError('')
    setAiStatus('idle')
  }

  const appendNumber = (value: number, index: number) => {
    if (usedSet.has(index)) return
    setTokens((prev) => [...prev, { type: 'num', text: value.toString(), index }])
    setFeedback('')
  }

  const appendOperator = (op: string) => {
    setTokens((prev) => [...prev, { type: 'op', text: op }])
    setFeedback('')
  }

  const backspace = () => {
    setTokens((prev) => (prev.length ? prev.slice(0, -1) : prev))
  }

  const clearInput = () => {
    setTokens([])
    setHintLevel(0)
    setFeedback('')
    resetAi()
  }

  const nextPuzzle = (nextMode: Mode = mode) => {
    const fresh = generateSolvablePuzzle(nextMode)
    setPuzzle(fresh)
    clearInput()
    if (solutionRef.current) {
      solutionRef.current.open = false
    }
  }

  const toggleMode = () => {
    const nextMode: Mode = mode === 'easy' ? 'hard' : 'easy'
    setMode(nextMode)
    nextPuzzle(nextMode)
  }

  const fetchAiHint = async () => {
    if (aiStatus === 'loading') return
    setAiStatus('loading')
    setAiError('')
    setAiHint('')

    try {
      const response = await fetch(`${API_BASE}/hint`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          numbers: puzzle.nums,
          expression: input,
          target: 24,
          mode,
          solution: puzzle.solution,
        }),
      })

      if (!response.ok) {
        const text = await response.text()
        throw new Error(text || 'Request failed')
      }

      const data = await response.json()
      setAiHint(data.hint ?? 'No hint returned.')
      setAiStatus('idle')
    } catch (error) {
      console.error('AI hint error', error)
      setAiError('Could not fetch a hint right now. Please try again in a moment.')
      setAiStatus('error')
    }
  }

  const checkSolution = () => {
    if (input.trim().length === 0) {
      setFeedback('Build an expression first.', 'error')
      return
    }

    if (usedIndices.length !== puzzle.nums.length) {
      setFeedback('Use every number exactly once.', 'error')
      return
    }

    try {
      const value = evaluateExpression(input)
      if (Number.isFinite(value) && Math.abs(value - 24) < 1e-6) {
        setFeedback('Great work! You made 24.', 'success')
      } else {
        setFeedback(`That equals ${value}. Keep going!`, 'error')
      }
    } catch (error) {
      console.error('Evaluation failed', error)
      setFeedback('That expression is not valid.', 'error')
    }
  }

  return (
    <div className="game-shell">
      <div className="game-card">
        <div className="game-head">
          <div>
            <p className="eyebrow">Daily brain stretch</p>
            <h1 className="game-title">Math 24</h1>
            <p className="subtitle">Use each number once to build 24. Parentheses are your friends.</p>
          </div>
          <button className="mode-toggle" type="button" onClick={toggleMode}>
            <span className="pill">Mode</span>
            <span>{mode === 'easy' ? 'Easy' : 'Hard'}</span>
          </button>
        </div>

        <section className="section">
          <div className="label-row">
            <p className="label">Numbers</p>
            <button className="link" type="button" onClick={() => nextPuzzle()}>
              Shuffle puzzle
            </button>
          </div>
          <div className="number-grid">
            {puzzle.nums.map((n, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => appendNumber(n, idx)}
                className={`number ${usedSet.has(idx) ? 'used' : ''}`}
                style={{ background: NUMBER_COLORS[idx % NUMBER_COLORS.length] }}
                aria-pressed={usedSet.has(idx)}
              >
                <span>{n}</span>
              </button>
            ))}
          </div>
        </section>

        <section className="section">
          <div className="label-row">
            <p className="label">Operators</p>
            <p className="hint">Easy mode hides division.</p>
          </div>
          <div className="operator-grid">
            {operatorList.map((op) => (
              <button
                key={op}
                type="button"
                onClick={() => appendOperator(op)}
                className="operator"
                aria-label={`Add ${op}`}
              >
                {op}
              </button>
            ))}
          </div>
        </section>

        <section className="section expression-card">
          <div className="label-row">
            <p className="label">Expression</p>
            <button className="link" type="button" onClick={clearInput}>
              Clear
            </button>
          </div>
          <div className="expression" aria-live="polite">
            {input || 'Tap numbers and operators to build your expression'}
          </div>
        </section>

        <section className="section">
          <div className="action-grid">
            <button className="btn primary" type="button" onClick={checkSolution}>
              Check ✓
            </button>
            <button className="btn secondary" type="button" onClick={() => nextPuzzle()}>
              New Puzzle 🎲
            </button>
            <button className="btn ghost" type="button" onClick={backspace}>
              Backspace
            </button>
          </div>
        </section>

        <section className="section hint-card">
          <div className="label-row">
            <p className="label">Hints</p>
            <p className="hint">{hintLevel}/{puzzle.hints.length} shown</p>
          </div>
          <div className="hint-actions">
            <button
              className="btn primary"
              type="button"
              onClick={fetchAiHint}
              disabled={aiStatus === 'loading'}
            >
              {aiStatus === 'loading' ? 'Gemini is thinking…' : 'AI Hint (Gemini)'}
            </button>
            <button className="btn subtle" type="button" onClick={toggleMode}>
              Switch to {mode === 'easy' ? 'Hard' : 'Easy'}
            </button>
          </div>
          {puzzle.hints.slice(0, hintLevel).map((hint, idx) => (
            <p key={hint} className="hint-note">
              <span className="hint-index">{idx + 1}</span> {hint}
            </p>
          ))}
          {aiStatus === 'loading' && <p className="hint-note ai-hint">Gemini is thinking about a nudge…</p>}
          {aiHint && aiStatus !== 'loading' && (
            <p className="hint-note ai-hint" aria-live="polite">{aiHint}</p>
          )}
          {aiError && <p className="hint-error" aria-live="assertive">{aiError}</p>}
        </section>

        {message && (
          <p className={`message ${tone === 'success' ? 'success' : tone === 'error' ? 'error' : ''}`}>
            {message}
          </p>
        )}

        <details className="solution" ref={solutionRef}>
          <summary>Peek at a solution</summary>
          <p>{puzzle.solution} = 24</p>
        </details>
      </div>
    </div>
  )
}
