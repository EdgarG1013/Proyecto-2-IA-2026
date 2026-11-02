"""
Reglas de Yoshi's World.

El tablero es una matriz 8x8 donde cada casilla vale:
    VACIO (0) -> casilla libre
    VERDE (1) -> pintada por el Yoshi verde (la máquina, MAX)
    ROJO  (2) -> pintada por el Yoshi rojo (el humano, MIN)

Las coordenadas internas son (fila, columna) empezando en 0.
En la interfaz y en el informe se muestran empezando en 1.
"""

import random
from dataclasses import dataclass

TAMANO = 8
TOTAL_CASILLAS = TAMANO * TAMANO

VACIO = 0
VERDE = 1
ROJO = 2

# Los 8 saltos posibles de un caballo de ajedrez: (cambio de fila, cambio de columna)
SALTOS_CABALLO = [
    (-2, -1), (-2, 1),
    (-1, -2), (-1, 2),
    (1, -2), (1, 2),
    (2, -1), (2, 1),
]


@dataclass
class Estado:
    tablero: list   # matriz 8x8 con VACIO, VERDE o ROJO
    verde: tuple    # (fila, columna) del Yoshi verde
    rojo: tuple     # (fila, columna) del Yoshi rojo
    turno: int      # VERDE o ROJO: a quién le toca mover

    def copiar(self):
        tablero_nuevo = [fila[:] for fila in self.tablero]
        return Estado(tablero_nuevo, self.verde, self.rojo, self.turno)

    def posicion(self, jugador):
        return self.verde if jugador == VERDE else self.rojo


def rival(jugador):
    return ROJO if jugador == VERDE else VERDE


def dentro_del_tablero(fila, columna):
    return 0 <= fila < TAMANO and 0 <= columna < TAMANO


def vecinos_caballo(casilla):
    """N(c): casillas a un salto de caballo de 'casilla' que están dentro del tablero."""
    fila, columna = casilla
    vecinos = []
    for df, dc in SALTOS_CABALLO:
        f, c = fila + df, columna + dc
        if dentro_del_tablero(f, c):
            vecinos.append((f, c))
    return vecinos


def movimientos(estado, jugador):
    """M(s): saltos legales del jugador = vecinos de caballo que siguen libres."""
    libres = []
    for f, c in vecinos_caballo(estado.posicion(jugador)):
        if estado.tablero[f][c] == VACIO:
            libres.append((f, c))
    return libres


def aplicar_movimiento(estado, casilla):
    """
    El jugador en turno salta a 'casilla' y la pinta de su color.
    Devuelve un estado NUEVO (no modifica el original) con el turno del rival.
    """
    nuevo = estado.copiar()
    jugador = estado.turno
    fila, columna = casilla
    nuevo.tablero[fila][columna] = jugador
    if jugador == VERDE:
        nuevo.verde = casilla
    else:
        nuevo.rojo = casilla
    nuevo.turno = rival(jugador)
    return nuevo


def pasar_turno(estado):
    """Regla del pase: el jugador en turno no puede moverse y le cede el turno al rival."""
    nuevo = estado.copiar()
    nuevo.turno = rival(estado.turno)
    return nuevo


def es_terminal(estado):
    """La partida termina cuando ninguno de los dos jugadores tiene saltos."""
    return not movimientos(estado, VERDE) and not movimientos(estado, ROJO)


def contar_casillas(estado, jugador):
    total = 0
    for fila in estado.tablero:
        total += fila.count(jugador)
    return total


def ganador(estado):
    """Devuelve 'verde', 'rojo' o 'empate' según quién pintó más casillas."""
    verdes = contar_casillas(estado, VERDE)
    rojas = contar_casillas(estado, ROJO)
    if verdes > rojas:
        return "verde"
    if rojas > verdes:
        return "rojo"
    return "empate"


def estado_inicial(semilla=None):
    """
    Coloca a los dos Yoshis en casillas aleatorias distintas y pinta esas casillas.
    Siempre empieza la máquina (verde).
    """
    generador = random.Random(semilla)
    todas = [(f, c) for f in range(TAMANO) for c in range(TAMANO)]
    casilla_verde, casilla_roja = generador.sample(todas, 2)

    tablero = [[VACIO] * TAMANO for _ in range(TAMANO)]
    tablero[casilla_verde[0]][casilla_verde[1]] = VERDE
    tablero[casilla_roja[0]][casilla_roja[1]] = ROJO
    return Estado(tablero, casilla_verde, casilla_roja, VERDE)
