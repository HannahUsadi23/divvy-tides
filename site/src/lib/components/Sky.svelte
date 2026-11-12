<script module>
  const clampN = (v) => Math.min(1, Math.max(0, v))
  const smoothN = (v) => {
    const c = clampN(v)
    return c * c * (3 - 2 * c)
  }
  // Where the sun is (percent of the sky box) at timeline position p.
  export const SUN_DAWN = { x: [60, 67], y: [114, 34] }
  export const sunAt = (p, sun = SUN_DAWN) => ({
    x: sun.x[0] + (sun.x[1] - sun.x[0]) * clampN(p),
    y: sun.y[0] + (sun.y[1] - sun.y[0]) * smoothN(p),
  })

  // Sky colors at points along the timeline (0 to 1), top of sky to horizon.
  export const DAWN = [
    { at: 0, top: '#0a0f26', mid: '#121a3d', low: '#1f2650' },
    { at: 0.3, top: '#121a43', mid: '#34336a', low: '#6b4e86' },
    { at: 0.55, top: '#2d3a7a', mid: '#a0638f', low: '#f09a73' },
    { at: 0.8, top: '#5f84c0', mid: '#d9a7a0', low: '#f8c987' },
    { at: 1, top: '#8db4e0', mid: '#cfd9e4', low: '#fbe2b3' },
  ]
  export const DUSK = [
    { at: 0, top: '#6a86bf', mid: '#e3a98f', low: '#f7c486' },
    { at: 0.5, top: '#3a4688', mid: '#b8708f', low: '#f09a73' },
    { at: 1, top: '#0b1030', mid: '#2a2f66', low: '#7a4a7e' },
  ]
</script>

<script>
  // The sky and the sun. If you've drawn a sun, sky-night or sky-day, those files are used;
  // anything missing is painted in code. The page only moves and fades them.
  import { assetUrl, hasAsset } from '../illustrations.js'

  let {
    p = 0, // position on the timeline, 0 to 1
    stops = DAWN,
    sun = SUN_DAWN, // percent of the box, start to end
    stars = 'dawn', // 'dawn' stars fade out; 'dusk' stars fade in
    plate = null, // 0 = night sky, 1 = day sky, for painted skies (defaults to p)
  } = $props()

  let drawn = $state({ sun: false, night: false, day: false })
  $effect(() => {
    Promise.all([hasAsset('sun'), hasAsset('skyNight'), hasAsset('skyDay')]).then(([s, n, d]) => {
      drawn = { sun: s, night: n, day: d }
    })
  })
  const painted = $derived(drawn.night && drawn.day)

  const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16))
  const mix = (a, b, t) => a.map((v, i) => Math.round(v + (b[i] - v) * t))
  const clamp = (v) => Math.min(1, Math.max(0, v))
  const smooth = (v) => {
    const c = clamp(v)
    return c * c * (3 - 2 * c)
  }

  const colors = $derived.by(() => {
    const x = clamp(p)
    let i = stops.findIndex((s) => s.at >= x)
    if (i <= 0) i = 1
    const a = stops[i - 1]
    const b = stops[i]
    const t = clamp((x - a.at) / (b.at - a.at))
    const out = {}
    for (const key of ['top', 'mid', 'low']) out[key] = `rgb(${mix(hex(a[key]), hex(b[key]), t).join(',')})`
    return out
  })

  const sunX = $derived(sun.x[0] + (sun.x[1] - sun.x[0]) * clamp(p))
  const sunY = $derived(sun.y[0] + (sun.y[1] - sun.y[0]) * smooth(p))
  const height = $derived(clamp(1 - (sunY - 34) / 80))
  const starOpacity = $derived(stars === 'dawn' ? 1 - smooth(p / 0.4) : smooth((p - 0.55) / 0.4))
  const mixAmount = $derived(smooth(plate ?? p))

  let seed = 5
  const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647
  const field = Array.from({ length: 90 }, () => ({ x: rnd() * 100, y: rnd() * 58, r: 0.5 + rnd() * 1.1, o: 0.4 + rnd() * 0.6 }))
</script>

<div
  class="sky"
  style={painted ? 'background: #0a0f26' : `background: linear-gradient(180deg, ${colors.top} 0%, ${colors.mid} 55%, ${colors.low} 100%)`}
  aria-hidden="true"
>
  {#if painted}
    <img class="plate" src={assetUrl('skyNight')} alt="" />
    <img class="plate" src={assetUrl('skyDay')} alt="" style="opacity: {mixAmount}" />
  {:else}
    <svg class="stars" style="opacity: {starOpacity}" viewBox="0 0 100 100" preserveAspectRatio="none">
      {#each field as s}<ellipse cx={s.x} cy={s.y} rx={s.r * 0.12} ry={s.r * 0.2} fill="#fff" opacity={s.o} />{/each}
    </svg>
  {/if}
  <div class="glow" style="left: {sunX}%; top: {sunY}%; opacity: {height * (painted ? 0.5 : 0.95)}"></div>
  {#if drawn.sun}
    <img class="sun drawn" src={assetUrl('sun')} alt="" style="left: {sunX}%; top: {sunY}%" />
  {:else}
    <div class="sun" style="left: {sunX}%; top: {sunY}%"></div>
  {/if}
</div>

<style>
  .sky { position: absolute; inset: 0; overflow: hidden; }
  .stars { position: absolute; inset: 0; width: 100%; height: 100%; }
  .plate { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }

  .glow {
    position: absolute;
    width: 150vmin;
    height: 150vmin;
    transform: translate(-50%, -50%);
    background: radial-gradient(circle, rgb(255 214 150 / 0.75) 0%, rgb(255 170 120 / 0.28) 28%, transparent 62%);
    pointer-events: none;
  }
  .sun {
    position: absolute;
    width: 11vmin;
    height: 11vmin;
    min-width: 56px;
    min-height: 56px;
    transform: translate(-50%, -50%);
    border-radius: 50%;
    background: radial-gradient(circle at 50% 45%, #fffbe8 0%, #ffe9b0 60%, #ffd78a 100%);
    box-shadow: 0 0 60px 20px rgb(255 214 150 / 0.55);
  }
  .sun.drawn {
    width: 11vmin;
    height: 11vmin;
    min-width: 56px;
    min-height: 56px;
    border-radius: 0;
    background: none;
    box-shadow: none;
    object-fit: contain;
    /* The same soft halo as before, following the shape of the drawing. */
    filter: drop-shadow(0 0 22px rgb(255 214 150 / 0.6)) drop-shadow(0 0 48px rgb(255 214 150 / 0.4));
  }
</style>
