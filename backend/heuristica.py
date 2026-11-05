"""
Función de evaluación heurística (versión doble: f1 + f2).

Todas las funciones se calculan desde el punto de vista del VERDE (la máquina):
un valor positivo es bueno para la máquina y uno negativo es bueno para el humano.

    f1 = (casillas verdes - casillas rojas) / 64        -> el presente
    f2 = (saltos del verde - saltos del rojo) / 8        -> el corto plazo (un salto)

    h(s) = w1*f1 + w2*f2                                  (estados no terminales)
    U(s) = 1000*signo(D) + D                              (estados terminales)

Las dos componentes miran a lo sumo un salto adelante. Así la máquina solo "ve el
futuro" a través de la profundidad del árbol, y la dificultad crece con el nivel:
en principiante (profundidad 2) puede escoger un salto bueno ahora que la deja
acorralada más adelante.

f3 (territorio) se conserva al final del archivo solo para los experimentos que
justifican haberla descartado: su BFS recorre todos los caminos futuros y le daba
a la máquina una visión a largo plazo que volvía casi imposible el nivel principiante.
"""

from collections import deque

from juego import (
    TAMANO, TOTAL_CASILLAS, VACIO, VERDE, ROJO,
    vecinos_caballo, movimientos, contar_casillas, es_terminal,
)

# Pesos w1, w2: no negativos, suman 1 y w1 > 0.
# Conservan la proporción 0.4 : 0.3 de la versión triple (0.4/0.7 ≈ 0.571 y 0.3/0.7 ≈ 0.429).
PESOS = (0.4 / 0.7, 0.3 / 0.7)

INFINITO = float("inf")


# ---------------------------------------------------------------------------
# f1: diferencia de casillas pintadas
# ---------------------------------------------------------------------------
def diferencia_pintadas(estado):
    """D(s) = |P_V| - |P_R|"""
    return contar_casillas(estado, VERDE) - contar_casillas(estado, ROJO)


def f1(estado):
    return diferencia_pintadas(estado) / TOTAL_CASILLAS


# ---------------------------------------------------------------------------
# f2: diferencia de movilidad
# ---------------------------------------------------------------------------
def f2(estado):
    saltos_verde = len(movimientos(estado, VERDE))
    saltos_rojo = len(movimientos(estado, ROJO))
    return (saltos_verde - saltos_rojo) / 8


# ---------------------------------------------------------------------------
# Heurística combinada, utilidad terminal y evaluación
# ---------------------------------------------------------------------------
def h(estado, pesos=PESOS):
    w1, w2 = pesos
    return w1 * f1(estado) + w2 * f2(estado)


def utilidad(estado):
    """
    Valor exacto de un estado terminal: más de 1000 si gana el verde,
    menos de -1000 si gana el rojo y 0 si hay empate. Sumar D hace que la
    máquina prefiera ganar por más casillas (o perder por menos).
    """
    d = diferencia_pintadas(estado)
    if d > 0:
        signo = 1
    elif d < 0:
        signo = -1
    else:
        signo = 0
    return 1000 * signo + d


def evaluar(estado, pesos=PESOS):
    """Eval(s): utilidad si la partida terminó, heurística h si no."""
    if es_terminal(estado):
        return utilidad(estado)
    return h(estado, pesos)


def detalle(estado, pesos=PESOS):
    """Todas las piezas de la heurística, para mostrarlas en la interfaz."""
    terminal = es_terminal(estado)
    return {
        "terminal": terminal,
        "utilidad": utilidad(estado) if terminal else None,
        "pintadas_verde": contar_casillas(estado, VERDE),
        "pintadas_rojo": contar_casillas(estado, ROJO),
        "saltos_verde": len(movimientos(estado, VERDE)),
        "saltos_rojo": len(movimientos(estado, ROJO)),
        "f1": f1(estado),
        "f2": f2(estado),
        "pesos": list(pesos),
        "h": h(estado, pesos),
    }


# ---------------------------------------------------------------------------
# f3: diferencia de territorio (DESCARTADA, no se usa en h)
# Se conserva para los experimentos de tests/test_heuristica_simple.py.
# ---------------------------------------------------------------------------
def distancias_bfs(estado, origen):
    """
    Búsqueda en anchura desde 'origen' que solo avanza por casillas libres.
    Devuelve una matriz 8x8 con el mínimo número de saltos para llegar
    a cada casilla (INFINITO si no se puede llegar).
    """
    distancia = [[INFINITO] * TAMANO for _ in range(TAMANO)]
    distancia[origen[0]][origen[1]] = 0
    cola = deque([origen])

    while cola:
        actual = cola.popleft()
        for f, c in vecinos_caballo(actual):
            libre = estado.tablero[f][c] == VACIO
            no_visitada = distancia[f][c] == INFINITO
            if libre and no_visitada:
                distancia[f][c] = distancia[actual[0]][actual[1]] + 1
                cola.append((f, c))

    return distancia


def territorio(estado):
    """
    Cada casilla libre es del Yoshi que llega a ella en MENOS saltos.
    Si llegan en el mismo número de saltos (o ninguno llega) no cuenta para nadie.
    Devuelve (T_V, T_R).
    """
    dist_verde = distancias_bfs(estado, estado.verde)
    dist_rojo = distancias_bfs(estado, estado.rojo)

    territorio_verde = 0
    territorio_rojo = 0
    for f in range(TAMANO):
        for c in range(TAMANO):
            if estado.tablero[f][c] != VACIO:
                continue
            if dist_verde[f][c] < dist_rojo[f][c]:
                territorio_verde += 1
            elif dist_rojo[f][c] < dist_verde[f][c]:
                territorio_rojo += 1

    return territorio_verde, territorio_rojo


def f3(estado):
    territorio_verde, territorio_rojo = territorio(estado)
    return (territorio_verde - territorio_rojo) / TOTAL_CASILLAS


def h_triple(estado):
    """Heurística de la versión triple, h = 0.4*f1 + 0.3*f2 + 0.3*f3 (solo para comparar)."""
    return 0.4 * f1(estado) + 0.3 * f2(estado) + 0.3 * f3(estado)
