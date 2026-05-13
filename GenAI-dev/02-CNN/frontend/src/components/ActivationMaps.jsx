export default function ActivationMaps({ data, loading }) {
  if (!data && !loading) return null

  return (
    <div className="activations">
      <h2 className="act-title">Activaciones de la CNN</h2>

      <Block
        title="Bloque 1 — rasgos básicos (bordes, curvas)"
        maps={data?.block1}
        size={28}
        loading={loading}
      />
      <Block
        title="Bloque 2 — rasgos complejos (formas)"
        maps={data?.block2}
        size={14}
        loading={loading}
      />
    </div>
  )
}

function Block({ title, maps, size, loading }) {
  return (
    <div className="act-block">
      <p className="act-block-title">{title}</p>
      <div className="act-grid">
        {loading || !maps
          ? Array.from({ length: 16 }).map((_, i) => (
              <div key={i} className="act-cell act-cell-loading" />
            ))
          : maps.map((b64, i) => (
              <img
                key={i}
                src={`data:image/png;base64,${b64}`}
                width={size}
                height={size}
                className="act-cell"
                title={`Filtro ${i + 1}`}
                style={{ imageRendering: 'pixelated' }}
              />
            ))}
      </div>
    </div>
  )
}
