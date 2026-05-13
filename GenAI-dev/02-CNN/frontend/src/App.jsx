import { useRef, useState, useEffect, useCallback } from 'react'
import Canvas from './components/Canvas'
import Result from './components/Result'
import ActivationMaps from './components/ActivationMaps'
import './App.css'

const API = 'http://localhost:8000'

export default function App() {
  const canvasRef = useRef(null)
  const [result, setResult] = useState(null)
  const [activations, setActivations] = useState(null)
  const [loading, setLoading] = useState(false)
  const [actLoading, setActLoading] = useState(false)
  const [error, setError] = useState(null)
  const [hasDrawing, setHasDrawing] = useState(false)
  const timerRef = useRef(null)

  const predict = useCallback(async () => {
    const canvas = canvasRef.current
    if (!canvas) return
    const image = canvas.toDataURL('image/png')

    setLoading(true)
    setActLoading(true)
    setError(null)

    try {
      const [predRes, actRes] = await Promise.all([
        fetch(`${API}/predict`,     { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ image }) }),
        fetch(`${API}/activations`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ image }) }),
      ])
      setResult(await predRes.json())
      setActivations(await actRes.json())
    } catch {
      setError('No se puede conectar con la API')
      setResult(null)
      setActivations(null)
    } finally {
      setLoading(false)
      setActLoading(false)
    }
  }, [])

  const handleStrokeEnd = useCallback(() => {
    setHasDrawing(true)
    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(predict, 700)
  }, [predict])

  const handleClear = () => {
    clearTimeout(timerRef.current)
    setResult(null)
    setActivations(null)
    setError(null)
    setHasDrawing(false)
  }

  useEffect(() => () => clearTimeout(timerRef.current), [])

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">✏️</div>
        <h1>Quick Draw</h1>
        <p className="subtitle">Dibuja y la CNN lo reconoce en tiempo real</p>
      </header>

      <main className="app-main">
        <section className="canvas-section">
          <p className="hint">smiley face · face · flower · star · sun · cloud</p>
          <Canvas ref={canvasRef} onStrokeEnd={handleStrokeEnd} onClear={handleClear} />
          {!hasDrawing && <p className="draw-cue">← dibuja aquí</p>}
        </section>

        <section className="result-section">
          <Result result={result} loading={loading} error={error} canvasRef={canvasRef} />
        </section>
      </main>

      <ActivationMaps data={activations} loading={actLoading} />
    </div>
  )
}
