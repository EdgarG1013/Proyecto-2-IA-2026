import { useState } from 'react'
import { motion } from 'motion/react'
import Yoshi from './Yoshi.jsx'
import { coordenada, formatearValor } from '../formato.js'

const INDICES = [0, 1, 2, 3, 4, 5, 6, 7]
const NOMBRE_CASILLA = { 0: 'libre', 1: 'pintada de verde', 2: 'pintada de rojo' }

// Ficha de un Yoshi. Se desliza a la nueva casilla y, en paralelo, hace un salto en arco.
function FichaYoshi({ color, posicion }) {
  const [fila, columna] = posicion
  const [anterior, setAnterior] = useState(posicion)
  const [mirando, setMirando] = useState(color === 'verde' ? 'derecha' : 'izquierda')

  // Al cambiar de casilla, el Yoshi mira hacia el lado al que saltó
  if (anterior[0] !== fila || anterior[1] !== columna) {
    setAnterior(posicion)
    if (anterior[1] !== columna) setMirando(columna > anterior[1] ? 'derecha' : 'izquierda')
  }

  return (
    <motion.div
      className="ficha"
      initial={false}
      animate={{ x: `${columna * 100}%`, y: `${fila * 100}%` }}
      transition={{ type: 'spring', stiffness: 170, damping: 20 }}
    >
      <motion.div
        key={`${fila}-${columna}`}
        className="ficha-salto"
        initial={{ y: 0, scaleY: 1 }}
        animate={{ y: ['0%', '-45%', '0%', '0%'], scaleY: [1, 1.06, 0.88, 1] }}
        transition={{ duration: 0.55, times: [0, 0.45, 0.8, 1], ease: 'easeOut' }}
      >
        <Yoshi color={color} mirando={mirando} />
      </motion.div>
    </motion.div>
  )
}

export default function Tablero({ partida, candidatos, puedeJugar, onJugar }) {
  const tablero = partida?.estado.tablero ?? INDICES.map(() => INDICES.map(() => 0))
  const legales = new Set((puedeJugar ? partida.movimientos : []).map(([f, c]) => `${f}-${c}`))
  const valores = new Map((candidatos ?? []).map((cand) => [`${cand.jugada[0]}-${cand.jugada[1]}`, cand]))

  return (
    <div className="tablero-marco">
      <div className="coordenadas coordenadas--columnas" aria-hidden="true">
        {INDICES.map((c) => <span key={c}>{c + 1}</span>)}
      </div>
      <div className="coordenadas coordenadas--filas" aria-hidden="true">
        {INDICES.map((f) => <span key={f}>{f + 1}</span>)}
      </div>

      <div className="tablero" role="grid" aria-label="Tablero de 8 por 8">
        {INDICES.map((f) =>
          INDICES.map((c) => {
            const clave = `${f}-${c}`
            const valor = tablero[f][c]
            const esLegal = legales.has(clave)
            const candidato = valores.get(clave)
            const oscura = (f + c) % 2 === 1

            return (
              <button
                key={clave}
                type="button"
                role="gridcell"
                className={`casilla ${oscura ? 'casilla--oscura' : ''} ${esLegal ? 'casilla--legal' : ''}`}
                disabled={!esLegal}
                onClick={() => onJugar([f, c])}
                aria-label={`Casilla ${coordenada([f, c])}, ${NOMBRE_CASILLA[valor]}${esLegal ? ', puedes saltar aquí' : ''}`}
              >
                {valor !== 0 && (
                  <motion.span
                    className={`pintura ${valor === 1 ? 'pintura--verde' : 'pintura--rojo'}`}
                    initial={{ scale: 0.2, opacity: 0, borderRadius: '50%' }}
                    animate={{ scale: 1, opacity: 1, borderRadius: '18%' }}
                    transition={{ delay: 0.3, type: 'spring', stiffness: 260, damping: 16 }}
                  />
                )}
                {esLegal && <span className="huevo" aria-hidden="true" />}
                {candidato && (
                  <motion.span
                    className={`valor-candidato ${candidato.elegido ? 'valor-candidato--elegido' : ''}`}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 }}
                  >
                    {candidato.exacto ? '' : '≤'}
                    {formatearValor(candidato.valor)}
                  </motion.span>
                )}
              </button>
            )
          }),
        )}

        {partida && (
          <div className="capa-fichas" aria-hidden="true">
            <FichaYoshi color="verde" posicion={partida.estado.verde} />
            <FichaYoshi color="rojo" posicion={partida.estado.rojo} />
          </div>
        )}
      </div>
    </div>
  )
}
