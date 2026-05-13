import { forwardRef, useRef, useState } from 'react'

const SIZES = [6, 12, 20]
const SIZE_LABELS = ['S', 'M', 'L']

const Canvas = forwardRef(function Canvas({ onStrokeEnd, onClear }, ref) {
  const [brushSize, setBrushSize] = useState(1)
  const drawing = useRef(false)

  function getPos(e) {
    const r = ref.current.getBoundingClientRect()
    if (e.touches) {
      return { x: e.touches[0].clientX - r.left, y: e.touches[0].clientY - r.top }
    }
    return { x: e.clientX - r.left, y: e.clientY - r.top }
  }

  function startDraw(e) {
    e.preventDefault()
    drawing.current = true
    const ctx = ref.current.getContext('2d')
    ctx.lineWidth = SIZES[brushSize]
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    ctx.strokeStyle = '#000'
    const p = getPos(e)
    ctx.beginPath()
    ctx.moveTo(p.x, p.y)
  }

  function draw(e) {
    e.preventDefault()
    if (!drawing.current) return
    const ctx = ref.current.getContext('2d')
    const p = getPos(e)
    ctx.lineTo(p.x, p.y)
    ctx.stroke()
  }

  function endDraw() {
    if (!drawing.current) return
    drawing.current = false
    onStrokeEnd()
  }

  function clear() {
    const canvas = ref.current
    const ctx = canvas.getContext('2d')
    ctx.fillStyle = '#fff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    onClear()
  }

  return (
    <div className="canvas-wrapper">
      <canvas
        ref={ref}
        width={480}
        height={480}
        className="draw-canvas"
        onMouseDown={startDraw}
        onMouseMove={draw}
        onMouseUp={endDraw}
        onMouseLeave={endDraw}
        onTouchStart={startDraw}
        onTouchMove={draw}
        onTouchEnd={endDraw}
        style={{ background: '#fff' }}
      />
      <div className="canvas-toolbar">
        <div className="brush-sizes">
          {SIZE_LABELS.map((label, i) => (
            <button
              key={i}
              className={`brush-btn ${brushSize === i ? 'active' : ''}`}
              onClick={() => setBrushSize(i)}
              title={`Grosor ${label}`}
            >
              <span className="brush-dot" style={{ width: SIZES[i], height: SIZES[i] }} />
            </button>
          ))}
        </div>
        <button className="clear-btn" onClick={clear}>
          Borrar
        </button>
      </div>
    </div>
  )
})

export default Canvas
