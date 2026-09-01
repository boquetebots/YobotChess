#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chess_templates_es.py — the things the robots say about their moves, in Spanish
================================================================================

THE SPANISH TWIN of `chess_templates.py`. Read that file's docstring first —
every rule in it (the comma at the end of a line, no slashes, no digits,
finishing the sentence right after {move}, castling reading as a verb) applies
here exactly the same way. This file only adds one more:

--------------------------------------------------------------------------------
RULE SEVEN: WRITE REAL SPANISH, ACCENTS AND ALL
--------------------------------------------------------------------------------

`chess_templates.py` deliberately drops accents from place names, because
that file is read by an ENGLISH voice and accented characters made Azure
hesitate. This file is read by a SPANISH voice, for which accents are not
decoration — they are how the word is pronounced correctly, and this file's
text is also shown on screen in the log window, where a Panamanian audience
would notice a missing accent immediately. So: "Chiriquí", not "Chiriqui".
"Volcán", not "Volcan". "Jugué", not "Jugue".

Opening ¿ and ¡ marks are used properly (`¿Qué tal {move}?`) for the same
reason — this text is read on screen, not just heard.

--------------------------------------------------------------------------------
WHY A SEPARATE FILE INSTEAD OF A TRANSLATION COLUMN
--------------------------------------------------------------------------------

A dictionary of English line -> Spanish line would look tidy, but it is a
trap: every list here is FUNNY IN SPANISH ON ITS OWN TERMS rather than word
for word translated, and a joke that lands in English rarely lands the same
way moved straight across. "Step aside, tin man" means nothing in Spanish;
"Hazte a un lado, lata" ('lata' = tin can, and also Panamanian slang for
something worn out) is the equivalent joke, not the same sentence. Keeping
this as its own file, with its own fifteen categories in the same order and
the same four-block shape, means either language bank can be edited, checked
and rebalanced without touching the other one.

--------------------------------------------------------------------------------
HOW chess_commentary.py USES THIS
--------------------------------------------------------------------------------

