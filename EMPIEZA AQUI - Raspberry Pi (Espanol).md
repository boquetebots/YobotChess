# EMPIEZA AQUÍ — Raspberry Pi

> La versión en inglés de esta guía es **`START HERE - Raspberry Pi.md`**.

Un Pi en este sistema es **la computadora que maneja al robot**. Maneja un
solo robot: le pregunta al juego "¿qué digo y cómo me muevo?", lo dice con la
boca moviéndose, y anima la cabeza y los ojos entre turno y turno.

**El Pi no sabe absolutamente nada de ajedrez.** Ni tablero, ni motor de
ajedrez, ni reglas. Eso vive en la computadora que esté corriendo
`chess_server.py`, y es a propósito — un solo tablero, un solo juego, y cero
posibilidad de que los dos robots estén jugando partidas distintas sin que
nadie se dé cuenta.

Un Pi *sí puede* correr todo el espectáculo si tú quieres. Simplemente casi
nunca lo hace.

---

## Antes de empezar

> **¿Necesito OhbotPi2 en esta máquina?** Solo si hay un robot conectado a
> ella. El juego, la pantalla y todos los scripts de prueba funcionan sin él.
> Y el ajedrez nunca te pide una llave de Azure — se la presta de OhbotPi2.
> Mira *What each machine actually needs* en `README.md`.


**El Pi necesita tener ya el proyecto OhbotPi2 instalado y funcionando.** De
ahí salen los motores, la voz y la sincronización de los labios. Si el robot
todavía no puede decir hola, detente aquí y arregla eso primero:

<https://github.com/boquetebots/OhbotPi>

También necesitas saber el **nombre o la dirección de la computadora que corre
el juego** — normalmente la PC con Windows. En una red Tailscale basta con el
nombre (`yobot1`, `lester-pc`); si no, consigue su dirección con `ipconfig` en
Windows o `hostname -I` en un Pi.

---

## 1. Baja los archivos al Pi

Entra por SSH y después:

```bash
cd ~/Projects
git clone https://github.com/boquetebots/YobotChess.git Chess
cd Chess
```

Más adelante, para recoger cualquier cambio:

```bash
cd ~/Projects/Chess
git pull
```

---

## 2. Corre el instalador

```bash
bash install.sh
```

Encuentra OhbotPi2, instala los tres complementos de Python **en el mismo
Python que usa OhbotPi2**, instala Stockfish, y escribe dos scripts cortos
para arrancar todo.

> **Por qué importa lo del "mismo Python".** OhbotPi2 en un Pi corre dentro de
> un entorno virtual — su propio Python privado en `~/Projects/Ohbot/venv`. Si
> los complementos de ajedrez se instalan en el Python del *sistema*, te sale
> "no module named chess" de un robot que por lo demás está perfectamente
> sano, y nada en ese mensaje te dice por qué. El instalador se encarga de
> esto; solo es un problema si instalas a mano.

El instalador te pide la contraseña una vez, para Stockfish.

---

## 3. Comprueba que el robot funciona, por su cuenta

Sin juego, sin servidor, sin ninguna otra computadora:

```bash
~/Projects/Ohbot/venv/bin/python3 chess_player.py --say-once
```

Debe decir una sola frase **con la boca moviéndose**. Si la boca se queda
cerrada o el robot se queda callado, la falla está en OhbotPi2, no aquí —
mira `HARDWARE_TEST.md`.

También puedes verlo moverse sin habla y sin nada de ajedrez:

```bash
~/Projects/Ohbot/venv/bin/python3 chess_player.py --animate-demo
```

Y ver la pantalla del público sin tener nada conectado:

```bash
bash demo.sh
```

Después abre `http://THE-PI-NAME:8080/` desde cualquier navegador en la red.

---

## 4. Apúntalo hacia el juego

Abre **`play-white.sh`** (o `play-black.sh`) en un editor de texto. Hay que
cambiar una sola línea:

```bash
SERVER="localhost"
```

Pon entre las comillas el nombre o la dirección de la computadora que corre el
juego. Guarda.

Después arranca el robot:

```bash
bash play-white.sh
```

Haz esto en la computadora de cada robot, un color para cada uno. Arranca el
juego desde los botones de la pantalla, o desde la computadora que corre el
servidor.

> **`--start` va en UN SOLO robot.** Si los dos lo mandan, se reinician el
> juego uno al otro y nunca pasan de la primera jugada.

---

## 5. Firewall

El Pi tiene que poder llegar a los puertos **8001** (blancas) y **8002**
(negras) del servidor. Los Pi normalmente no bloquean las conexiones que
salen, así que casi siempre esto es una configuración de la *otra* computadora
— Windows bloquea por defecto las conexiones que entran. `MAC_SETUP.md` tiene
el comando exacto para abrirlo.

Pruébalo desde el Pi antes de echarle la culpa a otra cosa:

```bash
curl http://THE-SERVER-NAME:8001/state
```

Si sale algo de JSON, la red está bien. Si se queda colgado o dice "connection
refused", el servidor no está corriendo, o el firewall está estorbando.

---

## Correr dos robots desde dos Pi

Ese es el arreglo normal una vez que tienes dos. Cada Pi corre su propio
`chess_player.py`, y los dos apuntan al **mismo** servidor:

| Máquina | Corre |
|---|---|
| La PC (o uno de los Pi) | `chess_server.py` y `chess_show.py` |
| Pi número uno | `bash play-white.sh` |
| Pi número dos | `bash play-black.sh` |

---

## Arrancar automáticamente

No hay un servicio de systemd para el ajedrez, y es a propósito. El jugador de
ajedrez compite con el Greeter por el único cable serial del robot, así que un
servicio de ajedrez que arrancara solo al prender la máquina pelearía con el
trabajo normal del robot cada vez. Arráncalo cuando quieras jugar una partida,
y párralo cuando termines.

Si más adelante sí quieres uno, copia el patrón de los servicios de usuario de
OhbotPi2 — corren sin `sudo`, y ese es todo el truco.

---

## A dónde ir después

| Quiero… | Lee |
|---|---|
| Entender la pantalla y sus botones | `SHOW_SETUP.md` |
| Dejar que un invitado juegue contra un robot | `HUMAN_GAME.md` |
| Cambiar lo que dicen los robots | `chess_templates.py` |
| Cambiar cómo se mueven los robots | los números al principio de `chess_animation.py` |
| Averiguar por qué un robot está callado o quieto | `HARDWARE_TEST.md` |
