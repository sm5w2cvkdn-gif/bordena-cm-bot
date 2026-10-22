# Bot Community Manager · Bordena Studio

Bot que diseña y publica una historia de Instagram por día con el estilo de Bordena Studio
(azul marino y crema, Cinzel + Roboto, arco y ola griega).

## Cómo funciona

| Hora (Buenos Aires) | Qué pasa |
|---|---|
| 08:30 | Una rutina de Claude en la nube diseña la historia del día y abre un *pull request* con la imagen. |
| antes de las 10:00 | Vos la mirás desde el celular (app de GitHub o mail) y hacés **merge** para aprobarla, o cerrás el PR si no te gusta. |
| 10:00 | Otra rutina publica la historia en Instagram vía Windsor.ai, **solo si la aprobaste**. |

## Qué podés editar

| Archivo | Para qué |
|---|---|
| `CALENDARIO.md` | Tema de cada día de la semana y fechas especiales. |
| `SERVICIOS.md` | Servicios, horarios y datos que el bot puede mencionar. El bot no inventa nada que no esté acá. |
| `PROMOS.md` | Promos y avisos con fecha de inicio y fin (feriados, horarios especiales). |
| `MARCA.md` | Estilo visual, tono de voz y reglas de la marca. |
| `fotos/` | Fotos que el bot puede usar en los diseños `foto` y `ventana`. |
| `marca/` | Logo en PNG (`logo-navy.png` y `logo-blanco.png`). |

## Diseños

| Diseño | Cómo es | Ideal para |
|---|---|---|
| `foto` | Foto con velo azul, título grande a la izquierda, caja con borde fino. | Saludos, horarios, feriados. |
| `marco` | Crema con marco azul fino, centrado, tarjeta azul opcional. | Gift cards, servicio destacado, promos. |
| `lista` | Blanco, opciones numeradas con líneas. | Combos, opciones, pasos. |
| `arco` | Arco mediterráneo con ola griega. | Mantenimiento, frases, recordatorios. |
| `navy` | Azul marino entero con ola griega arriba y abajo. | Agenda, anuncios. |
| `ventana` | Foto (u ola griega) dentro de un arco, texto abajo. | Tips, ambiente, trabajos. |

Ejemplos en `muestras/`.

## Formato del JSON

```json
{
  "diseno": "marco",
  "foto": "fotos/archivo.jpg",
  "etiqueta": "Faltan pocos días",
  "titulo": "Día de la Madre",
  "texto": "Llevate tu gift card **hoy mismo** para el tratamiento que elijas.",
  "texto_secundario": "Y te asesoramos para que el regalo sea perfecto.",
  "caja": {"etiqueta": "Bordena Studio", "titulo": "Gift card", "texto": "opcional"},
  "items": [{"etiqueta": "Opción 1", "titulo": "Beauty Reset", "texto": "Uñas + facial + cejas."}],
  "cierre": "Consultanos por tu gift card."
}
```

- `foto`: solo para `foto` y `ventana` (opcional; sin foto usan fondo azul / ola griega).
- `caja`: en `foto` y `navy` es un recuadro con borde; en `marco` es la tarjeta azul; en `arco` es un dato destacado.
- `items` y `cierre`: solo para `lista` (máximo 4 ítems).
- `texto_secundario`: no se usa en `foto` ni en `lista`.
- `**negrita**` funciona en `texto`, `texto_secundario`, `caja.texto` e `items[].texto`.

## Probar en tu compu

```bash
pip install -r requirements.txt
python render.py muestras/2-marco.json /tmp/prueba.jpg
```

Tipografías: Cinzel y Roboto (Google Fonts, licencia OFL, en `fuentes/`).
