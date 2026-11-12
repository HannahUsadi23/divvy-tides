<script>
  let { mode = 'dep', kind = 'time', highlighted = false } = $props()
</script>

<div class="legend" aria-hidden="true">
  {#if mode === 'net'}
    <span class="item"><i class="dot" style="background: var(--inflow)"></i> Receives more trips than it sends</span>
    <span class="item"><i class="dot" style="background: var(--outflow)"></i> Sends more than it receives</span>
    <span class="note">Bigger dot, bigger gap</span>
  {:else if kind === 'total' && highlighted}
    <span class="item"><i class="dot" style="background: var(--activity)"></i> The busiest tenth of stations</span>
    <span class="item"><i class="dot" style="background: var(--activity); opacity: 0.22"></i> All other stations</span>
    <span class="note">Bigger dot, more trips</span>
  {:else}
    <span class="item">
      <i class="dot" style="background: var(--activity)"></i>
      {#if kind === 'total'}
        Trips starting here on a typical weekday
      {:else}
        Trips starting here in an average hour
      {/if}
    </span>
    <span class="note">Bigger and darker, more trips</span>
  {/if}
</div>

<style>
  .legend {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem 1rem;
    font-family: var(--sans);
    font-size: 0.74rem;
    color: var(--ink-soft);
    line-height: 1.3;
  }
  .item { display: inline-flex; align-items: center; gap: 0.4rem; }
  .dot { width: 0.75rem; height: 0.75rem; border-radius: 50%; display: inline-block; flex: none; }
  .note { font-style: italic; }

  @media (max-width: 860px) {
    .note { display: none; }
  }
</style>
