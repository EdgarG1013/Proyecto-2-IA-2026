import { motion } from 'motion/react'
import { coordenada, formatearValor, formatearEntero } from '../formato.js'
import { NIVELES } from '../niveles.js'

export function Marcador({ partida }) {
  const verde = partida?.casillas_verde ?? 0
  const rojo = partida?.casillas_rojo ?? 0
  const turno = partida && !partida.terminado ? partida.estado.turno : null

  return (
    <section className="marcador" aria-label="Casillas pintadas">
      <div className={`marcador-lado marcador-lado--verde ${turno === 1 ? 'marcador-lado--turno' : ''}`}>
        <span className="marcador-nombre">Máquina</span>
        <motion.span key={verde} className="marcador-numero" initial={{ scale: 1.35 }} animate={{ scale: 1 }}>
          {verde}
        </motion.span>
      </div>
      <div className="marcador-libres">
        <span>{64 - verde - rojo}</span> libres
      </div>
      <div className={`marcador-lado marcador-lado--rojo ${turno === 2 ? 'marcador-lado--turno' : ''}`}>
        <span className="marcador-nombre">Tú</span>
        <motion.span key={rojo} className="marcador-numero" initial={{ scale: 1.35 }} animate={{ scale: 1 }}>
          {rojo}
        </motion.span>
      </div>
    </section>
  )
}

export function Ajustes({ config, onCambiar, mostrarValores, onMostrarValores, onNuevaPartida, hayPartida }) {
  return (
    <section className="ajustes">
      <fieldset className="niveles">
        <legend>Dificultad</legend>
        {NIVELES.map((nivel) => (
          <label key={nivel.id} className={`nivel ${config.nivel === nivel.id ? 'nivel--activo' : ''}`}>
            <input
              type="radio"
              name="nivel"
              value={nivel.id}
              checked={config.nivel === nivel.id}
              onChange={() => onCambiar({ ...config, nivel: nivel.id })}
            />
            <span className="nivel-nombre">{nivel.nombre}</span>
            <span className="nivel-detalle">profundidad {nivel.profundidad}</span>
          </label>
        ))}
      </fieldset>

      <label className="interruptor">
        <input
          type="checkbox"
          checked={config.poda}
          onChange={(e) => onCambiar({ ...config, poda: e.target.checked })}
        />
        <span className="interruptor-pista" aria-hidden="true" />
        Usar poda alfa-beta
      </label>

      <label className="interruptor">
        <input type="checkbox" checked={mostrarValores} onChange={(e) => onMostrarValores(e.target.checked)} />
        <span className="interruptor-pista" aria-hidden="true" />
        Mostrar valores de minimax en el tablero
      </label>

      <button type="button" className="boton boton--principal" onClick={onNuevaPartida}>
        {hayPartida ? 'Nueva partida' : 'Empezar partida'}
      </button>
    </section>
  )
}

