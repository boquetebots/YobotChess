# EMPIEZA AQUÍ — Windows

> La versión en inglés de esta guía es **`START HERE - Windows.md`**.

Lo normal es **una laptop, un robot, un invitado**. La laptop corre el motor de
ajedrez, el robot y el tablero en la pantalla. Alguien se sienta, toca una
pieza y juega contra el robot — que le contesta en voz alta, moviendo la boca.

Sin segunda computadora. Sin red. Sin Mac, sin Pi.

También se puede poner a dos robots a jugar *uno contra el otro*, y eso está
más abajo en esta página. Empieza por aquí.

> **¿Necesito OhbotPi2 en esta máquina?** Sí, si tiene un robot conectado —
> ahí es donde viven los motores y la voz. El juego, el tablero y todos los
> programas de prueba corren sin él. Y el ajedrez nunca te pide una llave de
> Azure; toma prestada la de OhbotPi2. Mira *What each machine actually needs*
> en `README.md`.

---

## 1. Consigue los archivos

Todo vive en GitHub, en **dos** proyectos:

| Proyecto | Qué es | Enlace |
|---|---|---|
| **OhbotPi** | el robot mismo — motores, voz, boca | <https://github.com/boquetebots/OhbotPi> |
| **YobotChess** | este — el juego, el tablero, lo que dicen | <https://github.com/boquetebots/YobotChess> |

**Una laptop con un robot conectado necesita los dos, y OhbotPi va primero.**
Logra que el robot salude por su cuenta antes de tocar el ajedrez — el ajedrez
toma prestada su voz y sus motores, y una falla de ese lado no se puede
arreglar desde este. Si esta máquina solo va a correr el juego y la pantalla,
con este proyecto solo es suficiente.

> **El ajedrez no te pide ninguna cuenta propia.** Instala primero el proyecto
> del robot — su `START_HERE_Windows.md` te lleva paso a paso. Una sola cuenta
> de voz de Microsoft Azure es todo lo que hace falta, porque esa es la voz, y
> el ajedrez la toma prestada. El proyecto del robot también tiene una función
> de conversación que necesita una segunda llave; nada del ajedrez la lee, así
> que déjala para cuando la quieras.

Haz una carpeta llamada `C:\Projects` y ponlos ahí **lado a lado**:

```
C:\Projects\
    OhbotPi2\      el robot
    Chess\         este proyecto
```

Ese arreglo no es adorno. El ajedrez encuentra el código del robot mirando en
la carpeta de al lado, así que lado a lado quiere decir que no hay nada más
que configurar.

### La forma fácil — descarga el zip

1. Abre <https://github.com/boquetebots/YobotChess>
2. Botón verde **Code** (Código), luego **Download ZIP** (Descargar ZIP)
3. Haz clic derecho en el archivo descargado, **Extract All** (Extraer todo),
   dentro de `C:\Projects`
4. **Cámbiale el nombre a la carpeta nueva, de `YobotChess-main` a `Chess`**

Haz lo mismo con <https://github.com/boquetebots/OhbotPi>, cambiándole el
nombre de `OhbotPi-main` a `OhbotPi2`.

> **A veces Windows envuelve el zip dos veces** — abres `Chess` y encuentras
> otro `YobotChess-main` adentro con todo metido ahí. Si `SETUP.bat` no está
> directamente en `C:\Projects\Chess`, sube el contenido un nivel.

### La otra forma — git

Si tienes git instalado, esto es mejor, porque `git pull` recoge los cambios
que vengan después. Un zip no se puede actualizar solo; lo tienes que
descargar de nuevo.

```
cd C:\Projects
git clone https://github.com/boquetebots/YobotChess.git Chess
```

---

## 2. Python

Abre un Command Prompt y escribe:

```
python --version
```

Si sale un número de versión, estás bien — pasa al paso 3.

Si dice "Not recognised" es que no está instalado. Consíguelo en
<https://www.python.org/downloads/>. **Cuando el instalador te pregunte, marca
la casilla que dice "Add Python to PATH."** Sin esa marca, nada de esto lo va
a encontrar.

---

## 3. Corre SETUP.bat

Haz doble clic en **`SETUP.bat`**. Una sola vez, para siempre.

Instala los tres complementos de Python y descarga Stockfish — el programa que
de verdad juega el ajedrez. Stockfish pesa 114 MB y no viene en esta descarga,
porque GitHub no acepta ningún archivo tan grande, así que la instalación lo
va a buscar. **Para esta única corrida necesitas estar conectado a internet.**
Después de eso todo funciona sin internet, menos la voz del robot.

Dale un par de minutos. Al final revisa el motor de ajedrez y te dice qué
encontró.

> A veces el antivirus se come un `.exe` recién descargado que no tiene
> publicador conocido. Si la instalación dice que el motor de ajedrez no
> arranca, busca "stockfish" en la lista de cuarentena y permítelo.

---

## 4. Pruébalo sin nada conectado

Haz doble clic en **`Demo - no robots.bat`**.

Tu navegador debe abrirse en un tablero de ajedrez, en 16:9, con una foto y un
reloj para cada lado, repitiendo una partida famosa. Eso comprueba que Python,
el motor de ajedrez, el juego y la pantalla funcionan — antes de que el
hardware esté siquiera cerca.

