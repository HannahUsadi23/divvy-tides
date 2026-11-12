<script>
  // How concentrated is ridership? Stations are ranked from busiest to quietest, and the curve
  // shows what share of all trips the busiest stations account for. A straight diagonal would
  // mean every station is equally busy.
  import { scaleLinear } from 'd3-scale'
  import { line, area } from 'd3-shape'
  import { percent } from '../format.js'

  let { starts, topCount } = $props()

  const counts = starts.filter((v) => v > 0).sort((a, b) => b - a)
  const total = counts.reduce((sum, v) => sum + v, 0)
  const points = [[0, 0]]
  let running = 0
  counts.forEach((v, i) => {
    running += v
    points.push([(i + 1) / counts.length, running / total])
  })
  const topShare = points[topCount][1]
  const topFraction = topCount / counts.length

  const W = 280
  const H = 150
  const m = { top: 12, right: 14, bottom: 34, left: 44 }
  const x = scaleLinear().domain([0, 1]).range([m.left, W - m.right])
  const y = scaleLinear().domain([0, 1]).range([H - m.bottom, m.top])
  // Thin the curve for the path; the marked point uses the full data.
  const step = Math.ceil(points.length / 140)
  const thin = points.filter((_, i) => i % step === 0 || i === points.length - 1)
  const curve = line().x((d) => x(d[0])).y((d) => y(d[1]))(thin)
  const fill = area().x((d) => x(d[0])).y0(y(0)).y1((d) => y(d[1]))(thin)
  const ticks = [0, 0.5, 1]
</script>

<figure>
  <svg viewBox="0 0 {W} {H}" role="img" aria-label="The busiest {percent(topFraction)} of stations account for {percent(topShare)} of trips that start at a station.">
    {#each ticks as t}
      <line class="grid" x1={m.left} x2={W - m.right} y1={y(t)} y2={y(t)} />
      <text class="tick" x={m.left - 6} y={y(t) + 3} text-anchor="end">{percent(t)}</text>
      <text class="tick" x={x(t)} y={H - m.bottom + 13} text-anchor="middle">{percent(t)}</text>
    {/each}
    <line class="equal" x1={x(0)} y1={y(0)} x2={x(1)} y2={y(1)} />
    <path class="fill" d={fill} />
    <path class="curve" d={curve} />
    <line class="guide" x1={x(topFraction)} x2={x(topFraction)} y1={y(0)} y2={y(topShare)} />
    <line class="guide" x1={x(0)} x2={x(topFraction)} y1={y(topShare)} y2={y(topShare)} />
    <circle class="mark" cx={x(topFraction)} cy={y(topShare)} r="4.5" />
    <text class="callout" x={x(topFraction) + 9} y={y(topShare) + 15}>
      busiest {percent(topFraction)} of stations
    </text>
    <text class="callout strong" x={x(topFraction) + 9} y={y(topShare) + 28}>
      = {percent(topShare)} of trips
    </text>
    <text class="axis" x={(m.left + W - m.right) / 2} y={H - 4} text-anchor="middle">Stations, busiest first</text>
    <text class="axis" transform="translate(8 {(m.top + H - m.bottom) / 2}) rotate(-90)" text-anchor="middle">Share of trips</text>
  </svg>
  <figcaption><span class="key"></span> If every station were equally busy, the curve would follow the dashed line.</figcaption>
</figure>

<style>
  figure { margin: 0; font-family: var(--sans); }
  svg { display: block; width: 100%; height: auto; }
  .grid { stroke: var(--rule); stroke-width: 1; }
  .equal { stroke: var(--ink-soft); stroke-width: 1.2; stroke-dasharray: 4 4; }
  .fill { fill: var(--activity); opacity: 0.12; }
  .curve { fill: none; stroke: var(--activity); stroke-width: 2.6; stroke-linejoin: round; }
  .guide { stroke: var(--ink); stroke-width: 1; stroke-dasharray: 2 3; opacity: 0.7; }
  .mark { fill: var(--activity); stroke: var(--paper); stroke-width: 1.5; }
  .tick, .axis { font-size: 9.5px; fill: var(--ink-soft); }
  .axis { font-size: 10px; }
  .callout { font-size: 10.5px; fill: var(--ink); paint-order: stroke; stroke: var(--paper); stroke-width: 3px; }
  .callout.strong { font-weight: 700; font-size: 12px; }
  figcaption { font-size: 0.72rem; color: var(--ink-soft); line-height: 1.4; margin-top: 0.1rem; }
  .key { display: inline-block; width: 1.4rem; border-top: 2px dashed var(--ink-soft); vertical-align: middle; margin-right: 0.3rem; }
</style>
