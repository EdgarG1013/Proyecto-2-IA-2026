"""
Experimento: ¿la dificultad del nivel principiante viene de la heurística combinada?

Se juegan partidas completas con la máquina (verde) en profundidad 2, la del nivel
principiante, usando dos funciones de evaluación distintas:

    simple:     f1 = (casillas verdes - casillas rojas) / 64
    combinada:  h  = 0.4*f1 + 0.3*f2 + 0.3*f3   (la que usa el juego)

contra tres tipos de jugador rojo que imitan a personas con distinta habilidad.
Si la heurística es la causa de la dificultad, el rojo debe ganarle más veces
a la máquina que usa solo f1.

Cómo ejecutarlo (desde la carpeta backend):

    Ver la tabla de resultados:
        ..\\.venv\\Scripts\\python.exe tests\\test_heuristica_simple.py

    Comprobarlo como prueba automática:
        ..\\.venv\\Scripts\\python.exe -m pytest tests\\test_heuristica_simple.py -v
"""

import os
import random
import sys
from functools import lru_cache

import pytest

# Al ejecutarlo como script, Python no ve la carpeta backend; pytest sí (pytest.ini)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from juego import (  # noqa: E402
    VERDE, ROJO, estado_inicial, movimientos, aplicar_movimiento,
    pasar_turno, es_terminal, contar_casillas,
)
from heuristica import f1, h  # noqa: E402
from minimax import decidir  # noqa: E402

PROFUNDIDAD_PRINCIPIANTE = 2
PARTIDAS = 40          # cada partida empieza en una posición aleatoria distinta
SEMILLA_BASE = 1000    # semillas fijas: los resultados son siempre los mismos

HEURISTICAS = {
    "simple (solo f1)": f1,
    "combinada (h)": h,
}


# ---------------------------------------------------------------------------
# Jugadores rojos (el "humano")
# ---------------------------------------------------------------------------
def rojo_aleatorio(estado, azar):
    """Salta a cualquier casilla legal: una persona que no piensa la jugada."""
    return azar.choice(movimientos(estado, ROJO))


def rojo_intuitivo(estado, azar):
    """
    Mira una sola jugada: escoge el salto que lo deja con más saltos que el verde.
    Es como juega una persona que entendió que quedarse sin salidas es perder.
    """
    def ventaja(jugada):
        hijo = aplicar_movimiento(estado, jugada)
        return len(movimientos(hijo, ROJO)) - len(movimientos(hijo, VERDE))

    return max(movimientos(estado, ROJO), key=ventaja)


def rojo_estratega(estado, azar):
    """
    Usa la heurística combinada pero sin mirar la respuesta del verde (profundidad 1):
    una persona que piensa en movilidad y en territorio.
    """
    return min(movimientos(estado, ROJO), key=lambda jugada: h(aplicar_movimiento(estado, jugada)))


RIVALES = {
    "aleatorio": rojo_aleatorio,
    "intuitivo": rojo_intuitivo,
    "estratega": rojo_estratega,
}


# ---------------------------------------------------------------------------
# Partidas
# ---------------------------------------------------------------------------
def jugar_partida(semilla, heuristica, rival):
    """
    Juega una partida completa y devuelve (casillas verdes, casillas rojas,
    jugadas de la máquina, jugadas en las que todas sus opciones valían lo mismo).
    """
    azar = random.Random(semilla)
    estado = estado_inicial(semilla)
    jugadas_maquina = 0
    jugadas_a_ciegas = 0

    while not es_terminal(estado):
        if not movimientos(estado, estado.turno):
            estado = pasar_turno(estado)  # regla del pase
            continue

        if estado.turno == VERDE:
            # Sin poda a propósito: con poda, el ordenamiento por movilidad decide los
            # empates y f1 estaría usando la movilidad "a escondidas". El valor minimax
            # es el mismo con y sin poda; solo cambia cuál de las empatadas se escoge.
            decision = decidir(estado, PROFUNDIDAD_PRINCIPIANTE, usar_poda=False, heuristica=heuristica)
            valores = {c["valor"] for c in decision["candidatos"]}
            jugadas_maquina += 1
            if len(decision["candidatos"]) > 1 and len(valores) == 1:
                jugadas_a_ciegas += 1
            jugada = decision["jugada"]
        else:
            jugada = rival(estado, azar)

        estado = aplicar_movimiento(estado, jugada)

    return contar_casillas(estado, VERDE), contar_casillas(estado, ROJO), jugadas_maquina, jugadas_a_ciegas


