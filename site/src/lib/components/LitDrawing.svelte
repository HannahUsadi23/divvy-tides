<script>
  // Sunlight on a drawing. The drawing is shown as usual; on top of it a warm glow, centered on
  // the sun and clipped to the drawing's own shape (its transparency), so only the buildings or
  // the rider catch the light. The glow strengthens as the sun climbs and falls away with
  // distance, so the side of the city facing the sun is lit first.
  import IllustrationSlot from './IllustrationSlot.svelte'
  import { assetUrl, hasAsset } from '../illustrations.js'

  let {
    id,
    fit = 'cover', // how the drawing fills its box: 'cover' | 'contain'
    sunX, // sun position, percent of the full scene width
    sunY, // sun position, percent of the full scene height
    strength = 0, // 0 (no light) to 1 (full morning light)
    // The drawing's box in the scene, as CSS lengths. Needed to place the glow on the sun.
    boxW = '100vw',
    boxH = '56vh',
    boxRight = '0px',
    boxBottom = '0px',
    sceneH = '100vh',
    // A second drawing on exactly the same canvas, laid directly on top (for example the lit
    // windows over the buildings), with its own opacity.
    overlayId = null,
    overlayOpacity = 1,
  } = $props()

  const url = assetUrl(id)
  // The light is clipped to your drawing, so it only appears once the file exists.
  let drawn = $state(false)
  $effect(() => {
    hasAsset(id).then((ok) => (drawn = ok))
  })
  const cx = $derived(`calc(${sunX} * 1vw - (100vw - ${boxRight} - ${boxW}))`)
  const cy = $derived(`calc(${sunY} * (${sceneH}) / 100 - (${sceneH} - ${boxH} - ${boxBottom}))`)
</script>

<div class="lit">
  <IllustrationSlot {id} {fit} />
  {#if overlayId}
    <div class="overlay" style="opacity: {overlayOpacity}"><IllustrationSlot id={overlayId} {fit} quiet /></div>
  {/if}
  {#if drawn}
    <div
      class="light"
      style="
        -webkit-mask-image: url({url}); mask-image: url({url});
        -webkit-mask-size: {fit}; mask-size: {fit};
        opacity: {strength};
        background:
          radial-gradient(circle 85vmin at {cx} {cy}, rgb(255 232 180 / 1) 0%, rgb(255 190 120 / 0.8) 24%, rgb(255 150 100 / 0.45) 52%, rgb(255 130 90 / 0.14) 80%, transparent 100%);
      "
    ></div>
  {/if}
</div>

<style>
  .lit { position: relative; width: 100%; height: 100%; }
  .overlay { position: absolute; inset: 0; }
  .light {
    position: absolute;
    inset: 0;
    pointer-events: none;
    mix-blend-mode: screen;
    -webkit-mask-repeat: no-repeat;
    mask-repeat: no-repeat;
    -webkit-mask-position: center bottom;
    mask-position: center bottom;
  }
</style>
