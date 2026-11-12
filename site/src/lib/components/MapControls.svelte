<script>
  import { clock } from '../format.js'

  let {
    kind = 'time', // 'time' = scrubber only, 'explore' = scrubber + period buttons
    t,
    playing,
    win = null,
    dayType = 'weekday',
    periods = {},
    activePeriod = null,
    onplay,
    onscrub,
    onperiod,
  } = $props()

  const mid = $derived(win ? (win.from + win.to) / 2 : t)
</script>

<div class="controls" role="group" aria-label="Map controls">
  {#if kind === 'explore'}
    <div class="periods" role="group" aria-label="Time period">
      {#each Object.entries(periods) as [key, p]}
        <button
          type="button"
          class:active={activePeriod === key}
          aria-pressed={activePeriod === key}
          onclick={() => onperiod(key)}
        >
          <span>{p.label}</span>
          <small>{p.range}</small>
        </button>
      {/each}
    </div>
  {/if}

  <div class="scrub">
    <output aria-live="off">
      <span class="clock">{win ? win.range : clock(t)}</span>
      <span class="day">{dayType === 'weekday' ? 'Average weekday' : 'Average weekend day'}</span>
    </output>
    <button type="button" class="play" onclick={onplay} aria-label={playing ? 'Pause' : 'Play'}>
      {#if playing}
        <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="5" width="4" height="14" /><rect x="14" y="5" width="4" height="14" /></svg>
      {:else}
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z" /></svg>
      {/if}
    </button>
    <input
      type="range"
      min="0"
      max="24"
      step="0.05"
      value={mid}
      aria-label="Time of day"
      aria-valuetext="{clock(mid)}, {dayType === 'weekday' ? 'average weekday' : 'average weekend day'}"
      oninput={(e) => onscrub(+e.currentTarget.value)}
    />
  </div>
</div>

<style>
  .controls {
    display: grid;
    gap: 0.6rem;
    font-family: var(--sans);
  }

  .periods { display: flex; flex-wrap: wrap; gap: 0.4rem; }
  .periods button {
    display: grid;
    padding: 0.4rem 0.7rem;
    border: 1px solid var(--rule);
    border-radius: 999px;
    background: var(--paper);
    cursor: pointer;
    text-align: left;
    line-height: 1.15;
    font-size: 0.8rem;
    font-weight: 600;
    transition: background 0.15s, border-color 0.15s;
  }
  .periods button small { font-weight: 400; color: var(--ink-soft); font-size: 0.72rem; }
  .periods button:hover { border-color: var(--ink-faint); }
  .periods button.active { background: var(--ink); border-color: var(--ink); color: var(--paper); }
  .periods button.active small { color: #c9cfdc; }

  .scrub {
    display: grid;
    grid-template-columns: auto 1fr;
    grid-template-areas: 'time time' 'play range';
    align-items: center;
    gap: 0.3rem 0.8rem;
  }
  output { grid-area: time; display: flex; align-items: baseline; gap: 0.6rem; line-height: 1.15; }
  .play {
    grid-area: play;
    width: 2.6rem;
    height: 2.6rem;
    border-radius: 50%;
    border: 0;
    background: var(--ink);
    cursor: pointer;
    display: grid;
    place-items: center;
  }
  .play svg { width: 1.2rem; fill: var(--paper); }

  input[type='range'] {
    grid-area: range;
    min-width: 0;
    width: 100%;
    height: 2.2rem;
    accent-color: var(--ink);
    cursor: pointer;
  }

  .clock { font-weight: 700; font-size: 1.15rem; font-variant-numeric: tabular-nums; }
  .day { font-size: 0.72rem; color: var(--ink-soft); }

  @media (max-width: 860px) {
    .periods { flex-wrap: nowrap; overflow-x: auto; margin: 0 -1.1rem; padding: 0 1.1rem 0.2rem; scrollbar-width: none; }
    .periods button { flex: none; }
    .scrub { grid-template-areas: 'play range time'; grid-template-columns: auto 1fr auto; }
    output { flex-direction: column; align-items: flex-end; gap: 0; min-width: 6.4rem; }
    .clock { font-size: 1.02rem; }
  }
</style>
