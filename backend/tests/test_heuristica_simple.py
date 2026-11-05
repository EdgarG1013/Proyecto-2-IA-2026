"""
Experimento: ¿qué tan fácil es ganarle a la máquina con cada heurística y en cada nivel?

Se juegan partidas completas entre la máquina (verde) y tres jugadores rojos automáticos
que imitan a personas con distinta habilidad. Se comparan tres funciones de evaluación:

    solo f1:   f1 = (casillas verdes - casillas rojas) / 64
    doble:     h  = w1*f1 + w2*f2           (la que usa el juego en esta versión)
    triple:    h  = 0.4*f1 + 0.3*f2 + 0.3*f3 (versión anterior, con territorio)

Parte 1: las tres heurísticas en principiante (profundidad 2).
Parte 2: la heurística doble en principiante, amateur y experto (2, 4 y 6).

Cómo ejecutarlo (desde la carpeta backend):

    Ver las tablas de resultados (unos 30 segundos):
        python tests/test_heuristica_simple.py

    Comprobarlo como prueba automática:
        python -m pytest tests/test_heuristica_simple.py -v
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
from heuristica import f1, h, h_triple  # noqa: E402
from minimax import decidir, PROFUNDIDAD_POR_NIVEL  # noqa: E402

PARTIDAS = 40          # cada partida empieza en una posición aleatoria distinta
SEMILLA_BASE = 1000    # semillas fijas: los resultados son siempre los mismos

# nombre -> (función de evaluación, usar poda)
# f1 sola juega sin poda a propósito: con poda, el ordenamiento por movilidad decide
# los empates y f1 estaría usando la movilidad "a escondidas". El valor minimax es el
# mismo con y sin poda; solo cambia cuál de las jugadas empatadas se escoge.
HEURISTICAS = {
    "solo f1": (f1, False),
    "doble (f1+f2)": (h, True),
    "triple (f1+f2+f3)": (h_triple, True),
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
    Piensa en movilidad y en territorio (heurística triple) pero sin mirar la respuesta
    del verde. Es el mismo rival en las dos versiones del proyecto, para poder comparar.
    """
    return min(movimientos(estado, ROJO), key=lambda jugada: h_triple(aplicar_movimiento(estado, jugada)))


RIVALES = {
    "aleatorio": rojo_aleatorio,
    "intuitivo": rojo_intuitivo,
    "estratega": rojo_estratega,
}


# ---------------------------------------------------------------------------
# Partidas
# ---------------------------------------------------------------------------
def jugar_partida(semilla, nombre_heuristica, rival, profundidad):
    """
    Juega una partida completa y devuelve (casillas verdes, casillas rojas,
    jugadas de la máquina, jugadas en las que todas sus opciones valían lo mismo).
    """
    heuristica, usar_poda = HEURISTICAS[nombre_heuristica]
    azar = random.Random(semilla)
    estado = estado_inicial(semilla)
    jugadas_maquina = 0
    jugadas_a_ciegas = 0

    while not es_terminal(estado):
        if not movimientos(estado, estado.turno):
            estado = pasar_turno(estado)  # regla del pase
            continue

        if estado.turno == VERDE:
            decision = decidir(estado, profundidad, usar_poda=usar_poda, heuristica=heuristica)
            jugadas_maquina += 1
            valores = {c["valor"] for c in decision["candidatos"]}
            if len(decision["candidatos"]) > 1 and len(valores) == 1 and not usar_poda:
                jugadas_a_ciegas += 1
            jugada = decision["jugada"]
        else:
            jugada = rival(estado, azar)

        estado = aplicar_movimiento(estado, jugada)

    return contar_casillas(estado, VERDE), contar_casillas(estado, ROJO), jugadas_maquina, jugadas_a_ciegas


@lru_cache(maxsize=None)
def resultados(nombre_heuristica, nombre_rival, profundidad):
    """Juega PARTIDAS partidas y resume el resultado desde el punto de vista del rojo."""
    rival = RIVALES[nombre_rival]
    resumen = {"gana_rojo": 0, "empates": 0, "gana_maquina": 0, "margen_rojo": 0,
               "jugadas_maquina": 0, "jugadas_a_ciegas": 0}

    for i in range(PARTIDAS):
        verdes, rojas, jugadas, a_ciegas = jugar_partida(SEMILLA_BASE + i, nombre_heuristica, rival, profundidad)
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
PRINCIPIANTE = PROFUNDIDAD_POR_NIVEL["principiante"]


