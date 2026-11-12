<script>
  // The one reusable map. The parent supplies a value per station, a mode and a zoom level.
  // D3 handles the projection, scales and nearest-station lookup. A small animation loop eases
  // every circle toward its target size and colour, and eases the camera between views.
  // Everything is drawn in real pixels, so dots and labels keep their size when zoomed.
  import { geoMercator, geoPath } from 'd3-geo'
  import { scaleSqrt } from 'd3-scale'
  import { Delaunay } from 'd3-delaunay'

  let {
    data,
    values,
    mode = 'dep', // 'dep' (trips starting) | 'net' (arrivals minus departures)
    maxValue,
    radiusMax = null, // largest dot in px; defaults to a size that suits the container
    zoom = 'core', // 'core' (central city) | 'city' (every station)
    highlight = null, // Uint8Array flags; non-highlighted stations fade back
    annotations = [],
    label = '',
    describe = () => null,
    reduceMotion = false,
  } = $props()

  const { stations, geo, methods } = data
  const n = stations.length

  // World coordinates: the whole city projected to about 1000 units wide.
  const everything = { type: 'MultiPoint', coordinates: stations.map((s) => [s.lng, s.lat]) }
  const projection = geoMercator().fitWidth(1000, everything)
  const path = geoPath(projection)
  const areaPaths = geo.features.map((f) => path(f))
  const pos = stations.map((s) => projection([s.lng, s.lat]))
  const delaunay = Delaunay.from(pos)

  // Each view is a rectangle in world units: [latMin, latMax, lngMin, lngMax] on the map.
  const rect = ([latMin, latMax, lngMin, lngMax]) => {
    const [x0, y0] = projection([lngMin, latMax])
    const [x1, y1] = projection([lngMax, latMin])
    return { x0, y0, x1, y1 }
  }
  const lats = stations.map((s) => s.lat)
  const lngs = stations.map((s) => s.lng)
  const views = {
    city: rect([Math.min(...lats), Math.max(...lats), Math.min(...lngs), Math.max(...lngs)]),
    core: rect(methods.view.core.bbox),
  }

  const COLORS = {
    dep: [204, 84, 152],
    depHot: [118, 18, 86],
    gain: [11, 79, 122],
    loss: [216, 80, 42],
  }

  let w = $state(0)
  let h = $state(0)
  const maxRadius = $derived(radiusMax ?? Math.max(8, Math.min(17, Math.min(w, h) * 0.03)))
  const rScale = $derived(scaleSqrt().domain([0, maxValue || 1]).range([0, maxRadius]).clamp(true))

  // Drawn and target state: circles (radius in px, alpha, rgb) and the camera.
  const cur = { r: new Float32Array(n), a: new Float32Array(n), c: new Float32Array(n * 3) }
  const tgt = { r: new Float32Array(n), a: new Float32Array(n), c: new Float32Array(n * 3) }
  const cam = { logk: 0, cx: 500, cy: 500 }
  const camTarget = { logk: 0, cx: 500, cy: 500 }
  let camReady = false
  let circlesReady = false
  let tick = $state(0)
  let raf = 0
  let last = 0

  function setCircleTargets() {
    for (let i = 0; i < n; i++) {
      const v = values[i] || 0
      let color, radius, alpha
      if (mode === 'net') {
        color = v >= 0 ? COLORS.gain : COLORS.loss
        radius = Math.max(0.9, rScale(Math.abs(v)))
        alpha = 0.85
      } else {
        const intensity = Math.sqrt(Math.min(1, Math.max(0, v) / (maxValue || 1)))
        color = [
          COLORS.dep[0] + (COLORS.depHot[0] - COLORS.dep[0]) * intensity,
          COLORS.dep[1] + (COLORS.depHot[1] - COLORS.dep[1]) * intensity,
          COLORS.dep[2] + (COLORS.depHot[2] - COLORS.dep[2]) * intensity,
        ]
        radius = Math.max(0.9, rScale(Math.max(0, v)))
        alpha = 0.5 + 0.42 * intensity
      }
      if (highlight && !highlight[i]) {
        alpha *= 0.22
        radius *= 0.6
      }
      tgt.r[i] = radius
      tgt.a[i] = alpha
      tgt.c[i * 3] = color[0]
      tgt.c[i * 3 + 1] = color[1]
      tgt.c[i * 3 + 2] = color[2]
    }
    if (!circlesReady) {
      circlesReady = true
      cur.c.set(tgt.c)
      cur.a.set(tgt.a)
    }
  }

  function setCameraTarget() {
    const v = views[zoom]
    const pad = Math.min(w, h) * 0.04 + 8
    const k = Math.min((w - 2 * pad) / (v.x1 - v.x0), (h - 2 * pad) / (v.y1 - v.y0))
    camTarget.logk = Math.log(k)
    camTarget.cx = (v.x0 + v.x1) / 2
    camTarget.cy = (v.y0 + v.y1) / 2
    if (!camReady || reduceMotion) {
      camReady = true
      Object.assign(cam, camTarget)
    }
  }

  function frame(now) {
    const dt = Math.min(64, Math.max(0, now - last))
    last = now
    const k = reduceMotion ? 1 : 1 - Math.exp(-dt / 110)
    const kc = reduceMotion ? 1 : 1 - Math.exp(-dt / 320)
    let moving = false

    for (let i = 0; i < n; i++) {
      const dr = tgt.r[i] - cur.r[i]
      const da = tgt.a[i] - cur.a[i]
      cur.r[i] += dr * k
      cur.a[i] += da * k
      let dc = 0
      for (let j = 0; j < 3; j++) {
        const d = tgt.c[i * 3 + j] - cur.c[i * 3 + j]
        cur.c[i * 3 + j] += d * k
        dc = Math.max(dc, Math.abs(d))
      }
      if (Math.abs(dr) > 0.02 || Math.abs(da) > 0.004 || dc > 1) moving = true
    }

    const dl = camTarget.logk - cam.logk
    const dx = camTarget.cx - cam.cx
    const dy = camTarget.cy - cam.cy
    cam.logk += dl * kc
    cam.cx += dx * kc
    cam.cy += dy * kc
    if (Math.abs(dl) > 0.0008 || Math.abs(dx) > 0.05 || Math.abs(dy) > 0.05) moving = true

    tick++
    if (moving) {
      raf = requestAnimationFrame(frame)
    } else {
      cur.r.set(tgt.r)
      cur.a.set(tgt.a)
      cur.c.set(tgt.c)
      Object.assign(cam, camTarget)
      tick++
      raf = 0
    }
  }

  const start = () => {
    if (!raf) {
      last = performance.now()
      raf = requestAnimationFrame(frame)
    }
  }

  $effect(() => {
    values
    mode
    maxValue
    highlight
    maxRadius
    setCircleTargets()
    start()
  })

  $effect(() => {
    if (!w || !h) return
    zoom
    setCameraTarget()
    start()
  })

  $effect(() => () => cancelAnimationFrame(raf))

  // Reading `tick` inside these makes the template redraw each animation frame.
  const scaleNow = (_t) => Math.exp(cam.logk)
  const shiftX = (_t) => w / 2 - scaleNow(_t) * cam.cx
  const shiftY = (_t) => h / 2 - scaleNow(_t) * cam.cy
  const worldTransform = (_t) => `translate(${shiftX(_t)} ${shiftY(_t)}) scale(${scaleNow(_t)})`
  const radius = (i, _t) => cur.r[i] / scaleNow(_t)
  const fill = (i, _t) =>
    `rgba(${cur.c[i * 3] | 0},${cur.c[i * 3 + 1] | 0},${cur.c[i * 3 + 2] | 0},${cur.a[i].toFixed(3)})`
  // A thin paper-colored outline separates overlapping dots; tiny dots go without one.
  const outline = (i, _t) => (cur.r[i] > 2.5 ? 0.8 : 0)

  // Screen position of a lng/lat point, for labels drawn on top of the map.
  const screen = (lng, lat, _t) => {
    const [x, y] = projection([lng, lat])
    const k = scaleNow(_t)
    return { x: x * k + shiftX(_t), y: y * k + shiftY(_t) }
  }

  // Hover and tap: one pointer handler plus a Delaunay lookup instead of ~1,900 listeners.
  let svgEl
  let boxEl
  let hovered = $state(null)
  let tip = $state({ x: 0, y: 0, left: false })

  function onPointer(e) {
    const box = svgEl.getBoundingClientRect()
    const px = e.clientX - box.left
    const py = e.clientY - box.top
    const k = scaleNow(0)
    const i = delaunay.find((px - shiftX(0)) / k, (py - shiftY(0)) / k)
    const dist = Math.hypot(pos[i][0] * k + shiftX(0) - px, pos[i][1] * k + shiftY(0) - py)
    if (dist > 14) {
      hovered = null
      return
    }
    tip = { x: px, y: py, left: px > w * 0.6 }
    hovered = i
  }

  const info = $derived(hovered === null ? null : describe(hovered))
