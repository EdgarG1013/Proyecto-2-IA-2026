# Yoshi's World

Proyecto 2 de Inteligencia Artificial (Universidad del Valle). Dos Yoshis saltan como caballos de ajedrez
sobre un tablero de 8×8 y pintan cada casilla que tocan. La máquina (verde) decide con un árbol minimax con
decisiones imperfectas, con o sin poda alfa-beta.

| Nivel        | Profundidad |
|--------------|-------------|
| Principiante | 2           |
| Amateur      | 4           |
| Experto      | 6           |

## Estructura del monorepo

```
backend/              FastAPI + lógica del juego (Python)
  juego.py            reglas: tablero, saltos de caballo, pase, fin de partida
  heuristica.py       f1, f2, f3, h(s), U(s)          (informe, secciones 3 y 4)
  minimax.py          minimax, alfabeta, decidir       (informe, secciones 7 y 8)
  main.py             endpoints /api/...
  tests/              pruebas; test_ejemplo_informe.py reproduce el ejemplo de la sección 6
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
h(raíz) = −0.234, valores de las ramas −0.103 / 0.019 / −0.019 y que la máquina juega (3,5).

## Despliegue en Vercel

1. Sube el repositorio a GitHub e impórtalo en Vercel (o ejecuta `vercel` en la raíz).
2. No hace falta configurar nada más: `vercel.json` construye `frontend/` y publica `api/index.py`
   como función de Python. Todas las rutas `/api/*` llegan a FastAPI.
3. La función tiene `maxDuration: 60` porque experto **sin poda** puede tardar unos segundos.

## Tiempos de referencia (Python 3.12, portátil)

| Nivel   | Con poda    | Sin poda    |
|---------|-------------|-------------|
| Amateur | ~30–50 ms   | ~80–190 ms  |
| Experto | ~0.2–0.5 s  | ~1.5–6 s    |

Con y sin poda la jugada elegida es siempre la misma; solo cambia cuántas hojas se evalúan.
