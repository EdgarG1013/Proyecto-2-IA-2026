// Dinosaurio dibujado a mano en SVG. 'color' es 'verde' o 'rojo'.
const COLORES = {
  verde: { cuerpo: '#3DAA5C', sombra: '#257A3E' },
  rojo: { cuerpo: '#E0544A', sombra: '#A8322B' },
}

export default function Yoshi({ color, mirando = 'derecha' }) {
  const { cuerpo, sombra } = COLORES[color]
  const voltear = mirando === 'izquierda' ? 'translate(100 0) scale(-1 1)' : undefined

  return (
    <svg viewBox="0 0 100 100" className="yoshi-svg" aria-hidden="true">
      <ellipse cx="50" cy="91" rx="27" ry="5" fill="rgba(30,45,59,.22)" />
      <g transform={voltear} stroke="#1E2D3B" strokeWidth="3" strokeLinejoin="round">
        {/* pies */}
        <ellipse cx="36" cy="85" rx="10" ry="6" fill={sombra} />
        <ellipse cx="60" cy="85" rx="10" ry="6" fill={sombra} />
        {/* cuerpo y barriga */}
        <ellipse cx="46" cy="64" rx="24" ry="21" fill={cuerpo} />
        <ellipse cx="52" cy="68" rx="13" ry="13" fill="#FFF7E3" />
        {/* cresta */}
        <path d="M24 50 l-6 -9 l11 1 Z M27 40 l-3 -11 l10 5 Z" fill="#F3C443" />
        {/* cabeza con hocico grande */}
        <ellipse cx="60" cy="38" rx="27" ry="19" fill={cuerpo} />
        <ellipse cx="82" cy="38" rx="2.4" ry="3.4" fill={sombra} stroke="none" />
        <path d="M62 49 q12 5 22 -2" fill="none" strokeWidth="2.5" />
        {/* ojo */}
        <ellipse cx="53" cy="23" rx="8.5" ry="11" fill="#FFFFFF" />
        <ellipse cx="56" cy="25" rx="3.6" ry="5.4" fill="#1E2D3B" stroke="none" />
        <circle cx="57.4" cy="22.6" r="1.4" fill="#FFFFFF" stroke="none" />
      </g>
    </svg>
  )
}