</script>

<div class="map" bind:this={boxEl} bind:clientWidth={w} bind:clientHeight={h}>
  <svg
    bind:this={svgEl}
    width={w}
    height={h}
    viewBox="0 0 {w} {h}"
    role="img"
    aria-label={label}
    onpointermove={onPointer}
    onpointerdown={onPointer}
    onpointerleave={() => (hovered = null)}
  >
    <g transform={worldTransform(tick)}>
      <g class="areas" aria-hidden="true">
        {#each areaPaths as d}<path {d} />{/each}
      </g>
      <g class="stations" aria-hidden="true">
        {#each stations as s, i}
          <circle cx={pos[i][0]} cy={pos[i][1]} r={radius(i, tick)} fill={fill(i, tick)} stroke-width={outline(i, tick)} />
        {/each}
        {#if hovered !== null}
          <circle class="ring" cx={pos[hovered][0]} cy={pos[hovered][1]} r={Math.max(5, cur.r[hovered] + 2) / scaleNow(tick)} />
        {/if}
      </g>
    </g>

    <g aria-hidden="true">
      {#each [screen(-87.619, 41.94, tick)] as lake}
        <text class="lake" x={lake.x} y={lake.y}>Lake Michigan</text>
      {/each}
      {#each annotations as a (a.text)}
        {@const p = screen(a.lng, a.lat, tick)}
        {@const tx = p.x + (a.dx ?? 0)}
        {@const ty = p.y + (a.dy ?? 0)}
        <g class="note">
          <line x1={p.x} y1={p.y} x2={tx} y2={ty} />
          <circle cx={p.x} cy={p.y} r="3" />
          <text x={tx} y={ty} text-anchor={a.anchor ?? 'start'} dy={ty < p.y ? '-0.45em' : '1.05em'}>{a.text}</text>
        </g>
      {/each}
    </g>
  </svg>

  {#if info}
    <div class="tip" class:left={tip.left} style="left:{tip.x}px; top:{tip.y}px" role="status">
      <strong>{info.name}</strong>
      <span class="area">{info.area}</span>
      <span>{info.text}</span>
    </div>
  {/if}
</div>

<style>
  .map { position: relative; width: 100%; height: 100%; }

  svg {
    display: block;
    overflow: hidden;
    touch-action: pan-y;
    /* Soft edges, so a zoomed map fades out instead of being cut off. */
    --edge: 28px;
    -webkit-mask-image:
      linear-gradient(to right, transparent, #000 var(--edge), #000 calc(100% - var(--edge)), transparent),
      linear-gradient(to bottom, transparent, #000 var(--edge), #000 calc(100% - var(--edge)), transparent);
    -webkit-mask-composite: source-in;
    mask-image:
      linear-gradient(to right, transparent, #000 var(--edge), #000 calc(100% - var(--edge)), transparent),
      linear-gradient(to bottom, transparent, #000 var(--edge), #000 calc(100% - var(--edge)), transparent);
    mask-composite: intersect;
  }

  .areas path {
    fill: #efe7d6;
    stroke: #d2c5ac;
    stroke-width: 0.8px;
    vector-effect: non-scaling-stroke;
  }

  .lake {
    font-family: var(--serif);
    font-style: italic;
    font-size: 17px;
    fill: var(--ink-faint);
    letter-spacing: 0.04em;
  }

  .stations circle {
    stroke: rgb(246 241 231 / 0.9);
    vector-effect: non-scaling-stroke;
  }
  .stations .ring {
    fill: none;
    stroke: var(--ink);
    stroke-width: 1.5px;
    vector-effect: non-scaling-stroke;
  }

  .note { animation: rise 0.6s ease both; }
  .note line { stroke: var(--ink); stroke-width: 1.2; opacity: 0.6; }
  .note circle { fill: var(--ink); }
  .note text {
    font-family: var(--sans);
    font-size: 14px;
    font-weight: 600;
    fill: var(--ink);
    paint-order: stroke;
    stroke: var(--paper);
    stroke-width: 5px;
    stroke-linejoin: round;
  }

  .tip {
    position: absolute;
    z-index: 5;
    transform: translate(14px, -110%);
    max-width: 15.5rem;
    padding: 0.55rem 0.7rem;
    background: var(--ink);
    color: var(--paper);
    border-radius: 6px;
    font-family: var(--sans);
    font-size: 0.8rem;
    line-height: 1.35;
    pointer-events: none;
    box-shadow: 0 6px 20px rgb(0 0 0 / 0.2);
  }
  .tip.left { transform: translate(calc(-100% - 14px), -110%); }
  .tip strong { display: block; font-size: 0.86rem; }
  .tip .area { display: block; opacity: 0.7; margin-bottom: 0.25rem; }

  @keyframes rise {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: none; }
  }
</style>