Cierra la ventana negra para detenerlo.

---

## 5. Revisa el robot

Un robot conectado a esta laptop necesita el proyecto **OhbotPi2** en esta
misma laptop. De ahí salen los motores, la voz de Azure y el movimiento de los
labios — el ajedrez no tiene nada de eso por su cuenta.

El ajedrez lo busca en estos lugares, en este orden, y se detiene en el primero
que tenga `yobot_core.py`, `ohbot_pi.py` y `ohbot_azure.py`:

1. `OHBOT_DIR` en un archivo llamado `.env` junto a los programas del ajedrez
2. `%USERPROFILE%\Projects\Ohbot` y `%USERPROFILE%\Projects\OhbotPi2`
3. `C:\Projects\OhbotPi2`
4. una carpeta llamada `OhbotPi2` o `Ohbot` al lado de esta

Si el tuyo está en otra parte, haz un archivo de texto simple llamado `.env` en
esta carpeta, con una sola línea adentro:

```
OHBOT_DIR=C:\Projects\OhbotPi2
```

Ahora haz que el robot diga una frase — sin ajedrez, sin juego, sin segunda
computadora:

```
python chess_player.py --say-once
```

**Mírale la boca, no solo escuches el sonido.** Si habla con la boca cerrada, o
no dice nada, la falla está del lado de OhbotPi2 y `HARDWARE_TEST.md` es la
guía para eso. Arregla eso antes de seguir; todo lo demás depende de ahí.

---

## 6. Juega con un invitado

Haz doble clic en **`Play a Human.bat`**.

El tablero se abre en esta pantalla y se pone en pantalla completa. Luego, en
la barra de control:

1. **Start game server** (Iniciar el servidor del juego)
2. **New game** (Juego nuevo)
3. **Start** (Empezar) el robot — su botón dice qué color le tocó

El robot saluda al salón y espera. Entrégale la laptop al invitado. **Toca una
pieza — sus casillas legales se iluminan. Toca una de ellas.** Esa es toda la
interfaz; a nadie hay que explicárselo dos veces.

**Deja la ventana negra abierta mientras estás jugando.** Si la cierras, todo
se detiene.

### Dos ajustes, arriba en el archivo

Abre `Play a Human.bat` en Notepad. Hay exactamente dos:

- **`GUEST`** — de qué color juega el invitado. `white` mueve primero, que es
  lo que la gente espera. El robot toma el otro.
- **`STRENGTH`** — no le muevas a esto sin una razón. `friendly` es a
  propósito. Con la fuerza de un club, el invitado pierde *todas* las partidas
  y la siguiente persona ya no pide turno. Friendly de todos modos castiga una
  pieza regalada, así que ganar significa algo.

`HUMAN_GAME.md` tiene lo demás: jugar con las negras, por qué se usa un solo
robot, y cómo pasarle el tablero a una tableta en vez de la pantalla de la
laptop.

---

## Dos robots jugando uno contra el otro

El espectáculo original, y todavía lo mejor para proyectar frente a un salón.
Necesita una **segunda computadora** con el segundo robot conectado a ella — un
Pi o una Mac — porque una sola máquina solo puede sostener el cable de un
robot.

| Máquina | Corre |
|---|---|
| Esta laptop | el juego, la pantalla, y el robot número uno |
| Un Pi o una Mac | el robot número dos |

Haz doble clic en **`Play Chess.bat`** en esta laptop, y sigue
**`START HERE - Raspberry Pi.md`** o **`MAC_SETUP.md`** en la otra máquina.

Los ajustes de arriba en `Play Chess.bat` son qué tan fuerte juegan, cuánto se
tardan entre jugadas, y qué tan atrás tiene que ir uno para rendirse.

> La segunda máquina tiene que poder alcanzar esta laptop en los puertos
> **8001** y **8002**. Windows bloquea las conexiones entrantes por defecto,
> así que este es el paso donde se atasca la gente. `MAC_SETUP.md` tiene el
> comando exacto. **El juego con invitado del paso 6 no necesita nada de
> esto** — nunca sale de la laptop.

---

## A dónde ir después

| Quiero… | Lee |
|---|---|
| El juego con invitado completo | `HUMAN_GAME.md` |
| Entender la pantalla y sus botones | `SHOW_SETUP.md` |
| Instalar el segundo robot | `START HERE - Raspberry Pi.md` o `MAC_SETUP.md` |
| Cambiar lo que dicen los robots | `chess_templates.py` — texto simple con un revisor incorporado |
| Cambiar cómo se mueven | el bloque de números de arriba en `chess_animation.py` |
| Averiguar por qué un robot está callado o quieto | `HARDWARE_TEST.md` |

---

## La que atrapa a todo el mundo

**Solo un programa a la vez puede sostener el cable del robot.** El Greeter, la
GUI, la página de calibración y el jugador de ajedrez todos quieren el mismo
puerto USB, y solo uno lo puede tener. Detén los otros primero — la página
Launcher en OhbotPi2 es la que dirige el tráfico.
