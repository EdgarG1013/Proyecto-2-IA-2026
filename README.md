# Yoshi's World

Proyecto 2 de Inteligencia Artificial (Universidad del Valle). Dos Yoshis saltan como caballos de ajedrez
sobre un tablero de 8×8 y pintan cada casilla que tocan. La máquina (verde) decide con un árbol minimax con
decisiones imperfectas, con o sin poda alfa-beta.

**Rama `heuristica-doble`:** la función de evaluación es h = w1·f1 + w2·f2 (casillas pintadas y movilidad),
con w = (0.4/0.7, 0.3/0.7) ≈ (0.571, 0.429). Las dos componentes miran a lo sumo un salto adelante, así que la
máquina solo ve el futuro a través de la profundidad del árbol y la dificultad crece con el nivel.
La versión con territorio (f3) está en la rama `heuristica-triple`.

| Nivel        | Profundidad |
|--------------|-------------|
| Principiante | 2           |
| Amateur      | 4           |
| Experto      | 6           |

## Estructura del monorepo

```
backend/              FastAPI + lógica del juego (Python)
  juego.py            reglas: tablero, saltos de caballo, pase, fin de partida
  heuristica.py       f1, f2, h(s), U(s); f3 se conserva solo para los experimentos
  minimax.py          minimax, alfabeta, decidir       (informe, secciones 7 y 8)
  main.py             endpoints /api/...
  tests/              pruebas; test_ejemplo_informe.py reproduce el ejemplo de profundidad 2
                      y test_heuristica_simple.py compara heurísticas y niveles
api/index.py          punto de entrada de Vercel (reexporta backend/main.py)
frontend/             React + Vite + Motion (animaciones)
vercel.json           build del frontend + función de Python en /api
requirements.txt      dependencias de Python para Vercel
```

La API no guarda partidas: el frontend envía el estado del tablero en cada petición y recibe el siguiente.
Por eso funciona igual en local y en las funciones serverless de Vercel.

| Endpoint                           | Qué hace                                                     |
|------------------------------------|--------------------------------------------------------------|
| `POST /api/partida/nueva`          | Posiciones aleatorias distintas; empieza la máquina          |
| `POST /api/partida/jugada-humano`  | Valida y aplica el salto del rojo                            |
| `POST /api/partida/jugada-maquina` | Ejecuta minimax y devuelve la jugada, el valor de cada candidata, nodos, hojas, podas y tiempo |

## Desarrollo local

Requisitos: Python 3.12 y Node 20+.

```powershell
# 1. Backend (una sola vez)
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt

# 2. Backend (cada vez) -> http://127.0.0.1:8000/docs
cd backend
..\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000

# 3. Frontend, en otra terminal -> http://localhost:5173
cd frontend
npm install
npm run dev
```

Vite redirige `/api` al puerto 8000 (`frontend/vite.config.js`).

### Pruebas

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest -q
```

`test_ejemplo_informe.py` comprueba que el código da los mismos números del informe:
h(raíz) = −0.214, valores de las ramas −0.107 / 0.000 / −0.054, que la máquina juega (3,5) y que con
poda (y ordenamiento por movilidad) evalúa 9 de las 21 hojas.

`test_heuristica_simple.py` juega partidas completas contra rivales automáticos. Para ver las tablas:

```powershell
cd backend
..\.venv\Scripts\python.exe tests\test_heuristica_simple.py
```

## Despliegue en Vercel

1. Sube el repositorio a GitHub e impórtalo en Vercel (o ejecuta `vercel` en la raíz).
2. No hace falta configurar nada más: `vercel.json` construye `frontend/` y publica `api/index.py`
   como función de Python. Todas las rutas `/api/*` llegan a FastAPI.
3. La función tiene `maxDuration: 60` como margen; con la heurística doble ninguna jugada tarda más de un segundo.

## Tiempos de referencia (Python 3.12, portátil)

| Nivel   | Con poda    | Sin poda    |
|---------|-------------|-------------|
| Amateur | ~2–3 ms     | ~3–17 ms    |
| Experto | ~7–18 ms    | ~60–230 ms  |

Con y sin poda la jugada elegida es siempre la misma; solo cambia cuántas hojas se evalúan.
