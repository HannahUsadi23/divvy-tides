<script>
  import { loadData } from './lib/data.js'
  import Hero from './lib/components/Hero.svelte'
  import Story from './lib/components/Story.svelte'
  import Ending from './lib/components/Ending.svelte'
  import IllustrationSlot from './lib/components/IllustrationSlot.svelte'

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const loading = loadData()
</script>

<main>
  <Hero {reduceMotion} />

  <section class="opening">
    <p>
      Every morning, Chicago begins to move. People leave their neighborhoods, head toward work and make their way
      across the city.
    </p>
    <p>
      Beneath the rhythm of the commute, there’s a pattern. A year of Divvy trips, about six million of them from
      October 2025 to September 2026, shows where the city goes and when.
    </p>
  </section>

  <div class="wheels"><IllustrationSlot id="wheels" pos="center 22%" quiet /></div>

  {#await loading}
    <p class="status" role="status">Loading a year of trips…</p>
  {:then data}
    <Story {data} {reduceMotion} />
    <Ending {data} />
  {:catch error}
    <p class="status" role="alert">The data didn’t load. {error.message}</p>
  {/await}
</main>

<style>
  .opening {
    max-width: 38rem;
    margin: 0 auto;
    padding: 14vh 1.5rem 6vh;
    font-size: 1.3rem;
    line-height: 1.55;
  }
  .opening p:first-child::first-letter {
    float: left;
    font-size: 4.2rem;
    line-height: 0.82;
    padding: 0.35rem 0.5rem 0 0;
    font-weight: 700;
  }
  .wheels { height: clamp(260px, 60vh, 640px); margin: 2vh 0 0; }
  .status { text-align: center; padding: 20vh 1.5rem; font-family: var(--sans); color: var(--ink-soft); }
</style>
