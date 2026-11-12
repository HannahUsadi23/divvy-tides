<script>
  import { illustrations, assetUrl } from '../illustrations.js'
  import SkylinePlaceholder from './SkylinePlaceholder.svelte'

  // quiet: render nothing at all when the file is missing (for optional layers).
  let { id, style = '', fit = 'cover', quiet = false, pos = 'center bottom' } = $props()

  const art = illustrations[id]
  let missing = $state(false)
</script>

{#if !missing}
  <figure class="slot {id}" {style}>
    <img src={assetUrl(id)} alt={art.alt} style="object-fit: {fit}; object-position: {pos}" onerror={() => (missing = true)} />
  </figure>
{:else if !quiet}
  <figure class="slot {id}" {style}>
    {#if id === 'skyline'}
      <div class="skyline-fallback" role="img" aria-label="Placeholder: {art.alt}">
        <SkylinePlaceholder />
      </div>
      <p class="tag">
        <strong>Illustration placeholder</strong>
        <span>{art.brief}</span>
        <code>public/illustrations/{art.file}</code>
      </p>
    {:else}
      <div class="placeholder" role="img" aria-label="Placeholder: {art.alt}" style="aspect-ratio: {art.ratio}">
        <p class="tag">
          <strong>Illustration placeholder</strong>
          <span>{art.brief}</span>
          <code>public/illustrations/{art.file}</code>
        </p>
      </div>
    {/if}
  </figure>
{/if}

<style>
  .slot { position: relative; margin: 0; width: 100%; height: 100%; }
  img { display: block; width: 100%; height: 100%; object-position: center bottom; }
  .skyline-fallback { position: absolute; inset: 0; color: #0a0e1f; }

  .placeholder {
    display: grid;
    width: 100%;
    background: repeating-linear-gradient(45deg, transparent 0 14px, rgb(0 0 0 / 0.035) 14px 15px), var(--paper-deep);
    border: 2px dashed var(--rule);
    color: var(--ink);
  }

  .tag {
    position: absolute;
    top: 0;
    left: 0;
    margin: 1rem;
    display: grid;
    gap: 0.25rem;
    max-width: 22rem;
    font-family: var(--sans);
    font-size: 0.78rem;
    line-height: 1.35;
    color: #f2ecdd;
    text-shadow: 0 1px 6px rgb(0 0 0 / 0.5);
  }
  .skyline .tag { left: auto; right: 0; text-align: right; }
  .placeholder .tag { position: static; color: var(--ink); text-shadow: none; }
  .tag strong { font-size: 0.8rem; letter-spacing: 0.06em; text-transform: uppercase; }
  .tag code { font-size: 0.72rem; opacity: 0.85; }
</style>
