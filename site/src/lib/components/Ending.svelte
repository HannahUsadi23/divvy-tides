<script>
  // Section 6 plus methodology. Includes a plain table of the stations behind the net-flow map
  // as an accessible alternative to the visualization.
  import IllustrationSlot from './IllustrationSlot.svelte'
  import { topStations } from '../data.js'
  import { number } from '../format.js'

  let { data } = $props()

  const m = data.methods
  const morning = topStations(data, 'weekday', 7, 10)
  const evening = topStations(data, 'weekday', 16, 19)
  const fmt = (v) => `${v > 0 ? '+' : '−'}${number(Math.abs(v), 0)}`
</script>

<section class="ending">
  <div class="text">
    <h2>What the data can’t show</h2>
    <p>
      The data only has completed trips. If someone found an empty station, or a full one with nowhere to dock, and
      went elsewhere, there’s no record of it.
    </p>
    <p>
      What it does show is a rhythm: the same neighborhoods take in trips in the morning and send them out in the
      evening, day after day.
    </p>
  </div>
  <div class="dock"><IllustrationSlot id="dock" fit="contain" quiet /></div>

  <details class="more">
    <summary>The stations behind the map, as a table</summary>
    <p class="note">
      Net trips on a typical weekday: trips that end at the station minus trips that start there, among
      trips with both ends recorded.
    </p>
    <div class="tables">
      {#each [['Morning rush, 7–10 am', morning], ['Evening rush, 4–7 pm', evening]] as [title, rows]}
        <table>
          <caption>{title}</caption>
          <thead><tr><th>Station</th><th>Area</th><th>Net trips</th></tr></thead>
          <tbody>
            <tr class="band"><th colspan="3" scope="colgroup">Receive more than they send</th></tr>
            {#each rows.gain as r}
              <tr><td>{r.name}</td><td>{r.area}</td><td class="num">{fmt(r.value)}</td></tr>
            {/each}
            <tr class="band"><th colspan="3" scope="colgroup">Send more than they receive</th></tr>
            {#each rows.loss as r}
              <tr><td>{r.name}</td><td>{r.area}</td><td class="num">{fmt(r.value)}</td></tr>
            {/each}
          </tbody>
        </table>
      {/each}
    </div>
  </details>

  <details class="more">
    <summary>How we counted</summary>
    <ul>
      <li>
        <strong>Data.</strong> Divvy’s public trip history, {m.window.start} to {m.window.end}: {number(m.counts.rawTrips)}
        trips. We removed {number(m.counts.removedTrips)} trips shorter than a minute or longer than a day,
        leaving {number(m.counts.cleanTrips)}. Times are Chicago local time.
      </li>
      <li>
        <strong>Stations.</strong> Divvy lists {number(m.counts.rawStationNames)} station names, which include renames and
        overflow “corral” docks. Names that describe the same spot (within 15 meters) are combined
        into {number(m.counts.locations)} locations.
      </li>
      <li>
        <strong>Average weekday.</strong> The mean of all {data.days.weekday} weekdays in the window, holidays
        included, counted by each trip’s own start or end time. A station that was closed for part of the year
        shows lower averages.
      </li>
      <li>
        <strong>Net trips.</strong> Trips ending at a station minus trips starting there, using only the
        {number(m.counts.withBothStations)} trips with both ends recorded. Trips with no recorded station, mostly
        electric bikes left away from a dock, are excluded from net flow and from the station map.
      </li>
      <li>
        <strong>The tide.</strong> Across {number(m.stats.tide.stations)} stations, morning (7–10) and evening (4–7)
        net trips have a correlation of {m.stats.tide.pearson} on weekdays and {m.stats.tide.weekendPearson} on
        weekends. This describes the relationship between stations; it does not show causes.
      </li>
      <li>
        <strong>Sources.</strong> Divvy System Data, operated by Lyft Bikes and Scooters, LLC and made available under the
        Divvy data license agreement. Neighborhood boundaries: City of Chicago Data Portal, community areas.
      </li>
    </ul>
  </details>
</section>

<style>
  .ending {
    max-width: 46rem;
    margin: 0 auto;
    padding: 12vh 1.5rem 14vh;
  }
  h2 { font-size: 2.1rem; margin-bottom: 1rem; }
  /* Larger than the text column, but never taller than the screen. */
  .dock {
    width: min(94vw, 56rem, 92vh);
    aspect-ratio: 1300 / 1241;
    margin: 3rem 0 3.5rem 50%;
    transform: translateX(-50%);
  }

  .more { border-top: 1px solid var(--rule); padding: 0.9rem 0; font-size: 1rem; }
  .more:last-of-type { border-bottom: 1px solid var(--rule); }
  summary { cursor: pointer; font-weight: 600; }
  .note, li { color: var(--ink-soft); line-height: 1.55; }
  ul { padding-left: 1.1rem; display: grid; gap: 0.6rem; }
  li strong { color: var(--ink); }

  .tables { display: grid; gap: 1.5rem; margin-top: 1rem; }
  table { width: 100%; border-collapse: collapse; font-family: var(--sans); font-size: 0.85rem; }
  caption { text-align: left; font-weight: 700; padding-bottom: 0.4rem; }
  th, td { text-align: left; padding: 0.3rem 0.5rem; border-bottom: 1px solid var(--rule); }
  thead th { font-size: 0.74rem; color: var(--ink-soft); }
  .band th { background: var(--paper-deep); font-size: 0.74rem; letter-spacing: 0.03em; }
  .num { text-align: right; font-variant-numeric: tabular-nums; }
</style>
