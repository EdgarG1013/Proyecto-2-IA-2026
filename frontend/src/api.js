// Cliente de la API. En desarrollo Vite redirige /api al backend (vite.config.js);
// en Vercel /api lo atiende la función de Python (vercel.json).

async function post(ruta, cuerpo) {
  const respuesta = await fetch(`/api${ruta}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cuerpo),
  })
  if (!respuesta.ok) {
    let mensaje = `El servidor respondió ${respuesta.status}.`
    try {
      const datos = await respuesta.json()
      if (typeof datos.detail === 'string') mensaje = datos.detail
    } catch {
      // la respuesta no era JSON; se queda el mensaje genérico
    }
    throw new Error(mensaje)
  }
  return respuesta.json()
}

export const nuevaPartida = () => post('/partida/nueva', {})

export const jugadaHumano = (estado, jugada) =>
  post('/partida/jugada-humano', { estado, jugada })

export const jugadaMaquina = (estado, nivel, poda) =>
  post('/partida/jugada-maquina', { estado, nivel, poda })