@pytest.mark.parametrize("nombre_rival", list(RIVALES))
def test_en_principiante_la_doble_es_mas_facil_de_ganar_que_la_triple(nombre_rival):
    doble = resultados("doble (f1+f2)", nombre_rival, PRINCIPIANTE)
    triple = resultados("triple (f1+f2+f3)", nombre_rival, PRINCIPIANTE)
    assert puntos_rojo(doble) > puntos_rojo(triple)


@pytest.mark.parametrize("nombre_rival", list(RIVALES))
def test_con_la_doble_la_dificultad_sube_con_el_nivel(nombre_rival):
    principiante = resultados("doble (f1+f2)", nombre_rival, PROFUNDIDAD_POR_NIVEL["principiante"])
    amateur = resultados("doble (f1+f2)", nombre_rival, PROFUNDIDAD_POR_NIVEL["amateur"])
    experto = resultados("doble (f1+f2)", nombre_rival, PROFUNDIDAD_POR_NIVEL["experto"])
    assert puntos_rojo(principiante) > puntos_rojo(amateur) >= puntos_rojo(experto)


def test_f1_sola_decide_a_ciegas_la_mayoria_de_las_veces():
    """
    Propiedad 4 del informe: en profundidad 2 todas las hojas tienen el mismo f1
    (salvo que alguien quede encerrado), así que la máquina no distingue sus jugadas.
    Por eso f1 sola no sirve y se combina con f2.
    """
    solo_f1 = resultados("solo f1", "intuitivo", PRINCIPIANTE)
    assert solo_f1["jugadas_a_ciegas"] / solo_f1["jugadas_maquina"] > 0.5


# ---------------------------------------------------------------------------
# Tablas para el informe
# ---------------------------------------------------------------------------
def imprimir_encabezado(columna):
    encabezado = (f"{'Rival (rojo)':<12} {columna:<20} {'Gana rojo':>9} {'Empates':>8} "
                  f"{'Gana máquina':>13} {'Margen rojo':>12}")
    print(encabezado)
    print("-" * len(encabezado))


def imprimir_fila(nombre_rival, etiqueta, r):
    print(f"{nombre_rival:<12} {etiqueta:<20} {r['gana_rojo']:>9} {r['empates']:>8} "
          f"{r['gana_maquina']:>13} {r['margen_rojo'] / PARTIDAS:>+12.1f}")


def imprimir_tablas():
    print(f"\nParte 1. Principiante (profundidad {PRINCIPIANTE}), {PARTIDAS} partidas por fila\n")
    imprimir_encabezado("Heurística")
    for nombre_rival in RIVALES:
        for nombre_heuristica in HEURISTICAS:
            imprimir_fila(nombre_rival, nombre_heuristica, resultados(nombre_heuristica, nombre_rival, PRINCIPIANTE))
        print()

    solo_f1 = resultados("solo f1", "intuitivo", PRINCIPIANTE)
    print(f"Con solo f1, en el {100 * solo_f1['jugadas_a_ciegas'] / solo_f1['jugadas_maquina']:.0f} % de sus jugadas "
          "todas las opciones de la máquina valían lo mismo (decide a ciegas).")

    print(f"\nParte 2. Heurística doble (f1+f2) en cada nivel, {PARTIDAS} partidas por fila\n")
    imprimir_encabezado("Nivel")
    for nombre_rival in RIVALES:
        for nivel, profundidad in PROFUNDIDAD_POR_NIVEL.items():
            etiqueta = f"{nivel} ({profundidad})"
            imprimir_fila(nombre_rival, etiqueta, resultados("doble (f1+f2)", nombre_rival, profundidad))
        print()

    print("Margen rojo: casillas del rojo menos casillas del verde, en promedio por partida.")


if __name__ == "__main__":
    imprimir_tablas()
