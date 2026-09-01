# EMPIEZA AQUÍ — Mac

> La versión en inglés de esta guía es **`START HERE - Mac.md`**.

Una Mac en este sistema normalmente maneja **al segundo robot** — Goldie —
mientras la PC con Windows corre el juego. También puede correr todo el
espectáculo ella sola.

El recorrido completo de las dos computadoras, con los comandos del firewall y
la trampa de la calibración, está en **`MAC_SETUP.md`**. Esta página es la
versión corta.

> **¿Necesito OhbotPi2 en esta máquina?** Solo si hay un robot conectado a
> ella. El juego, la pantalla y todos los scripts de prueba funcionan sin él.
> Y el ajedrez nunca te pide una llave de Azure — se la presta de OhbotPi2.
> Mira *What each machine actually needs* en `README.md`.

---

## 1. Consigue los archivos

```bash
cd ~/Projects
git clone https://github.com/boquetebots/YobotChess.git Chess
cd Chess
```

Vale la pena ponerlo en `~/Projects`, al lado de `OhbotPi2` — el ajedrez busca
ahí el código del robot sin que tengas que decírselo.

---

## 2. Corre el instalador

```bash
bash install.sh
```

Encuentra OhbotPi2, instala los tres complementos de Python en el mismo Python
que él usa, instala Stockfish con Homebrew si lo tienes, y escribe dos scripts
cortos para arrancar todo.

**¿No tienes Homebrew?** No pasa nada en una Mac que solo maneja un robot —
solo la computadora que corre `chess_server.py` necesita el motor de ajedrez.
Instala Homebrew desde <https://brew.sh> si esta Mac va a correr el juego.

---

## 3. Comprueba que el robot funciona, por su cuenta

```bash
~/yobot-venv/bin/python3 chess_player.py --say-once
```

Una sola frase, **con la boca moviéndose**.

> **Usa `~/yobot-venv/bin/python3`, no `python3` a secas.** El Python propio
> de la Mac no tiene adentro los paquetes del robot, y el error que te sale no
> dice nada útil sobre por qué. `install.sh` pone los complementos de ajedrez
> en ese mismo lugar, así que este único comando lo tiene todo. Si aun así no
> funciona, la falla está en OhbotPi2 —
mira `HARDWARE_TEST.md`.

---

## 4. Únete a un juego que está corriendo en la PC

Abre **`play-black.sh`** y pon la dirección de la PC en la línea `SERVER`:

```bash
SERVER="192.168.50.42"
```

Después:

```bash
bash play-black.sh
```

También existe **`chess_show_agent.py`**, que le permite al botón "Start
Goldie" (Iniciar a Goldie) de la PC arrancarla por la red, para que no tengas
que tocar la Mac en absoluto. `MAC_SETUP.md` lo explica.

---

## 5. O corre todo aquí mismo

```bash
~/yobot-venv/bin/python3 chess_show.py --strength club --gap 0.8
```

Después abre <http://localhost:8080/>. Sin nada conectado, absolutamente nada:

```bash
~/yobot-venv/bin/python3 chess_show.py --demo
```

---

## La que te va a agarrar desprevenido

**Cada computadora guarda su propia calibración.** `MotorDefinitionsv21.omd`
*no* se comparte por git, y eso es a propósito — compartirlo una sola vez le
puso a Goldie la boca de Lester. Los robots guardados en `ohbotData/robots/`
**sí** se comparten, y cargar el que quieres desde esa biblioteca es la forma
en que se supone que una calibración viaje de una computadora a otra.

`MAC_SETUP.md` tiene los detalles, incluyendo qué hacer antes de tu próximo
`git pull` en OhbotPi2.