export function Razonamiento({ decision, pensando, config }) {
  const profundidad = NIVELES.find((n) => n.id === config.nivel).profundidad

  if (pensando) {
    return (
      <section className="razonamiento">
        <h2>Lo que pensó la máquina</h2>
        <p className="pensando">
          <span className="pensando-punto" aria-hidden="true" />
          Explorando el árbol a profundidad {profundidad} {config.poda ? 'con poda' : 'sin poda'}…
        </p>
      </section>
    )
  }

  if (!decision) {
    return (
      <section className="razonamiento">
        <h2>Lo que pensó la máquina</h2>
        <p className="texto-suave">Aquí verás el valor minimax de cada salto que consideró la máquina.</p>
      </section>
    )
  }

  const ordenados = [...decision.candidatos].sort((a, b) => b.valor - a.valor)
  const nivel = NIVELES.find((n) => n.id === decision.nivel)

  return (
    <section className="razonamiento">
      <h2>Lo que pensó la máquina</h2>
      <p>
        Saltó a <strong>{coordenada(decision.jugada)}</strong> con valor{' '}
        <strong>{formatearValor(decision.valor)}</strong>. {nivel.nombre}, profundidad {decision.profundidad},{' '}
        {decision.poda ? 'con poda alfa-beta' : 'sin poda'}.
      </p>

      <ol className="candidatos">
        {ordenados.map((cand) => {
          const elegido = cand.jugada[0] === decision.jugada[0] && cand.jugada[1] === decision.jugada[1]
          return (
            <li key={coordenada(cand.jugada)} className={elegido ? 'candidato--elegido' : ''}>
              <span>{coordenada(cand.jugada)}</span>
              <span className="candidato-valor">
                {cand.exacto ? '' : '≤ '}
                {formatearValor(cand.valor)}
              </span>
            </li>
          )
        })}
      </ol>
      {ordenados.some((c) => !c.exacto) && (
        <p className="nota">
          ≤ significa que la poda cortó esa rama: solo se sabe que vale como mucho eso, y ya no podía superar a la
          mejor jugada.
        </p>
      )}

      <dl className="estadisticas">
        <div>
          <dt>Nodos</dt>
          <dd>{formatearEntero(decision.nodos)}</dd>
        </div>
        <div>
          <dt>Hojas evaluadas</dt>
          <dd>{formatearEntero(decision.hojas)}</dd>
        </div>
        <div>
          <dt>Podas</dt>
          <dd>{formatearEntero(decision.podas)}</dd>
        </div>
        <div>
          <dt>Tiempo</dt>
          <dd>{formatearEntero(Math.round(decision.tiempo_ms))} ms</dd>
        </div>
      </dl>
    </section>
  )
}

export function Evaluacion({ heuristica }) {
  if (!heuristica) return null
  const { f1, f2, h, pesos } = heuristica
  // h está en [-1, 1]; la barra muestra hacia qué lado se inclina el tablero
  const porcentaje = ((h + 1) / 2) * 100

  const filas = [
    { nombre: 'f₁ casillas pintadas', verde: heuristica.pintadas_verde, rojo: heuristica.pintadas_rojo, valor: f1, peso: pesos[0] },
    { nombre: 'f₂ saltos disponibles', verde: heuristica.saltos_verde, rojo: heuristica.saltos_rojo, valor: f2, peso: pesos[1] },
  ]

  return (
    <section className="evaluacion">
      <h2>Evaluación del tablero actual</h2>
      <div className="balanza" role="img" aria-label={`h = ${formatearValor(h)}`}>
        <motion.div className="balanza-verde" animate={{ width: `${porcentaje}%` }} transition={{ type: 'spring', stiffness: 120, damping: 20 }} />
        <span className="balanza-centro" />
      </div>
      <p className="balanza-valor">
        h = <strong>{formatearValor(h)}</strong>{' '}
        {h > 0.02 ? 'favorece a la máquina' : h < -0.02 ? 'te favorece a ti' : 'equilibrado'}
      </p>
      {heuristica.terminal && (
        <p className="nota">
          Estado terminal: minimax no usa h sino la utilidad exacta U(s) = 1000·signo(D) + D ={' '}
          <strong>{formatearValor(heuristica.utilidad)}</strong>.
        </p>
      )}
      <table className="tabla-heuristica">
        <thead>
          <tr>
            <th scope="col">Componente</th>
            <th scope="col">Verde</th>
            <th scope="col">Rojo</th>
            <th scope="col">Valor</th>
            <th scope="col">Peso</th>
          </tr>
        </thead>
        <tbody>
          {filas.map((fila) => (
            <tr key={fila.nombre}>
              <th scope="row">{fila.nombre}</th>
              <td>{fila.verde}</td>
              <td>{fila.rojo}</td>
              <td>{formatearValor(fila.valor)}</td>
              <td>{fila.peso.toFixed(3)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}

export function Bitacora({ eventos }) {
  if (eventos.length === 0) return null
  return (
    <details className="bitacora">
      <summary>Historial de jugadas ({eventos.length})</summary>
      <ol reversed>
        {[...eventos].reverse().map((evento, i) => (
          <li key={eventos.length - i} className={`bitacora-${evento.quien}`}>
            {evento.texto}
          </li>
        ))}
      </ol>
    </details>
  )
}