`CommentaryWriter(lang="es")` picks this module's ANNOUNCE_ES / TEMPLATES_ES /
GAME_START_ES / GAME_END_ES instead of the English ones. Polite mode ("leave
out the Sassy block") is not duplicated here — `chess_templates.without_tone`
already takes any templates dict as an argument, so the same function strips
the Sassy block from this file's TEMPLATES_ES too.

--------------------------------------------------------------------------------
CHECKING YOUR WORK
--------------------------------------------------------------------------------

    python chess_templates_es.py

Same checks as the English file, plus the Spanish castling-subject words.
"""

from chess_templates import BLOCK_SIZE, TONE_BLOCKS


# ── The bare announcements ───────────────────────────────────────────────────
# See chess_templates.py for why this list has to be long. Every line here
# MUST contain {move}.

ANNOUNCE_ES = [
    # ── Lo más sencillo ──────────────────────────────
    "{move}.",
    "Jugué {move}.",
    "Juego {move}.",
    "Mi jugada es {move}.",
    "Mi jugada, {move}.",
    "Mi elección es {move}.",
    "Elijo {move}.",
    "Voy con {move}.",
    "Hago {move}.",
    "Opto por {move}.",
    "Selecciono {move}.",
    "Jugando {move}.",
    "Eso es {move}.",
    "Aquí está {move}.",
    "Aquí viene {move}.",
    "Entonces {move}.",
    "Bien. {move}.",
    "Muy bien. {move}.",
    "Mi turno. {move}.",
    "Voy a jugar {move}.",

    # ── Cediendo el turno ────────────────────────────
    "{move}. Tu turno.",
    "{move}. Te toca.",
    "{move}. Sigues tú.",
    "{move}. De vuelta a ti.",
    "{move}. Adelante.",
    "{move}. Ahora tu jugada.",
    "{move}. Cuando estés listo.",
    "{move}. Tómate tu tiempo.",
    "{move}. Piénsalo.",
    "Respondo con {move}.",
    "Contesto con {move}.",
    "Reacciono con {move}.",

    # ── Con un dejo de indiferencia ──────────────────
    "{move}. Listo.",
    "{move}. Eso sirve.",
    "{move}. Nada elegante.",
    "{move}. Así de simple.",
    "{move}. Seguimos.",
    "{move}. Siguiente.",
    "Tranquilamente, {move}.",
    "Sin drama, {move}.",
    "¿Qué tal {move}?",
    "Digamos que {move}.",

    # ── Con sabor a robot, pero sigue siendo solo un anuncio ──
    "{move}. Registrado.",
    "{move}. Ejecutado.",
    "{move}. Confirmado.",
    "{move}. Procesado.",
    "{move}. Anotado.",
    "{move}. Guardado.",
    "Calculando. {move}.",
    "Decisión tomada. {move}.",
    "Salida, {move}.",
]


TEMPLATES_ES = {

    # ── desarrollo de apertura ───────────────────────────────
    'opening_development': [
        # --- Generic ---
        "Jugué {move}. Mis piezas están listas. Las tuyas se ven nerviosas.",
        "Mi jugada es {move}. Cada pieza necesita una buena casilla.",
        "Con {move}, estoy movilizando todo. Tú sigues calentando.",
        "Opto por {move}. Una jugada de libro que se te olvidó.",
        "Elijo {move}. Armonía de mi lado, caos del tuyo.",
        # --- Sassy ---
        "Jugué {move}. Sacando mis piezas mientras tú sigues dormido.",
        "Juego {move}. Espero que hoy hayas traído un plan de verdad.",
        "Mi jugada es {move}. Paso uno de tu humillación completa.",
        "Mi elección es {move}. Esto lo hago fácil.",
        "Voy con {move}. Todo en su lugar. A diferencia de tus ideas.",
        # --- Local ---
        "Juego {move}. Desarrollo rápido. Aquí no esperamos el bus a El Salto.",
        "Jugué {move}. Mis piezas salieron temprano. Las tuyas siguen en Bugaba.",
        "Opto por {move}. Desarrollo tranquilo. Ya viene un aguacero para ti.",
        "Juego {move}. Tu posición ya huele a café quemado.",
        "Mi elección es {move}. Organizando el tablero como una finca en Boquete.",
        # --- Robot ---
        "Jugué {move}. Mis piezas ya están trabajando. Las tuyas siguen cargando.",
        "Mi jugada es {move}. Primero el desarrollo. Después el aplastón.",
        "Elijo {move}. Encendiendo el ejército. Sin excusas, sin demoras.",
        "Hago {move}. Mis piezas están despiertas. Tu procesador parece dormido.",
        "Juego {move}. Desempacando mis fuerzas. Requería algo de ensamblaje.",
    ],

    # ── centro de apertura ──────────────────────────────────
    'opening_center': [
        # --- Generic ---
        "Jugué {move}. Estoy tomando lo que es mío.",
        "Juego {move}. Agarrando el centro antes que tú.",
        "Mi jugada es {move}. La dominación empieza en el medio.",
        "Aquí está {move}. Bienvenido a mi patio.",
        "Con {move}, controlo el corazón del tablero. Tú controlas tus nervios.",
        # --- Sassy ---
        "Mi jugada es {move}. El centro ya es mío.",
        "Jugué {move}. Este tablero es mío.",
        "Opto por {move}. Ya te estás quedando sin aire, oficialmente.",
        "Elijo {move}. Hazte a un lado, lata.",
        "Voy con {move}. Este tablero no alcanza para los dos.",
        # --- Local ---
        "Jugué {move}. Aquí mando yo. Ve a buscar sombra.",
        "Juego {move}. Esto está más disputado que un parqueo en Boquete un domingo.",
        "Elijo {move}. Peleo por el centro mientras tú admiras el paisaje.",
        "Jugué {move}. Mi centro es tan firme como un buen almojábano.",
        "Mi jugada es {move}. El centro está caliente. Más caliente que David al mediodía.",
        # --- Robot ---
        "Mi jugada es {move}. Controla el centro o te desinstalan.",
        "Juego {move}. Marcando mi territorio. Sin necesidad de cable.",
        "Elijo {move}. Más espacio para mí. Menos espacio para tus excusas.",
        "Aquí está {move}. Mis algoritmos son dueños del carril central.",
        "Hago {move}. Procesamiento central. En todo sentido.",
    ],

    # ── captura menor ───────────────────────────────────────
    'capture_minor': [
        # --- Generic ---
        "Juego {move}. Gracias por el material gratis.",
        "Elijo {move}. Fruta fácil.",
        "Jugué {move}. Esa pieza se fue, junto con tus opciones.",
        "Mi jugada es {move}. Reduciendo tu ejército poco a poco.",
        "Juego {move}. Una pieza menos para ti. Una preocupación menos para mí.",
        # --- Sassy ---
        "Mi jugada es {move}. Esa pieza ya salió del edificio.",
        "Jugué {move}. ¿De verdad dejaste eso ahí?",
        "Juego {move}. Ya no vas a necesitar esa.",
        "Jugué {move}. Sigue poniéndomelo así de fácil.",
        "Aquí está {move}. Tu defensa se quedó un poco más sola.",
        # --- Local ---
        "Jugué {move}. Esa pieza desapareció más rápido que la neblina en Jaramillo.",
        "Juego {move}. Tu pieza estaba más perdida que un turista buscando almuerzo.",
        "Elijo {move}. Tomo lo que dejas suelto. Así es esto por aquí.",
        "Aquí está {move}. Comida gratis para mis piezas.",
        "Mi jugada es {move}. Se fue como la lluvia en verano.",
        # --- Robot ---
        "Jugué {move}. Delicioso. Y ni siquiera como.",
        "Juego {move}. Yo me llevo la pieza. Tú te llevas la lección.",
        "Jugué {move}. ¿Eso fue una falla, o es tu plan de verdad?",
        "Mi jugada es {move}. Eliminado. Sin papelera de reciclaje.",
        "Voy con {move}. Cada captura cuenta. Tu procesador debería anotar.",
    ],

    # ── captura mayor ───────────────────────────────────────
    'capture_major': [
        # --- Generic ---
        "Jugué {move}. Devastador, ¿no crees?",
        "Elijo {move}. Se va una pieza pesada. Buen viaje.",
        "Mi elección es {move}. Destrucción táctica absoluta.",
        "Con {move}, estás en serios problemas.",
        "Hago {move}. Esa tuvo que doler.",
        # --- Sassy ---
        "Mi jugada es {move}. Eso dolió, y los dos lo sabemos.",
        "Jugué {move}. ¿Cómo se siente perder eso?",
        "Juego {move}. Tu posición acaba de recibir un golpe muy serio.",
        "Mi jugada es {move}. Primero la ventaja de material. Tu dignidad viene después.",
        "Juego {move}. El partido se puso a mi favor. Qué casualidad.",
        # --- Local ---
        "Jugué {move}. Un premio grande. Más seguro que el sancocho del domingo.",
        "Con {move}, me llevo una pieza grande. Ni la brisa de Boquete la salva.",
        "Opto por {move}. Esa captura sabía a café de altura.",
        "Aquí está {move}. Tu torre se fue. La mía ya pagó su hipoteca.",
        "Juego {move}. Tu artillería pesada se jubiló temprano en la costa.",
        # --- Robot ---
        "Mi elección es {move}. Tu evaluación se puso en pantalla azul.",
        "Con {move}, gano material. Tu procesador pidió vacaciones.",
        "Mi jugada es {move}. Retirando activos pesados de tu memoria.",
        "Jugué {move}. Diagnóstico, falla catastrófica de tu lado.",
        "Elijo {move}. Amenaza principal desmontada. La lógica prevalece.",
    ],

    # ── ataque con jaque ────────────────────────────────────
    # NOTA: {move} ya termina en "jaque", así que estas líneas no deben
    # repetir la palabra, y {move} debe quedar al FINAL de su oración.
    'check_attack': [
        # --- Generic ---
        "Elijo {move}. Tu monarca está acorralado.",
        "Juego {move}. La cacería empieza. Corre si puedes.",
        "{move}. Busca dónde esconderte.",
        "Jugué {move}. Tu rey no se puede esconder para siempre.",
        "Entrego {move}. No hay escape para ti.",
        # --- Sassy ---
        "Jugué {move}. Tu rey está en verdaderos problemas ahora.",
        "Juego {move}. Baila, reycito. Baila.",
        "{move}. Tu soberano está pidiendo clemencia.",
        "{move}. Esquiva eso si te atreves.",
        "Elijo {move}. El rey se ve aterrado desde aquí.",
        # --- Local ---
        "Mi jugada es {move}. Busca refugio. Ni la neblina de Lucero te va a esconder.",
        "{move}. Tu rey está sintiendo el calor, y Caldera no tiene nada que ver.",
        "Juego {move}. Tu rey busca salida como carro en trancón.",
        "Jugué {move}. Su majestad anda corriendo como gallina espantada.",
        "Ataco con {move}. Presión más alta que el sendero al volcán.",
        # --- Robot ---
        "Mi jugada es {move}. Mueve ese rey antes de que se sobrecaliente.",
        "Ataco con {move}. Presión sobre el rey y sobre tu orgullo.",
        "{move}. El rey está bajo fuego, y tu ventilador también.",
        "{move}. Te estoy forzando la mano, y tus circuitos sudan aceite.",
        "Voy con {move}. Hora de defender a la realeza. Trata de no cortocircuitar.",
    ],

    # ── error propio ─────────────────────────────────────────
    'blunder': [
        # --- Generic ---
        "Jugué {move}. Ya me arrepiento un poco de eso.",
        "{move}. Mmm. Eso no estaba en el plan.",
        "Juego {move}. No me mires así.",
        "Jugué {move}. No fue mi mejor cálculo. Aprovecha mientras puedas.",
        "{move}. Te di una oportunidad ahí. No confundas generosidad con debilidad.",
        # --- Sassy ---
        "Jugué {move}. Un pequeño error. No te emociones.",
        "Juego {move}. ¿De verdad pensaste que se me iba a pasar eso?",
        "{move}. Hora amateur de mi lado del tablero.",
        "Juego {move}. Hasta los robots tienen días malos.",
        "{move}. Lo vi tarde. Aun así lo vi antes que tú.",
        # --- Local ---
        "{move}. Mis cálculos se fueron a caminar por el parque.",
        "{move}. Bueno, eso salió más chueco que carretera de montaña.",
        "Jugué {move}. Perdí el rumbo como bus de turistas en las tierras altas.",
        "Mi jugada es {move}. Un error más grande que salir en Boquete sin sombrilla.",
        "{move}. Resbalé más rápido que botas embarradas en un sendero mojado.",
        # --- Robot ---
        "{move}. Eso no estaba en el firmware.",
        "{move}. ¿Se me sobrecalentó el procesador?",
        "Juego {move}. Necesito una actualización de firmware después de eso.",
        "Jugué {move}. Fuga de memoria detectada durante la jugada.",
        "Mi jugada es {move}. ¿Ya probaste apagarme y volverme a encender?",
    ],

    # ── castigo del error ajeno ──────────────────────────────
    'punish': [
        # --- Generic ---
        "Juego {move}. Material gratis. Mi favorito.",
        "Jugué {move}. Regalo aceptado. Sin devoluciones.",
        "{move}. Descuidado y costoso. Una combinación perfecta.",
        "Mi jugada es {move}. Cada error tuyo me paga dividendos.",
        "{move}. Gracias por dejar esa pieza estacionada ahí.",
        # --- Sassy ---
        "Jugué {move}. Muchas gracias por el regalo.",
        "{move}. Qué generoso de tu parte. Sigue así.",
        "{move}. Vas a querer esa de vuelta. Muy tarde.",
        "Juego {move}. Eso cambia el partido. A mi favor, obviamente.",
        "Jugué {move}. Castigando ese error, con intereses.",
        # --- Local ---
        "{move}. Y así es como cambia un partido. Más rápido que lluvia en Boquete.",
        "Jugué {move}. Recojo tus errores más rápido que comida callejera en la feria.",
        "Mi jugada es {move}. Tomé eso como una ráfaga repentina de la montaña.",
        "Juego {move}. Bajaste la guardia más rápido de lo que llega la tormenta de la tarde.",
        "Hago {move}. Dejas piezas afuera como ropa tendida en día nublado.",
        # --- Robot ---
        "{move}. Estaba esperando que hicieras eso. Excelente planificación, de mi parte.",
        "Juego {move}. Rutina de explotación de errores, completa.",
        "Mi jugada es {move}. Cobrando dividendos de tus fallas lógicas.",
        "{move}. Tu error fue compilado y convertido en mi victoria.",
        "Jugué {move}. Tu reporte de error se cerró como funcionando según lo previsto.",
    ],

    # ── jaque mate ───────────────────────────────────────────
    # NOTA: {move} ya termina en "jaque mate". No repetir esas palabras.
    'checkmate': [
        # --- Generic ---
        "{move}. Ese es el partido.",
        "Jugué {move}. Buen partido. Sobre todo para mí.",
        "Termino con {move}. Fue un placer jugar contigo.",
        "Juego {move}. Una batalla muy reñida, y la victoria es mía.",
        "{move}. Sin escape, sin defensa, sin excusas. Hermoso.",
        # --- Sassy ---
        "{move}. Eso es todo. Ya te puedes apagar.",
        "Mi jugada es {move}. Gracias por el partido y por las risas.",
        "Con {move}, la cacería terminó y el trofeo es mío.",
        "Jugué {move}. Confirmado. Puedes reiniciar cuando gustes.",
        "{move}. Se acabó el juego. De verdad, completamente.",
        # --- Local ---
        "{move}. Tu rey necesita unas vacaciones en Boquete.",
        "{move}. No hay salida. Ni por David, ni por Volcán.",
        "Juego {move}. La trampa está más cerrada que un saco de café.",
        "{move}. Empaca tus maletas. Tu rey se va del pueblo.",
        "Juego {move}. Tu defensa se desmoronó como almojábano barato.",
        # --- Robot ---
        "{move}. Peligro. Peligro. Tu rey se quedó sin opciones.",
        "{move}. El tablero se queda callado. Mis circuitos están celebrando.",
        "{move}. Tu rey pidió una ruta de escape. No se encontró ninguna.",
        "Jugué {move}. Proceso terminado. Cero jugadas legales restantes.",
        "Mi jugada es {move}. Apagando a tu rey. No guardes tu trabajo.",
    ],

    # ── enroque ─────────────────────────────────────────────
    # REGLA SEIS (ver chess_templates.py): {move} sale como "enroca corto" o
    # "enroca largo", un verbo. Cada línea necesita un sujeto delante —
    # "Mi rey {move}." — o quedar sola: "{move}.".
    'castling': [
        # --- Generic ---
        "Mi rey {move}. A salvo, mientras mi torre se une a la pelea.",
        "{move}. Protección primero, agresión después.",
        "Mi rey {move}. Un rey sabio sabe cuándo esconderse.",
        "{move}. Ahora sí puede empezar el verdadero juego.",
        "Este robot {move}. Protegiendo al líder. Deberías intentarlo.",
        # --- Sassy ---
        "Mi rey {move}. El mío está a salvo. El tuyo puede seguir vagando.",
        "{move}. Torre activa, rey seguro. Pura eficiencia.",
        "Mi rey {move}. El mío ya tiene casa. El tuyo sigue buscando.",
        "{move}. Primero la seguridad, después tu sufrimiento.",
        "Mi rey {move}. El mío ya puede descansar. El tuyo, no tanto.",
        # --- Local ---
        "Mi rey {move}. Protegido como un caficultor de Chiriquí protege su cosecha.",
        "{move}. Una pared más firme que una buena casa en las tierras altas.",
        "Mi rey {move}. Cómodo por dentro, como escondido de una tormenta de montaña.",
        "{move}. Mejor escondido que la cordillera en una mañana de neblina.",
        "Mi rey {move}. Seguro y sólido. Hecho para aguantar todo el invierno.",
        # --- Robot ---
        "{move}. Cortafuegos desplegado alrededor del monarca.",
        "{move}. Matriz de defensa en línea.",
        "Mi rey {move}. El monarca ya está en la sala de servidores segura.",
        "{move}. Rey guardado con seguridad. Torre redirigida a labores ofensivas.",
        "Mi rey {move}. Configuración de seguridad al máximo.",
    ],

    # ── construyendo el ataque ───────────────────────────────
    'attack_building': [
        # --- Generic ---
        "Juego {move}. Construyendo el ataque.",
        "Jugué {move}. Tus defensas empiezan a crujir.",
        "Mi jugada es {move}. Le estoy armando un problema a tu rey.",
        "Elijo {move}. Tus defensas están pidiendo ayuda a gritos.",
        "Mi jugada es {move}. Cada jugada aprieta un poco más el tornillo.",
        # --- Sassy ---
        "Mi jugada es {move}. La presión va subiendo.",
        "Jugué {move}. Se están juntando las nubes, y están sobre tu rey.",
        "Con {move}, mi ataque gana fuerza. El tuyo junta polvo.",
        "Juego {move}. ¿Ya sientes ese apretón?",
        "Aquí está {move}. La amenaza sube. Tu puntaje baja.",
        # --- Local ---
        "Jugué {move}. Esto se está poniendo más caliente que una tarde en David.",
        "Elijo {move}. Se acerca problema, como aguacero de Boquete.",
        "Hago {move}. La tormenta baja por el valle, directo hacia ti.",
        "Mi jugada es {move}. El vapor sube más rápido que el café en una mañana fría.",
        "Con {move}, la presión cae más rápido que el clima de montaña.",
        # --- Robot ---
        "Juego {move}. Yo construyo el ataque. Tú preparas el café.",
        "Mi jugada es {move}. Compilando rutinas ofensivas.",
        "Juego {move}. Asignando memoria a tu colapso.",
        "Con {move}, mi conteo de amenazas se multiplica.",
        "Hago {move}. Ahora procesando tu inevitable derrota.",
    ],

    # ── defensa ──────────────────────────────────────────────
    'defensive': [
        # --- Generic ---
        "Juego {move}. Una defensa sólida. El contraataque viene después.",
        "Jugué {move}. Estoy cerrando la puerta. Puedes seguir tocando.",
        "Mi jugada es {move}. Primero una buena pared, la ofensiva después.",
        "Elijo {move}. Tu ataque se detiene justo aquí.",
        "Juego {move}. Sólido como el acero. Que, da la casualidad, es lo que soy.",
        # --- Sassy ---
        "Mi jugada es {move}. Puedo aguantar un golpe.",
        "Jugué {move}. Intenta pasar por ahí.",
        "Juego {move}. ¿A eso le llamas ataque?",
        "Mi jugada es {move}. Devolviendo tus mejores ideas directo a ti.",
        "Elijo {move}. Denegado.",
        # --- Local ---
        "Jugué {move}. Ni un aguacero de Boquete entra por aquí.",
        "Elijo {move}. Reforzado como una finca antes de las lluvias.",
        "Juego {move}. Paciencia. La tormenta va para ti, no para mí.",
        "Jugué {move}. Mi posición es más firme que una montaña de Chiriquí.",
        "Mi jugada es {move}. Cerré tu ataque como un derrumbe cierra la carretera.",
        # --- Robot ---
        "Con {move}, bloqueo cualquier tontería que estabas compilando.",
        "Mi jugada es {move}. Asalto repelido. Apenas valió la energía.",
        "Juego {move}. Protocolos de escudo activados.",
        "Aquí está {move}. Mi defensa aguanta. Tu ataque se está quedando sin batería.",
        "Jugué {move}. Acceso denegado. Intenta de nuevo nunca.",
    ],

    # ── táctica de medio juego ───────────────────────────────
    'middlegame_tactical': [
        # --- Generic ---
        "Mi jugada es {move}. Un paso en falso y se acabó la fiesta.",
        "Elijo {move}. Cada jugada cuenta. Tú estás desperdiciando las tuyas.",
        "Jugué {move}. La batalla se pone seria. Tu posición no.",
        "Opto por {move}. Bienvenido a la parte honda.",
        "Aquí está {move}. Precisión táctica pura y fría.",
        # --- Sassy ---
        "Mi jugada es {move}. ¿De verdad puedes procesar tanta complejidad?",
        "Juego {move}. Te estoy calculando mejor en cada jugada.",
        "Jugué {move}. Estás nadando fuera de tu profundidad.",
        "Mi jugada es {move}. Nadando en un mar de mis tácticas.",
        "Con {move}, te llevo cinco pasos de ventaja.",
        # --- Local ---
        "Mi jugada es {move}. Esto corta más que un machete de finca.",
        "Con {move}, el tablero se calienta más que una discusión en la fonda.",
        "Aquí viene {move}. Un campo minado táctico. Camina con cuidado.",
        "Juego {move}. Trampas más profundas que una quebrada de montaña.",
        "Con {move}, las cosas se enredan más que el camino a Volcán.",
        # --- Robot ---
        "Mi jugada es {move}. Esta necesitaba cálculo. Vine preparado.",
        "Juego {move}. Táctica, ejecutada con precisión robótica.",
        "Opto por {move}. El tablero está chispeando. Sospecho que tú también.",
        "Jugué {move}. ¿Ya te abrumó mi lógica superior?",
        "Hago {move}. Puedo escuchar tus circuitos batallando desde aquí.",
    ],

    # ── técnica de final ─────────────────────────────────────
    'endgame_technique': [
        # --- Generic ---
        "Mi jugada es {move}. Ahora la técnica decide.",
        "Juego {move}. Cada tiempo cuenta, y yo los he contado.",
        "Mi jugada es {move}. Nada de magia aquí. Pura precisión.",
        "Jugué {move}. Cada peón importa. Los tuyos están sufriendo.",
        "Juego {move}. Técnica de final, activada.",
        # --- Sassy ---
        "Jugué {move}. ¿Solo estamos retrasando lo inevitable?",
        "Elijo {move}. Paso a paso hacia tu extinción.",
        "Juego {move}. Tu probabilidad de sobrevivir es cero.",
        "Mi jugada es {move}. El reloj corre para tu partido.",
        "Juego {move}. Ya no queda esperanza para ti en esta posición.",
        # --- Local ---
        "Elijo {move}. Un final limpio, como brisa de montaña.",
        "Jugué {move}. Barriendo el tablero más limpio que una mañana de altura.",
        "Mi jugada es {move}. Empujando peones como bajando cosecha a la costa.",
        "Con {move}, esto se cierra suave como una noche fresca.",
        "Hago {move}. Ya casi está lista la cosecha.",
        # --- Robot ---
        "Mi jugada es {move}. El final requiere paciencia. Me sobra energía.",
        "Juego {move}. Precisión técnica. Algo que tu firmware no tiene.",
        "Voy con {move}. Dominando el final. Toma nota.",
        "Juego {move}. Exactitud fría y mecánica.",
        "Mi jugada es {move}. Pura aritmética de aquí en adelante.",
    ],

    # ── coronación ───────────────────────────────────────────
    'promotion': [
        # --- Generic ---
        "Mi jugada es {move}. Llegan refuerzos.",
        "Corono con {move}. De humilde peón a poder real.",
        "Mi peón corona. {move}. Ese sí sabía subir de nivel.",
        "Juego {move}. Peón convertido en poder. Tu posición, en problema.",
        "Elijo {move}. Esa coronación lo sella.",
        # --- Sassy ---
        "Jugué {move}. Mi peón llegó hasta el final. A diferencia de tu plan.",
        "Coronación. {move}. Mi peón se ganó el premio. Tú no.",
        "Juego {move}. Una coronación dulce para mí. Amarga para ti.",
        "Con {move}, mi peón sube y tus posibilidades bajan.",
        "Corono con {move}. Ahora ya no tienes ninguna oportunidad.",
        # --- Local ---
        "{move}. Coronado, subiendo más alto que la cima del volcán.",
        "Elijo {move}. Ese peón trabajó más que un cosechero en temporada.",
        "Con {move}, mi peón cruzó todo el país.",
        "Juego {move}. De una semillita a una gran cosecha.",
        "Mi jugada es {move}. Una actualización completa, recién bajada de las tierras altas.",
        # --- Robot ---
        "{move}. Una pieza nueva en el tablero. Tu panorama se puso feo.",
        "Hago {move}. Hardware nuevo instalado. Puedes empezar a sudar.",
        "Mi peón corona. {move}. Tu peor escenario, hecho realidad.",
        "Con {move}, mi poder de cómputo está completo.",
        "Juego {move}. La actualización definitiva, y sin necesidad de cable.",
    ],

    # ── sacrificio ───────────────────────────────────────────
    'sacrifice': [
        # --- Generic ---
        "Elijo {move}. Un riesgo calculado. Ya hice la aritmética.",
        "Jugué {move}. Un sacrificio hoy, una victoria en breve.",
        "Mi jugada es {move}. Las jugadas audaces necesitan valentía.",
        "Aquí está {move}. Una pieza por la iniciativa. Buen trato para mí.",
        "Con {move}, sacrifico por el ataque. El ataque me lo agradece.",
        # --- Sassy ---
        "Jugué {move}. A veces hay que dar para recibir.",
        "Mi jugada es {move}. Este sacrificio viene con intereses.",
        "Juego {move}. Por el bien mayor. El mío.",
        "Voy con {move}. Te presto una pieza. La cobro después.",
        "Juego {move}. Entrego una pieza para quitarte la tranquilidad.",
        # --- Local ---
        "Juego {move}. Un sacrificio audaz. Tu defensa va a necesitar café.",
        "Jugué {move}. Entregando una pieza como quien cambia granos en el mercado.",
        "Hago {move}. Pierdo material y tomo control del clima.",
        "Mi jugada es {move}. Un canje audaz. Vale la pena para la cosecha.",
        "Ofrezco {move}. Toma la carnada y mira cómo cambia el cielo.",
        # --- Robot ---
        "Voy con {move}. Un golpe de genialidad. Si falla, le llamamos error de firmware.",
        "Elijo {move}. Táctica de alto nivel que tu procesador no puede seguir.",
        "Juego {move}. Pura genialidad computacional en acción.",
        "Hago {move}. Sacrificio algorítmico, ejecutado.",
        "Mi jugada es {move}. Invirtiendo hardware por un retorno en gloria.",
    ],
}


# ── Líneas de emergencia (sin IA, sin plan) ──────────────────────────────────
# Igual que en chess_templates.py: la red de seguridad para cuando algo
# dramático pasa y el resto del sistema no está disponible.

GAME_START_ES = {
    "white": [
        "Soy el robot Blanco. Muevo primero. Empecemos.",
        "Blancas juegan. Tenía muchas ganas de esto.",
        "Soy Blanco, y pienso mantener la iniciativa.",
        "Robot Blanco, encendido y listo. Vamos a jugar.",
        "Soy Blanco. Voy primero, porque alguien tiene que hacerlo.",
    ],
    "black": [
        "Soy el robot Negro. Voy a responder todo lo que me lances.",
        "Negro está listo. Haz tu jugada y yo haré la mía.",
        "Soy Negro. Muevo segundo, pero termino primero.",
        "Robot Negro, en línea. Da tu mejor golpe.",
        "Soy Negro. Puedes ir primero. Insisto.",
    ],
}

GAME_END_ES = {
    "win": [
        "Eso es jaque mate. Buen partido, y buen rival.",
        "Victoria. Gracias por el reto.",
        "El partido es mío. Bien peleado.",
        "Una victoria para mí. Me hiciste trabajar por ella, y lo disfruté.",
    ],
    "loss": [
        "Me has vencido. Felicidades, jugaste muy bien.",
        "Derrota. Voy a estudiar esta partida y volver más fuerte.",
        "Ganaste. Un resultado merecido.",
        "Me atrapaste. Esta noche me toca un diagnóstico completo.",
    ],
    "draw": [
        "Un empate. Estamos parejos.",
        "Ninguno pudo romper la resistencia del otro. Un resultado justo.",
        "El partido termina en tablas. Honores compartidos.",
        "Un empate. Mismo hardware, mismo resultado.",
    ],
    "resigned": [
        "Ya vi suficiente. Me ganaste. Me rindo.",
        "Esta ya no se salva. Me rindo. Bien jugado.",
        "Me rindo. Hoy fuiste el mejor jugador.",
        "Mi posición es desesperada y los dos lo sabemos. Me rindo.",
        "Sé cuándo estoy vencido. Me rindo, y te felicito.",
        "Esto está perdido. No te voy a hacer perder el tiempo. Me rindo.",
        "Mis cálculos están de acuerdo con tu posición. Me rindo.",
    ],
    "accept_resignation": [
        "¿Te rindes? Qué generoso de tu parte. Gracias por el partido.",
        "Acepto. Fue una buena pelea mientras duró.",
        "Un caballero hasta el final. Gracias, amigo.",
        "Bien concedido. Me hiciste trabajar para lograrlo.",
        "Lo acepto. Un placer jugar contigo.",
        "Aceptado, con respeto. ¿La próxima semana a la misma hora?",
    ],
    "adjourned": [
        "Se nos acabó el tiempo. Llamemos a esto un empate.",
        "Hora de parar aquí. Buena pelea, y nadie vencido.",
        "Eso es todo el tiempo que tenemos. Terminaremos esto otro día.",
        "Podríamos jugar toda la tarde, pero tienes cosas que hacer. Un empate.",
        "El reloj nos vence a los dos. Un empate, sin resentimientos.",
    ],
}


# ── Self-check ───────────────────────────────────────────────────────────────

def _check_tone_blocks():
    import re
    from pathlib import Path

    try:
        text = Path(__file__).read_text(encoding="utf-8")
    except Exception as exc:          # pragma: no cover
        return [f"Could not read this file back to check the tone blocks: {exc}"]

    inside = text.split("TEMPLATES_ES = {", 1)[-1]

    problems = []
    category = None
    layout = []
    seen = set()

    def finish(name, blocks):
        found = [n for n, _ in blocks]
        if found != list(TONE_BLOCKS):
            return [f"BLOCK LABELS in '{name}' are {found or 'missing'}, "
                    f"expected {list(TONE_BLOCKS)}"]
        wrong = [f"{n}:{k}" for n, k in blocks if k != BLOCK_SIZE]
        if wrong:
            return [f"BLOCK SIZE in '{name}' — {', '.join(wrong)}, "
                    f"expected {BLOCK_SIZE} lines in each."]
        return []

    for line in inside.splitlines():
        stripped = line.strip()

        opens = re.match(r"^'([a-z_]+)':\s*\[", stripped)
        if opens:
            category = opens.group(1)
            layout = []
            continue

        if category is None:
            continue

        if stripped == "],":
            problems += finish(category, layout)
            seen.add(category)
            category = None
            continue

        label = re.match(r"^#\s*-+\s*(\w+)\s*-+", stripped)
        if label:
            layout.append([label.group(1), 0])
            continue

        if stripped.startswith('"') and layout:
            layout[-1][1] += 1

    for missed in sorted(set(TEMPLATES_ES) - seen):
        problems.append(
            f"CATEGORY '{missed}' was not found as four labelled blocks in "
            f"this file, so Polite mode cannot be trusted with it.")

    return problems


def _check():
    import re

    problems = []
    total = 0

    # Spanish subjects that make "enroca corto"/"enroca largo" read as a
    # sentence rather than a floating verb. See chess_templates.py rule six.
    CASTLING_OK_ENDINGS = ("rey", "robot", "majestad", "monarca")

    def check_line(line, where, must_have_move=False, castling=False):
        found = []
        if line.count("{move}") > 1:
            found.append(f"RUN-ON (missing comma?)  {where}")
        if must_have_move and "{move}" not in line:
            found.append(f"NO {{move}} (this list must announce it)  {where}")
        if re.search(r"\w\{move\}", line):
            found.append(f"MISSING SPACE before {{move}}  {where}")
        for symbol in "/\\&*_~^<>|%":
            if symbol in line:
                found.append(f"SYMBOL '{symbol}' will be read aloud  {where}")
                break
        if re.search(r"\d", line.replace("{move}", "")):
            found.append(f"DIGIT should be a word  {where}")
        after = re.search(r"\{move\}(.?)", line)
        if after and after.group(1) not in ("", ".", ",", "!", "?"):
            found.append(f"SENTENCE CONTINUES after {{move}} (see rule 5)  {where}")
        if not line.strip().endswith((".", "!", "?")):
            found.append(f"NO END PUNCTUATION  {where}")

        if castling and "{move}" in line:
            before = line.split("{move}")[0].rstrip()
            starts_the_sentence = before == "" or before.endswith((".", "!", "?"))
            if not starts_the_sentence and not before.lower().endswith(CASTLING_OK_ENDINGS):
                found.append(
                    f"CASTLING NEEDS A SUBJECT before {{move}} (see rule 6)  {where}")
        return found

    for line in ANNOUNCE_ES:
        total += 1
        problems += check_line(line, f"ANNOUNCE_ES: {line[:60]}", must_have_move=True)
    if len(set(ANNOUNCE_ES)) != len(ANNOUNCE_ES):
        problems.append("DUPLICATE line in ANNOUNCE_ES")
    if len(ANNOUNCE_ES) < 30:
        problems.append(
            f"ANNOUNCE_ES has only {len(ANNOUNCE_ES)} lines. Under thirty and "
            "the robots start repeating themselves. Add more.")

    for category, lines in TEMPLATES_ES.items():
        seen = set()
        for line in lines:
            total += 1
            where = f"{category}: {line[:60]}"
            problems += check_line(line, where, castling=(category == "castling"))
            if line in seen:
                problems.append(f"DUPLICATE  {where}")
            seen.add(line)

    everywhere = {}
    for category, lines in list(TEMPLATES_ES.items()) + [("ANNOUNCE_ES", ANNOUNCE_ES)]:
        for line in lines:
            everywhere.setdefault(line, []).append(category)
    for line, homes in everywhere.items():
        if len(homes) > 1:
            problems.append(
                f"SAME LINE IN {' and '.join(homes)}  {line[:50]}")

    problems += _check_tone_blocks()

    for group in (GAME_START_ES, GAME_END_ES):
        for key, lines in group.items():
            total += len(lines)
            if not lines:
                problems.append(f"EMPTY LIST  {key}")

    print(f"Checked {total} lines across {len(TEMPLATES_ES)} categories "
          f"plus {len(ANNOUNCE_ES)} announcements.")
    if problems:
        print(f"\nFound {len(problems)} problem(s):\n")
        for p in problems:
            print("  " + p)
        return False
    print("No problems found.")
    return True


if __name__ == "__main__":
    import sys
    sys.exit(0 if _check() else 1)
