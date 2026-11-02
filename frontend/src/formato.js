// Coordenadas como en el informe: (fila, columna) empezando en 1.
export const coordenada = ([fila, columna]) => `(${fila + 1}, ${columna + 1})`

// Valores de minimax: heurística en [-1, 1] con 3 decimales; utilidades terminales (±1000 + D) enteras.
export function formatearValor(valor) {
  const signo = valor > 0 ? '+' : ''
  if (Math.abs(valor) >= 1000) return `${signo}${valor}`
  return `${signo}${valor.toFixed(3)}`
}

export const formatearEntero = (n) => n.toLocaleString('es-CO')
