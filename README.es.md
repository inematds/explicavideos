# Explicavideos

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

Proceso reproducible para videos explicativos con avatar y voz de Nei, ilustraciones, capítulos y subtítulos. Derivado de las producciones completadas de Astra Básico y OSWork Quick.

[Guía de uso](https://inematds.github.io/explicavideos/guia/es/) · [Fuente OSWork](https://inematds.github.io/oswork/)

## Flujo real

Fuente → escenas con cobertura → bloques de hasta 4.400 caracteres → HeyGen Studio con la suscripción → descarga → transcripción de Groq con tiempos por palabra → composición HyperFrames → validación → renderizado → concatenación → GitHub Release y reproductor → bot v3.

El adaptador OSWork cubre los 48 temas, todos los campos explicativos, ocho laboratorios y revisiones en 122 escenas. Primera producción: portugués. El motor admite PT/ES/EN; para otros idiomas se necesitan archivos de escenas revisados, no se traducen automáticamente.

## Operación

Requiere Python 3 con requests y beautifulsoup4, Node, FFmpeg, gh autenticado, systemd de usuario, Xvfb y el perfil de HeyGen autenticado. El adaptador del navegador usa Playwright instalado en inemaccbot. Esta versión se puede ejecutar en el entorno INEMA; ajuste las rutas para otra máquina. No es un servicio público.

```bash
python3 explica.py --config examples/oswork.json prepare
python3 explica.py --config examples/oswork.json preview
python3 engine/check_layouts.py
python3 explica.py --config examples/oswork.json start
python3 explica.py --config examples/oswork.json status
journalctl --user -u explica-oswork-completo-submit -n 20 --no-pager
```

`prepare` no sobrescribe producciones ya iniciadas. `start` inicia cinco servicios persistentes; no interrumpe los que ya están activos. No reinicie un envío `needs_review`: primero compruebe si existe un ID en HeyGen. La producción en curso ya está preparada; use `status`, no `prepare`.

## Formato v2: animación explicativa (2.0.0)

> 2.2.3: Whisper local — los fragmentos omitidos (huecos > 3 s entre palabras) se vuelven a transcribir por separado, con hasta 3 inicios; la comprobación de alineación (v1 y v2) considera acertado el número hablado en dígitos ("83%") frente al guion escrito con todas las letras. LOOP-R PT: 10 bloques reprobados entre 0,79 y 0,88 pasaron a 0,97–0,99.
>
> 2.2.2: los servicios (`start`) se ejecutan dentro de `explica.slice` (`~/.config/systemd/user/explica.slice`: MemoryMax=40G, sin swap). Si el lote de renders excede el límite, el kernel termina un render, no las terminales de la sesión (incidente de 2026-09-27 04:01).
>
> 2.2.1: `"transcriber": "whisper-local"` en la configuración reemplaza Groq por Whisper large-v3 local (un proceso a la vez, bloqueo en /tmp; `whisper_prompt` para nombres propios) y `"balanced_blocks": true` equilibra los bloques para que no quede un último bloque corto (< 60 s). Sin estas claves, el comportamiento es el anterior. Primer uso: LOOP-R (`examples/loop-r-*.json`).
>
> 2.1.1: v2 en PT/EN/ES (etiquetas fijas y `lang` por idioma; `setup_output` acepta v1 en cualquier idioma) y regla de autoría "ningún cuadro vacío durante más de 3 s".
>
> 2.0.1: el plano anterior permanece en pantalla hasta que el siguiente muestra contenido (las etiquetas no cuentan) y el título grande de la escena espera al primer contenido — el escenario vacío medido bajó de 26% a 17% en OSWork v6.2 M1; lo que queda son cuadros con poco contenido, que deben resolverse en el guion visual.

En v2, el elemento visual explica lo que se está diciendo en el momento en que se dice. Cada escena recibe un guion visual (`<output>/visual-v2/pt-bNN.json`), con planos de 21 primitivas animadas en `engine/v2/runtime/v2.js`. Todos los tiempos son **señales habladas**, resueltas mediante la transcripción real. El subtítulo usa la grafía del guion, y se reutilizan el avatar y el audio de la producción v1, sin una nueva generación en HeyGen. Reglas y catálogo: [engine/v2/AUTHORING.md](engine/v2/AUTHORING.md). Ejemplo aprobado: `visual-v2/pt-b01.json` de OSWork.

```bash
export EXPLICAVIDEOS_CONFIG=examples/oswork-v2.json
python3 engine/v2/setup_output.py            # nuevo directorio de salida; v1 no se toca
python3 engine/v2/build_block.py 1 --strict   # señales → tiempos, 0 advertencias, se notifican los huecos > 10 s
engine/v2/run_lane.sh 1 2 3                   # hyperframes check + render verificado por bloque; sale ≠0 si algún bloque falla (2.4.5)
python3 engine/assemble_languages.py && python3 engine/publish_finished.py
```

El motor v1 (`explica.py`, `engine/*.py`) sigue igual y disponible. La versión anterior del video OSWork está en el release `video-v1.0.0`.

## Configuración para otros videos

Copie examples/oswork.json y cambie id, title, source_repo, output, github_repo y release_tag. Para contenido que no sea de OSWork, proporcione `scene_files` con rutas por idioma, por ejemplo `{"pt":"/caminho/lesson-pt.json"}`. Cada escena contiene title, chapter, speech, labels, source, kind y takeaway; svg es opcional. El guion debe revisarse antes de `start`.

Los medios y estados se guardan en `~/projetos/output/<id>/`. El repositorio contiene el motor, las configuraciones, la documentación y los recursos visuales; no contiene credenciales ni archivos MP4.

## Calidad y recuperación

- Fuente congelada en JSON, cobertura por tema y SHA-256 de cada bloque.
- Nunca repetir automáticamente un envío con resultado ambiguo.
- Avatar: plantilla TEMPLATE-AVATAR16, Nei, voz INEMATIME, Avatar III.
- Transcripción real; correspondencia de palabras superior al 90% para renderizar/publicar.
- Composición 1920×1080, 25 fps; subtítulos sin superposición.
- Verificación de HyperFrames, duración real, presencia de audio y decodificación con FFmpeg.
- MP4 y SRT en Release; reproductor con capítulos y VTT en el curso.
- Aviso final en el bot v3 solo después de la publicación y el recibo del portal.

`verification/production.json` registra fallas por bloque. Corrija la causa y elimine solo el estado de ese bloque para reanudarlo, conservando su ID de HeyGen. Los servicios tienen una ventana de 12 horas; haga seguimiento con status y journalctl. No hay reintentos a ciegas de generación.

## Costos

La generación del avatar usa la sesión de la suscripción a HeyGen en el navegador. La API de HeyGen se usa solo para consultas; Groq cobra la transcripción según la cuenta. HyperFrames renderiza localmente. El motor no llama a un LLM para coordinar cada etapa. Tener una suscripción no significa tener uso ilimitado; este proyecto registra la duración y los ID, pero no calcula la factura de los proveedores.

## HeyGen: cómo el motor genera, verifica y descarga (opciones)

**Modelo actual — el predeterminado, en producción. Sin cambios.** La generación se hace con un script Playwright en el **estudio** de HeyGen (`engine/heygen-studio.mjs`: clona `TEMPLATE-AVATAR16`, cambia título y guion, "Generar" → modal → "Enviar"), con cargo a la suscripción mediante el perfil de navegador con sesión en la pantalla `:99`. Verificar la cola (`submit.py`), seguir el progreso (`monitor.py`, cada 60 s) y descargar el MP4 usan llamadas **de solo lectura** a `GET /v3/videos/<id>` en la **API** de HeyGen.

**Opción en estudio — estudio de punta a punta (AÚN NO implementada).** La misma ruta `| estudio` del [promoavatar3](https://github.com/inematds/promoavatar3), llevada hasta el final: verificar el estado y descargar también por el estudio, por el título exacto, sin clave de API. Gana: ninguna API; ve el estado real (Draft, en cola, procesando, listo, falló). Pierde: depende de la sesión del perfil y del diseño de HeyGen; cada verificación abre el navegador (segundos, cada 5–10 min); envío y verificación comparten la pantalla `:99`, uno a la vez.

**Por qué — el caso del 29/09/2026.** Tres bloques de OSWork v6.2 quedaron 4 días como `pending` en la API. En el estudio los tres estaban en **Draft**: el clic final del modal no se registró, el script guardó el ID de todos modos y la API informa un borrador como `pending`. No se generó ni se cobró nada.

**Protección mínima para ambos modelos (pendiente):** tras "Enviar", confirmar en Proyectos que el título salió de **Draft**; si no, marcar `needs_review`. Desbloquear un borrador es generar video: solo con autorización explícita. Nunca reenviar sin mirar antes el estudio.

## Referencias y licencias

Pipeline adaptado de astrabasico y oswork-quick. Fuentes locales de diseño: Montserrat y DejaVu; animación GSAP. El contenido educativo y los diagramas pertenecen al curso fuente. Conserve las licencias de los recursos al redistribuirlos.

## Verificación

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q engine
```


## Entrega OSWork

[Ver el video completo](https://inematds.github.io/oswork/videos/). Recibo de publicación en docs/video-publication.json.