@lru_cache(maxsize=None)
def resultados(nombre_heuristica, nombre_rival):
    """Juega PARTIDAS partidas y resume el resultado desde el punto de vista del rojo."""
    heuristica = HEURISTICAS[nombre_heuristica]
    rival = RIVALES[nombre_rival]
    resumen = {"gana_rojo": 0, "empates": 0, "gana_maquina": 0, "margen_rojo": 0,
               "jugadas_maquina": 0, "jugadas_a_ciegas": 0}

    for i in range(PARTIDAS):
        verdes, rojas, jugadas, a_ciegas = jugar_partida(SEMILLA_BASE + i, heuristica, rival)
        resumen["margen_rojo"] += rojas - verdes
        resumen["jugadas_maquina"] += jugadas
        resumen["jugadas_a_ciegas"] += a_ciegas
        if rojas > verdes:
            resumen["gana_rojo"] += 1
        elif verdes > rojas:
            resumen["gana_maquina"] += 1
        else:
            resumen["empates"] += 1

    return resumen


def puntos_rojo(resumen):
    """Victoria = 1 punto, empate = 0.5."""
    return resumen["gana_rojo"] + 0.5 * resumen["empates"]


# ---------------------------------------------------------------------------
# Pruebas
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("nombre_rival", list(RIVALES))
def test_es_mas_facil_ganarle_a_la_heuristica_simple(nombre_rival):
    simple = resultados("simple (solo f1)", nombre_rival)
    combinada = resultados("combinada (h)", nombre_rival)
    assert puntos_rojo(simple) > puntos_rojo(combinada)


def test_con_f1_la_maquina_decide_a_ciegas_la_mayoria_de_las_veces():
    """
    Propiedad 4 del informe: en profundidad 2 todas las hojas tienen el mismo f1
    (salvo que alguien quede encerrado), así que la máquina no distingue sus jugadas.
    """
    simple = resultados("simple (solo f1)", "intuitivo")
    combinada = resultados("combinada (h)", "intuitivo")
    assert simple["jugadas_a_ciegas"] / simple["jugadas_maquina"] > 0.5
    assert combinada["jugadas_a_ciegas"] / combinada["jugadas_maquina"] < 0.1


# ---------------------------------------------------------------------------
# Tabla para el informe
# ---------------------------------------------------------------------------
def imprimir_tabla():
    print(f"\nMáquina en profundidad {PROFUNDIDAD_PRINCIPIANTE} (principiante), {PARTIDAS} partidas por fila\n")
    encabezado = (f"{'Rival (rojo)':<11} {'Heurística de la máquina':<25} {'Gana rojo':>9} "
                  f"{'Empates':>8} {'Gana máquina':>13} {'Margen rojo':>12} {'Jugadas a ciegas':>17}")
    print(encabezado)
    print("-" * len(encabezado))

    for nombre_rival in RIVALES:
        for nombre_heuristica in HEURISTICAS:
            r = resultados(nombre_heuristica, nombre_rival)
            a_ciegas = 100 * r["jugadas_a_ciegas"] / r["jugadas_maquina"]
            print(f"{nombre_rival:<11} {nombre_heuristica:<25} {r['gana_rojo']:>9} {r['empates']:>8} "
                  f"{r['gana_maquina']:>13} {r['margen_rojo'] / PARTIDAS:>+12.1f} {a_ciegas:>16.0f}%")
        print()



if __name__ == "__main__":
    imprimir_tabla()
