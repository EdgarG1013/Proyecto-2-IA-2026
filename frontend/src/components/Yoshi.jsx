// Sprites de los Yoshis (frontend/public). Ambos dibujos miran a la izquierda;
// para mirar a la derecha se voltean horizontalmente.
const SPRITES = {
  verde: '/Yoshi-verde.svg',
  rojo: '/Yoshi-rojo.svg',
}

export default function Yoshi({ color, mirando = 'izquierda' }) {
  return (
    <div className="yoshi">
      <span className="yoshi-sombra" />
      <img
        src={SPRITES[color]}
        alt=""
        draggable="false"
        className={`yoshi-img ${mirando === 'derecha' ? 'yoshi-img--volteado' : ''}`}
      />
    </div>
  )
}
