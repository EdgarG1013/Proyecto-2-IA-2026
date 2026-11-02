import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, MotionConfig, motion } from 'motion/react'
import Tablero from './components/Tablero.jsx'
import { Ajustes, Bitacora, Evaluacion, Marcador, Razonamiento } from './components/Panel.jsx'
import { NIVELES } from './niveles.js'
import { jugadaHumano, jugadaMaquina, nuevaPartida } from './api.js'
import { coordenada } from './formato.js'

// Pausa antes de que la máquina mueva, para que se alcance a ver el salto anterior
const PAUSA_MAQUINA_MS = 650

function textoEstado(partida, pensando, config) {
  if (!partida) return 'Elige la dificultad y si la máquina usa poda. La máquina (verde) siempre mueve primero.'
  if (partida.terminado) return 'La partida terminó: ninguno de los dos tiene saltos.'
  if (pensando) {
    const nivel = NIVELES.find((n) => n.id === config.nivel)
    return `La máquina está pensando a profundidad ${nivel.profundidad}…`
  }
  if (partida.estado.turno === 2) {
    return partida.pase === 'verde'
      ? 'La máquina se quedó sin saltos. Vuelves a mover.'
      : 'Tu turno: salta a una de las casillas con huevo.'
  }
  return partida.pase === 'rojo' ? 'No tienes saltos. La máquina vuelve a mover.' : 'Turno de la máquina.'
}

function textoGanador(partida) {
  const marcador = `${partida.casillas_verde} a ${partida.casillas_rojo}`
  if (partida.ganador === 'verde') return { titulo: 'Ganó la máquina', detalle: `Pintó ${marcador}.` }
  if (partida.ganador === 'rojo') return { titulo: '¡Ganaste!', detalle: `Pintaste ${partida.casillas_rojo} contra ${partida.casillas_verde}.` }
  return { titulo: 'Empate', detalle: `Cada uno pintó ${partida.casillas_verde}.` }
}

export default function App() {
  const [config, setConfig] = useState({ nivel: 'principiante', poda: true })
  const [mostrarValores, setMostrarValores] = useState(true)
  const [partida, setPartida] = useState(null)
  const [decision, setDecision] = useState(null)
  const [pensando, setPensando] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState(null)
  const [eventos, setEventos] = useState([])
  const [reintentos, setReintentos] = useState(0)

  // La máquina lee los ajustes del momento en que le toca jugar
  const configActual = useRef(config)
  useEffect(() => {
    configActual.current = config
  }, [config])

  function registrar(nuevos) {
    setEventos((anteriores) => [...anteriores, ...nuevos])
  }

  function eventoDePase(respuesta) {
    if (respuesta.pase === 'rojo') return [{ quien: 'rojo', texto: 'Rojo no tiene saltos y pierde el turno.' }]
    if (respuesta.pase === 'verde') return [{ quien: 'verde', texto: 'Verde no tiene saltos y pierde el turno.' }]
    return []
  }

  async function empezar() {
    setError(null)
    setDecision(null)
    setPensando(false)
    try {
      const respuesta = await nuevaPartida()
      setPartida(respuesta)
      setEventos([
        {
          quien: 'inicio',
          texto: `Verde empieza en ${coordenada(respuesta.estado.verde)} y rojo en ${coordenada(respuesta.estado.rojo)}.`,
        },
      ])
    } catch (e) {
      setError(`No se pudo crear la partida. ${e.message}`)
    }
  }

  async function jugar(casilla) {
    if (!partida || enviando || pensando || partida.estado.turno !== 2) return
    setEnviando(true)
    setError(null)
    try {
      const respuesta = await jugadaHumano(partida.estado, casilla)
      setPartida(respuesta)
      registrar([{ quien: 'rojo', texto: `Rojo salta a ${coordenada(casilla)}.` }, ...eventoDePase(respuesta)])
    } catch (e) {
      setError(e.message)
    } finally {
      setEnviando(false)
    }
  }

  // Cuando es el turno del verde, la máquina pide su jugada al backend
  useEffect(() => {
    if (!partida || partida.terminado || partida.estado.turno !== 1) return

    let cancelado = false
    const temporizador = setTimeout(async () => {
      setPensando(true)
      setError(null)
      try {
        const { nivel, poda } = configActual.current
        const respuesta = await jugadaMaquina(partida.estado, nivel, poda)
        if (cancelado) return
        setDecision(respuesta.decision)
        setPartida(respuesta.partida)
        registrar([
          { quien: 'verde', texto: `Verde salta a ${coordenada(respuesta.decision.jugada)}.` },
          ...eventoDePase(respuesta.partida),
        ])
      } catch (e) {
        if (!cancelado) setError(`La máquina no pudo jugar. ${e.message}`)
      } finally {
        if (!cancelado) setPensando(false)
      }
    }, PAUSA_MAQUINA_MS)

    return () => {
      cancelado = true
      clearTimeout(temporizador)
    }
  }, [partida, reintentos])

  const turnoHumano = Boolean(partida && !partida.terminado && partida.estado.turno === 2 && !pensando)

  // Los valores de las candidatas se muestran en el tablero mientras el humano decide
  const candidatos =
    mostrarValores && decision && turnoHumano
      ? decision.candidatos.map((c) => ({
          ...c,
          elegido: c.jugada[0] === decision.jugada[0] && c.jugada[1] === decision.jugada[1],
        }))
      : null

  const final = partida?.terminado ? textoGanador(partida) : null

  return (
    <MotionConfig reducedMotion="user">
      <div className="pagina">
        <header className="cabecera">
          <h1>Yoshi&rsquo;s World</h1>
          <p className="estado" aria-live="polite">
            {textoEstado(partida, pensando, config)}
          </p>
        </header>

        <main className="juego">
          <div className="zona-tablero">
            <Tablero partida={partida} candidatos={candidatos} puedeJugar={turnoHumano && !enviando} onJugar={jugar} />

            <AnimatePresence>
              {!partida && (
                <motion.div className="aviso" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <p>Dos Yoshis saltan como caballos de ajedrez. Cada casilla que tocan queda de su color y nadie puede volver a usarla.</p>
                  <p>Gana quien pinte más casillas.</p>
                  <button type="button" className="boton boton--principal" onClick={empezar}>
                    Empezar partida
                  </button>
                </motion.div>
              )}
              {final && (
                <motion.div
                  className={`aviso aviso--final aviso--${partida.ganador}`}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ delay: 0.6, type: 'spring', stiffness: 200, damping: 18 }}
                >
                  <p className="aviso-titulo">{final.titulo}</p>
                  <p>{final.detalle}</p>
                  <button type="button" className="boton boton--principal" onClick={empezar}>
                    Jugar otra vez
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <aside className="panel">
            <Marcador partida={partida} />

            {error && (
              <div className="error" role="alert">
                <p>{error}</p>
                {partida && partida.estado.turno === 1 && (
                  <button type="button" className="boton" onClick={() => setReintentos((n) => n + 1)}>
                    Reintentar jugada de la máquina
                  </button>
                )}
              </div>
            )}

            <Ajustes
              config={config}
              onCambiar={setConfig}
              mostrarValores={mostrarValores}
              onMostrarValores={setMostrarValores}
              onNuevaPartida={empezar}
              hayPartida={Boolean(partida)}
            />
            <Razonamiento decision={decision} pensando={pensando} config={config} />
            <Evaluacion heuristica={partida?.heuristica} />
            <Bitacora eventos={eventos} />
          </aside>
        </main>
      </div>
    </MotionConfig>
  )
}
