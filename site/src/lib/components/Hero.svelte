<script>
  // Section 1: the illustrated opening. The sky, stars and sun are drawn in code and driven by
  // scroll, so the sun rises behind your skyline illustration. Past the sunrise the scene
  // dissolves into the paper background where the map begins. With reduced motion the finished
  // sunrise is shown and nothing is tied to scrolling.
  import Sky, { sunAt } from './Sky.svelte'
  import LitDrawing from './LitDrawing.svelte'

  let { reduceMotion = false } = $props()

  let el
  let scroll = $state(reduceMotion ? 0.75 : 0)

  $effect(() => {
    if (reduceMotion) return
    const update = () => {
      const r = el.getBoundingClientRect()
      const span = r.height - window.innerHeight
      scroll = Math.min(1, Math.max(0, -r.top / span))
    }
    update()
    window.addEventListener('scroll', update, { passive: true })
    window.addEventListener('resize', update)
    return () => {
      window.removeEventListener('scroll', update)
      window.removeEventListener('resize', update)
    }
  })

  const smooth = (x) => {
    const c = Math.min(1, Math.max(0, x))
    return c * c * (3 - 2 * c)
  }
  // The sun is up by 75% of the scroll; the last stretch dissolves into the page.
  const time = $derived(smooth(scroll / 0.75))
  const dissolve = $derived(smooth((scroll - 0.8) / 0.2))
  const sun = $derived(sunAt(time))
  // Sunlight strength: nothing until the sun clears the horizon, full once it is well up.
  const strength = $derived(smooth((100 - sun.y + 4) / 70) * 0.9)
  // Window lights stay on while it is dark and fade out as the sun comes up.
  const windows = $derived(1 - smooth((time - 0.15) / 0.6))
</script>

<header class="hero" bind:this={el} style="height: {reduceMotion ? '100vh' : '230vh'}">
  <div class="pin">
    <Sky p={time} />
    <div class="skyline" style="filter: brightness({0.9 + 0.45 * time})">
      <div class="ground"></div>
      <LitDrawing
        id="skyline"
        overlayId="skylineLit"
        overlayOpacity={windows}
        sunX={sun.x}
        sunY={sun.y}
        {strength}
        boxW="100vw"
        boxH="var(--sky-h)"
      />
    </div>
    <div class="foreground" style="filter: brightness({0.6 + 0.4 * time})">
      <LitDrawing
        id="foreground"
        fit="contain"
        sunX={sun.x}
        sunY={sun.y}
        strength={strength * 0.85}
        boxW="var(--fg-w)"
        boxH="calc(var(--fg-w) * 1.135)"
        boxRight="var(--fg-right)"
        boxBottom="4vh"
      />
    </div>
    <div class="scrim"></div>
    <div class="title" style="opacity: {1 - dissolve * 0.9}">
      <p class="kicker">Data story</p>
      <h1>Where Do Chicago’s Divvy Bikes Go?</h1>
      <p class="deck">A year of Divvy trips shows a tide moving through the city every weekday.</p>
      <p class="byline">By Hannah Usadi</p>
    </div>
    <p class="cue" style="opacity: {1 - scroll * 3}" aria-hidden="true">Scroll</p>
    <div class="fade" style="opacity: {dissolve}"></div>
  </div>
</header>

<style>
  .hero { position: relative; }
  .pin {
    --sky-h: clamp(200px, 37vw, 56vh);
    --fg-w: clamp(210px, 30vw, 440px);
    --fg-right: max(1rem, 5vw);
    position: sticky;
    top: 0;
    height: 100vh;
    overflow: hidden;
    background: var(--night);
  }
  .skyline { position: absolute; left: 0; right: 0; bottom: 0; height: var(--sky-h); }
  /* The painted base of the city is see-through; this is the ground it sits on. */
  .ground {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    height: 24%;
    background: linear-gradient(180deg, rgb(10 34 55 / 0) 0%, rgb(10 34 55 / 0.92) 55%, rgb(10 34 55) 100%);
  }
  .foreground {
    position: absolute;
    right: var(--fg-right);
    bottom: 4vh;
    width: var(--fg-w);
    aspect-ratio: 1100 / 1249;
  }
  .scrim {
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgb(10 14 30 / 0.5) 0%, rgb(10 14 30 / 0.22) 38%, transparent 60%);
    pointer-events: none;
  }
  .title {
    position: absolute;
    left: max(1.5rem, calc((100% - 1280px) / 2 + 1.5rem));
    right: 1.5rem;
    top: max(5vh, 2.25rem);
    max-width: 44rem;
    color: #fff7ea;
    text-shadow: 0 2px 24px rgb(0 0 0 / 0.45);
  }
  .kicker {
    margin: 0 0 0.8rem;
    font-family: var(--sans);
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    opacity: 0.9;
  }
  h1 { font-size: clamp(2.4rem, min(5.2vw, 7.4vh), 4.2rem); }
  .deck { margin: 0.8rem 0 0.6rem; font-size: clamp(1.1rem, 2.2vw, 1.45rem); max-width: 34rem; line-height: 1.4; }
  .byline { margin: 0; font-family: var(--sans); font-size: 0.85rem; opacity: 0.85; }
  .cue {
    position: absolute;
    left: 50%;
    bottom: 3vh;
    transform: translateX(-50%);
    margin: 0;
    font-family: var(--sans);
    font-size: 0.72rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #fff7ea;
  }
  .fade { position: absolute; inset: 0; background: var(--paper); pointer-events: none; }

  /* Phones: the title goes up into the empty sky, and the city and rider get more room. */
  @media (max-width: 860px) {
    .title { top: 11vh; }
    .pin {
      --sky-h: clamp(220px, 40vh, 420px);
      --fg-w: clamp(200px, 56vw, 320px);
      --fg-right: 4vw;
    }
  }
</style>
