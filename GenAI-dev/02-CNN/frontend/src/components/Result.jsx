import { useEffect, useRef } from 'react'

const EMOJIS = {
  'smiley face': '😊',
  'face': '😐',
  'flower': '🌸',
  'star': '⭐',
  'sun': '☀️',
  'cloud': '☁️',
}

function Preview({ canvasRef }) {
  const previewRef = useRef(null)

  useEffect(() => {
    const preview = previewRef.current
    const source = canvasRef?.current
    if (!preview || !source) return
    const ctx = preview.getContext('2d')
    ctx.drawImage(source, 0, 0, 28, 28)
  })

  return (
    <div className="preview-wrapper">
      <p className="preview-label">lo que ve el modelo</p>
      <canvas ref={previewRef} width={28} height={28} className="preview-canvas" />
    </div>
  )
}

function ConfBar({ label, prob, isTop }) {
  const pct = (prob * 100).toFixed(1)
  return (
    <div className={`bar-row ${isTop ? 'bar-top' : ''}`}>
      <span className="bar-emoji">{EMOJIS[label] ?? '?'}</span>
      <span className="bar-label">{label}</span>
      <div className="bar-track">
        <div
          className="bar-fill"
          style={{ width: `${pct}%`, opacity: isTop ? 1 : 0.45 }}
        />
      </div>
      <span className="bar-pct">{pct}%</span>
    </div>
  )
}

export default function Result({ result, loading, error, canvasRef }) {
  if (error) {
    return (
      <div className="result-card result-error">
        <p>⚠️ {error}</p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="result-card result-loading">
        <div className="spinner" />
        <p>Analizando…</p>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="result-card result-empty">
        <p className="empty-text">La predicción aparecerá aquí</p>
        <Preview canvasRef={canvasRef} />
      </div>
    )
  }

  const sorted = Object.entries(result.all_probs).sort((a, b) => b[1] - a[1])

  return (
    <div className="result-card result-active">
      <div className="result-top">
        <span className="result-emoji">{EMOJIS[result.category] ?? '?'}</span>
        <div>
          <div className="result-category">{result.category}</div>
          <div className="result-confidence">{(result.confidence * 100).toFixed(1)}% de confianza</div>
        </div>
      </div>

      <div className="bars">
        {sorted.map(([label, prob]) => (
          <ConfBar key={label} label={label} prob={prob} isTop={label === result.category} />
        ))}
      </div>

      <Preview canvasRef={canvasRef} />
    </div>
  )
}
