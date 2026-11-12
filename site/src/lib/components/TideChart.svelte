<script>
  // A small D3 line chart: net trips per hour for the downtown core and everywhere else.
  // The two lines mirror each other, which is the tide in one picture.
  import { scaleLinear } from 'd3-scale'
  import { line, curveMonotoneX } from 'd3-shape'
  import { max } from 'd3-array'
  import { hourLabel } from '../format.js'

  let { curve, hour = null } = $props()

  const W = 360
  const H = 118
  const m = { top: 14, right: 8, bottom: 20, left: 8 }

  const limit = Math.ceil(max([...curve.core, ...curve.rest].map(Math.abs)) / 20) * 20
  const x = scaleLinear().domain([0, 23]).range([m.left, W - m.right])
  const y = scaleLinear().domain([-limit, limit]).range([H - m.bottom, m.top])
  const draw = line().x((_, h) => x(h)).y((v) => y(v)).curve(curveMonotoneX)
  const core = draw(curve.core)
  const rest = draw(curve.rest)
  const ticks = [0, 6, 12, 18]
</script>

<figure>
  <svg viewBox="0 0 {W} {H}" role="img" aria-label="Net trips by hour on an average weekday. Downtown receives more trips than it sends in the morning and the reverse in the evening. The rest of the city does the opposite.">
    <rect class="up" x={m.left} y={m.top} width={W - m.left - m.right} height={y(0) - m.top} />
    <rect class="down" x={m.left} y={y(0)} width={W - m.left - m.right} height={H - m.bottom - y(0)} />
    <line class="zero" x1={m.left} x2={W - m.right} y1={y(0)} y2={y(0)} />
    {#each ticks as h}
      <text class="tick" x={x(h)} y={H - 5} text-anchor="middle">{hourLabel(h)}</text>
    {/each}
    <path class="rest" d={rest} />
    <path class="core" d={core} />
    {#if hour !== null}
      <line class="now" x1={x(Math.min(23, Math.max(0, hour)))} x2={x(Math.min(23, Math.max(0, hour)))} y1={m.top - 4} y2={H - m.bottom} />
    {/if}
    <text class="band" x={m.left + 2} y={m.top + 9}>more trips arrive</text>
    <text class="band" x={m.left + 2} y={H - m.bottom - 4}>more trips leave</text>
  </svg>
  <figcaption>
    <span><i class="key solid"></i> Downtown (within 3 km of the Loop)</span>
    <span><i class="key dash"></i> Rest of the city</span>
  </figcaption>
</figure>

<style>
  figure { margin: 0; font-family: var(--sans); }
  svg { display: block; width: 100%; height: auto; }
  .up { fill: var(--inflow); opacity: 0.07; }
  .down { fill: var(--outflow); opacity: 0.08; }
  .zero { stroke: var(--ink-faint); stroke-width: 1; }
  .core { fill: none; stroke: var(--ink); stroke-width: 2.4; }
  .rest { fill: none; stroke: var(--ink-soft); stroke-width: 2; stroke-dasharray: 5 4; }
  .now { stroke: var(--ink); stroke-width: 1.2; }
  .tick { font-size: 10px; fill: var(--ink-soft); }
  .band { font-size: 9.5px; fill: var(--ink-soft); font-style: italic; }
  figcaption { display: flex; flex-wrap: wrap; gap: 0.2rem 1rem; font-size: 0.72rem; color: var(--ink-soft); }
  .key { display: inline-block; width: 1.4rem; height: 0; border-top: 2.4px solid var(--ink); vertical-align: middle; margin-right: 0.3rem; }
  .key.dash { border-top: 2px dashed var(--ink-soft); }
</style>
