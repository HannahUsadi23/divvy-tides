<script>
  // Stand-in skyline drawn in code so the sunrise can be judged before the real illustration
  // exists. Window lights are warm and fade with the --lights variable (set by the parent).
  let seed = 11
  const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647

  const W = 1600
  const H = 500
  const blocks = []
  let x = -10
  while (x < W) {
    const width = 26 + rnd() * 48
    const height = 60 + rnd() * 150
    blocks.push({ x, y: H - height, w: width, h: height })
    x += width - 3
  }

  // A few taller landmarks: a stepped tower with antennas, a tapering one, and two plain ones.
  const towers = [
    { d: 'M610 500 V150 H628 V120 H650 V90 H672 V120 H694 V150 H712 V500 Z', mast: [[640, 90, 640, 40], [662, 90, 662, 50]] },
    { d: 'M1010 500 L1026 170 H1090 L1106 500 Z', mast: [[1042, 170, 1042, 120], [1074, 170, 1074, 124]] },
    { d: 'M1190 500 V190 H1240 V500 Z', mast: [] },
    { d: 'M380 500 V250 H408 V222 H436 V250 H452 V500 Z', mast: [[422, 222, 422, 190]] },
  ]

  const lights = []
  for (const b of blocks) {
    const columns = Math.floor(b.w / 9)
    for (let c = 0; c < columns; c++) {
      for (let y = b.y + 10; y < H - 14; y += 14) {
        if (rnd() < 0.09) lights.push({ x: b.x + 5 + c * 9, y })
      }
    }
  }
</script>

<svg viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMax slice" aria-hidden="true">
  <g class="body">
    {#each blocks as b}<rect x={b.x} y={b.y} width={b.w} height={b.h} />{/each}
    {#each towers as t}
      <path d={t.d} />
      {#each t.mast as m}<line x1={m[0]} y1={m[1]} x2={m[2]} y2={m[3]} />{/each}
    {/each}
    <rect x="0" y={H - 14} width={W} height="14" />
  </g>
  <g class="windows">
    {#each lights as l}<rect x={l.x} y={l.y} width="3" height="5" />{/each}
  </g>
</svg>

<style>
  svg { display: block; width: 100%; height: 100%; }
  .body rect, .body path { fill: currentColor; }
  .body line { stroke: currentColor; stroke-width: 2.5; }
  .windows rect { fill: #ffd58a; opacity: var(--lights, 0.7); }
</style>
