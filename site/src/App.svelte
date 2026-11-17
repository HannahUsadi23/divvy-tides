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
      I knew I had a Divvy problem when I showed up to a date at a cute French café 25 minutes late, drenched in
      sweat, after biking to six different stations in search of an empty dock.
    </p>
    <p>
      When I moved from Atlanta to Chicago, one of the first things I did was trade my car for a bike. I spent that
      first summer flying around the city on Divvys, getting to know Chicago one docking station at a time. I even
      rode one in Critical Mass, a massive group bike ride through the city, and racked up a $40 charge along the
      way.
    </p>
    <p>
      I’ve spent countless hours hunting for empty docks, and slightly fewer hunting for bikes when I’m running late.
      I’ve come to think of Chicago less as a collection of neighborhoods and more as a network of places where I can
      theoretically return a bicycle.
    </p>
    <p>
      But while I was circling the block looking for somewhere to park, millions of other people were making their own
      trips across the city.
    </p>
    <p>
      From October 2025 to September 2026, Divvy recorded roughly six million completed rides. Together, they reveal
      a pattern in how Chicago moves that I never noticed while pedaling through it.
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
