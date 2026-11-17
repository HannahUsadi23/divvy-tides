<script>
  // Sections 2-4: one sticky map, reused for every beat. Scrolling past a step changes what
  // the map shows; the reader can also scrub time, pick a period or change the zoom.
  import { untrack } from 'svelte'
  import ChicagoMap from './ChicagoMap.svelte'
  import MapControls from './MapControls.svelte'
  import MapLegend from './MapLegend.svelte'
  import TideChart from './TideChart.svelte'
  import ConcentrationChart from './ConcentrationChart.svelte'
  import { fillValues, dailyTotals, robustMax, areaNet } from '../data.js'
  import { hourLabel, number, percent } from '../format.js'

  let { data, reduceMotion = false } = $props()

  const periods = {
    morning: { label: 'Morning rush', range: '7–10 am', dayType: 'weekday', from: 7, to: 10 },
    midday: { label: 'Midday', range: '12–3 pm', dayType: 'weekday', from: 12, to: 15 },
    evening: { label: 'Evening rush', range: '4–7 pm', dayType: 'weekday', from: 16, to: 19 },
    weekend: { label: 'Weekend afternoon', range: '1–5 pm', dayType: 'weekend', from: 13, to: 17 },
  }
  const windowOf = (key) => ({ from: periods[key].from, to: periods[key].to, range: periods[key].range })

  const maxes = { dep: robustMax(data, 'dep', 'weekday'), net: robustMax(data, 'net', 'weekday') }
  const totals = dailyTotals(data, 'weekday')
  const totalMax = Math.max(...totals)
  const conc = data.methods.stats.concentration
  const tide = data.methods.stats.tide
  const curve = data.methods.stats.tideCurve
  const core = data.methods.view.core

  const top10 = new Uint8Array(data.n)
  Array.from(data.stations.keys())
    .sort((a, b) => data.stations[b].starts - data.stations[a].starts)
    .slice(0, conc.top10Count)
    .forEach((i) => (top10[i] = 1))

  const round10 = (v) => number(Math.round(Math.abs(v) / 10) * 10)
  const net = (area, key) => areaNet(data, area, periods[key].dayType, periods[key].from, periods[key].to)
  const facts = {
    loopMorning: round10(net('Loop', 'morning')),
    loopEvening: round10(net('Loop', 'evening')),
    westTownMorning: round10(net('West Town', 'morning')),
    lincolnParkMorning: round10(net('Lincoln Park', 'morning')),
    lincolnParkEvening: round10(net('Lincoln Park', 'evening')),
  }

  // Label offsets are in screen pixels.
  const places = {
    loop: { lng: -87.6298, lat: 41.8819, text: 'The Loop', dx: 58, dy: 34, anchor: 'start' },
    lincolnPark: { lng: -87.6485, lat: 41.9217, text: 'Lincoln Park', dx: -62, dy: -36, anchor: 'end' },
    westTown: { lng: -87.676, lat: 41.9005, text: 'West Town', dx: -70, dy: 22, anchor: 'end' },
  }
  const tideNotes = [places.loop, places.lincolnPark, places.westTown]

  const steps = [
    {
      id: 'night',
      paragraphs: [
        'At 4:30 in the morning, Chicago’s bike-share stations are nearly still.',
        'Each dot represents a station, sized by the number of trips that begin there during an average weekday hour.',
      ],
      alt: 'Map of Divvy stations at 4:30 am on an average weekday. Almost every station is small and pale.',
      scene: { kind: 'time', measure: 'dep', dayType: 'weekday', time: 4.5, controls: 'time', zoom: 'core' },
    },
    {
      id: 'play',
      paragraphs: [
        'Then the commute begins. Activity builds through the morning, and by late afternoon, the rush is even bigger.',
        'The city has its own rhythm. But not every part of Chicago moves to the same beat.',
      ],
      alt: 'Map of Divvy stations animating through an average weekday, with dark clusters downtown at about 8 am and 5 pm.',
      scene: { kind: 'time', measure: 'dep', dayType: 'weekday', time: 8, controls: 'time', autoplay: true, zoom: 'core' },
    },
    {
      id: 'uneven',
      paragraphs: [
        'That activity isn’t spread evenly across Chicago.',
        `The busiest 10% of stations, many clustered downtown and along the lakefront, account for ${percent(conc.top10ShareOfStationStarts)} of trips that begin at a recorded station.`,
        `Half of those trips start at just ${conc.locationsForHalf} of the ${number(conc.locationsWithStarts)} locations in the analysis.`,
        `And even this map doesn’t tell the whole story. Roughly one in five trips has no recorded starting station, often because electric bikes can be left away from docks. Including those trips, the busiest tenth accounts for ${percent(conc.top10ShareOfAllCleanTrips)} of all rides.`,
        'The concentration is striking. But it tells us where rides happened, not necessarily where everyone wanted to ride.',
      ],
      alt: 'Map of every Divvy station, sized by trips per weekday. The busiest tenth, downtown and along the lakefront, are dark; the rest are faint. A chart shows the busiest tenth of stations account for about 60% of trips.',
      scene: { kind: 'total', measure: 'dep', dayType: 'weekday', controls: 'none', highlight: true, concentration: true, zoom: 'city' },
    },
    {
      id: 'tide',
      paragraphs: [
        'I’ve spent plenty of time wondering where I could return a Divvy. But there’s another question hiding in the data: where are all those trips ending?',
        'On weekday mornings, Divvy trips flow toward the Loop.',
        `Between 7 and 10 am, about ${facts.loopMorning} more trips end in the Loop than begin there on an average weekday. In West Town, the opposite happens: about ${facts.westTownMorning} more trips begin than end. Lincoln Park sends out about ${facts.lincolnParkMorning} more than it receives.`,
      ],
      small: 'Blue stations receive more trips than they send out. Coral stations send out more than they receive. The map isn’t showing how many bikes are physically at each station. It’s showing the balance between recorded arrivals and departures.',
      alt: 'Map of net trips in the morning rush. Downtown stations are blue, receiving more trips than they send. Neighborhoods to the north and west are coral.',
      scene: { kind: 'time', measure: 'net', dayType: 'weekday', window: 'morning', controls: 'none', chart: true, notes: tideNotes, zoom: 'core' },
    },
    {
      id: 'midday',
      paragraphs: [
        'By early afternoon, rides are still happening across Chicago, but arrivals and departures are more evenly matched in the central area.',
      ],
      alt: 'Map of net trips at midday. Most stations are small and neutral.',
      scene: { kind: 'time', measure: 'net', dayType: 'weekday', window: 'midday', controls: 'none', chart: true, notes: [], zoom: 'core' },
    },
    {
      id: 'flip',
      pause: true,
      paragraphs: ['Then the map flips.'],
      alt: 'Map of net trips in the evening rush. The colors are reversed: downtown stations are coral and the neighborhoods are blue.',
      scene: { kind: 'time', measure: 'net', dayType: 'weekday', window: 'evening', controls: 'none', chart: true, notes: tideNotes, zoom: 'core' },
    },
    {
      id: 'evening',
      paragraphs: [
        'By evening, the direction reverses.',
        `Between 4 and 7 pm, the Loop sends out about ${facts.loopEvening} more trips than it receives. Lincoln Park, which lost trips in the morning, now gains about ${facts.lincolnParkEvening}.`,
        'And this isn’t just a downtown phenomenon.',
        `Of the ${number(tide.flipStations)} stations that gained or lost at least ${tide.flipMinTrips} trips over the year in both rush hours, ${percent(tide.flipShare)} reverse direction between the two.`,
        'Stations that receive more trips than they send out in the morning tend to do the opposite in the evening.',
        'The city isn’t simply becoming busier or quieter. The direction of its movement is changing.',
      ],
      alt: 'Map of net trips in the evening rush. The colors are reversed: downtown stations are coral and the neighborhoods are blue.',
      scene: { kind: 'time', measure: 'net', dayType: 'weekday', window: 'evening', controls: 'none', chart: true, notes: tideNotes, zoom: 'core' },
    },
    {
      id: 'weekend',
      paragraphs: [
        'On weekends, that near-mirror-image pattern is much weaker.',
        'Without the same weekday commuting rhythm, trips follow a different schedule. The sharp morning peak fades, and riding builds more gradually toward the afternoon.',
        'The contrast suggests that commuting plays an important role in shaping Divvy’s weekday movements, although the data doesn’t tell us precisely why any individual person rides.',
      ],
      alt: 'Map of net trips on a weekend afternoon. Dots are smaller and the blue and coral are mixed together, compared with the weekday rush hours.',
      scene: { kind: 'time', measure: 'net', dayType: 'weekend', window: 'weekend', controls: 'none', chart: false, notes: [], zoom: 'core' },
    },
    {
      id: 'explore',
      paragraphs: [
        'On weekdays, morning and evening movements look remarkably similar in magnitude, but opposite in direction.',
      ],
      small: 'That pattern isn’t proof that individual bikes return to where they started. Divvy crews also move bikes between stations, and those movements aren’t captured here.',
      alt: 'Interactive map of net trips. Use the period buttons or the time slider to change the view.',
      scene: { kind: 'time', measure: 'net', dayType: 'weekday', window: 'morning', controls: 'explore', chart: true, notes: [], zoom: 'core' },
    },
  ]

  // View state, set whenever the active step changes and adjusted by the controls.
  let active = $state(0)
  let kind = $state('time')
  let measure = $state('dep')
  let dayType = $state('weekday')
  let t = $state(4.5)
  let win = $state(null)
  let activePeriod = $state(null)
  let playing = $state(false)
  let controls = $state('time')
  let chart = $state(false)
  let showConcentration = $state(false)
  let highlighted = $state(false)
  let notes = $state([])
  let label = $state(steps[0].alt)
  let sceneZoom = $state('core')
  let zoomOverride = $state(null)
  let touched = false

  const zoom = $derived(zoomOverride ?? sceneZoom)

  function applyScene(step) {
    const s = step.scene
    kind = s.kind
    measure = s.measure
    dayType = s.dayType
    controls = s.controls
    chart = !!s.chart
    showConcentration = !!s.concentration
    highlighted = !!s.highlight
    notes = s.notes ?? []
    label = step.alt
    activePeriod = s.window ?? null
    win = s.window ? windowOf(s.window) : null
    sceneZoom = s.zoom ?? 'core'
    zoomOverride = null
    if (s.autoplay) {
      // Keep going if the clock is already running; otherwise play the day from the start.
      if (reduceMotion) {
        t = s.time ?? 8
        playing = false
      } else if (!playing) {
        t = 4.5
        playing = true
      }
    } else {
      playing = false
      if (s.time !== undefined) t = s.time
    }
  }

  $effect(() => {
    const step = steps[active]
    untrack(() => applyScene(step))
  })

  // Playback: advance the clock until 10 pm, then stop.
  $effect(() => {
    if (!playing) return
    let raf
    let last = performance.now()
    const advance = (now) => {
      t = Math.min(22, t + ((now - last) / 1000) * 1.25)
      last = now
      if (t >= 22) {
        playing = false
        return
      }
      raf = requestAnimationFrame(advance)
    }
    raf = requestAnimationFrame(advance)
    return () => cancelAnimationFrame(raf)
  })

  // Start the day on its own as soon as the map is half on screen.
  let stageEl
  let inView = $state(false)
  let autoStarted = false
  $effect(() => {
    const observer = new IntersectionObserver(([entry]) => (inView = entry.isIntersecting), { threshold: 0.5 })
    observer.observe(stageEl)
    return () => observer.disconnect()
  })
  $effect(() => {
    if (!inView || autoStarted || reduceMotion) return
    autoStarted = true
    const timer = setTimeout(() => {
      if (active <= 1 && !touched && !playing) {
        t = 4.5
        playing = true
      }
    }, 700)
    return () => clearTimeout(timer)
  })

  const values = $derived.by(() => {
    if (kind === 'total') return totals
    const from = win ? win.from : t - 0.5
    const to = win ? win.to : t + 0.5
    return fillValues(new Float32Array(data.n), data, { measure, dayType, from, to })
  })
  const mode = $derived(kind === 'total' ? 'dep' : measure)
  const startsPerStation = data.stations.map((s) => s.starts)
  const maxValue = $derived(kind === 'total' ? totalMax : maxes[measure])
  const chartHour = $derived(
    chart && dayType === 'weekday' ? (win ? (win.from + win.to) / 2 : t) - 0.5 : null
  )

  function describe(i) {
    const s = data.stations[i]
    const v = values[i]
    let text
    if (kind === 'total') {
      text = `About ${number(v)} trips start here on a typical weekday.`
    } else if (measure === 'dep') {
      text = `About ${number(v, v < 10 ? 1 : 0)} trips start here in an average hour.`
    } else {
      const span = win ? win.to - win.from : 1
      const when = win ? `from ${win.range}` : `around ${hourLabel(t)}`
      const gap = Math.abs(v * span)
      const size = number(gap, gap < 10 ? 1 : 0)
      const day = dayType === 'weekday' ? 'weekday' : 'weekend day'
      text = v >= 0
        ? `About ${size} more trips end here than start here ${when}, on a typical ${day}.`
        : `About ${size} more trips start here than end here ${when}, on a typical ${day}.`
    }
    return { name: s.name, area: s.area === 'Outside Chicago' ? '' : s.area, text }
  }

  function togglePlay() {
    touched = true
    if (!playing && t >= 21.9) t = 4.5
    win = null
    playing = !playing
  }
  function scrub(value) {
    touched = true
    playing = false
    win = null
    activePeriod = null
    t = value
  }
  function pickPeriod(key) {
    touched = true
    playing = false
    activePeriod = key
    dayType = periods[key].dayType
    win = windowOf(key)
  }
  const toggleZoom = () => (zoomOverride = zoom === 'core' ? 'city' : 'core')

  // Pick the step whose card is closest to the middle of the area where text is visible.
  let stepEls = $state([])
  $effect(() => {
    let frame = 0
    const update = () => {
      frame = 0
      const narrow = window.matchMedia('(max-width: 860px)').matches
      const top = narrow ? stageEl.getBoundingClientRect().bottom : 0
      const focus = top + (window.innerHeight - top) / 2
      let best = 0
      let bestDistance = Infinity
      stepEls.forEach((el, i) => {
        if (!el) return
        const r = el.querySelector('.card').getBoundingClientRect()
        const distance = Math.abs(r.top + r.height / 2 - focus)
        if (distance < bestDistance) {
          bestDistance = distance
          best = i
        }
      })
      if (best !== untrack(() => active)) active = best
    }
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update)
    }
    update()
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', onScroll)
    return () => {
      window.removeEventListener('scroll', onScroll)
      window.removeEventListener('resize', onScroll)
      cancelAnimationFrame(frame)
    }
  })
</script>

<section class="story" aria-label="Map story">
  <div class="steps">
    {#each steps as step, i (step.id)}
      <article class="step" class:active={i === active} class:pause={step.pause} bind:this={stepEls[i]} aria-labelledby={step.title ? `h-${step.id}` : undefined}>
        <div class="card">
          {#if step.title}<h2 id="h-{step.id}">{step.title}</h2>{/if}
          {#each step.paragraphs as paragraph}<p>{paragraph}</p>{/each}
          {#if step.small}<p class="small">{step.small}</p>{/if}
        </div>
      </article>
    {/each}
  </div>

  <div class="stage" bind:this={stageEl}>
    <div class="canvas">
      <ChicagoMap
        {data}
        {values}
        {mode}
        {maxValue}
        radiusMax={kind === 'total' ? 10 : null}
        {zoom}
        highlight={highlighted ? top10 : null}
        annotations={notes}
        {label}
        {describe}
        {reduceMotion}
      />
    </div>
    <div class="panel">
      <MapLegend {mode} {kind} {highlighted} />
      <p class="zoomnote">
        {#if zoom === 'core'}
          Zoomed in on the central city, where {percent(core.tripShare)} of trips happen.
        {:else}
          Showing every station.
        {/if}
        <button type="button" onclick={toggleZoom}>{zoom === 'core' ? 'Show the whole city' : 'Zoom in'}</button>
      </p>
      {#if controls !== 'none'}
        <MapControls
          kind={controls}
          {t}
          {playing}
          {win}
          {dayType}
          {periods}
          {activePeriod}
          onplay={togglePlay}
          onscrub={scrub}
          onperiod={pickPeriod}
        />
      {/if}
      {#if showConcentration}
        <div class="chart"><ConcentrationChart starts={startsPerStation} topCount={conc.top10Count} /></div>
      {/if}
      {#if chart && dayType === 'weekday'}
        <div class="chart"><TideChart {curve} hour={chartHour} /></div>
      {/if}
    </div>
  </div>
</section>

<style>
  .story {
    display: grid;
    grid-template-columns: minmax(19rem, 27rem) minmax(0, 1fr);
    gap: 2.5rem;
    max-width: 1280px;
    margin: 0 auto;
    padding: 0 1.5rem;
  }
  .steps { grid-area: 1 / 1; padding: 22vh 0 30vh; }
  .stage {
    grid-area: 1 / 2;
    position: sticky;
    top: 0;
    align-self: start;
    height: 100vh;
    display: flex;
    gap: 1.2rem;
    padding: 1.2rem 0;
  }
  .canvas { flex: 1; min-width: 0; min-height: 0; }
  .panel { flex: none; width: 17.5rem; align-self: flex-end; display: grid; gap: 1rem; }

  .zoomnote { margin: 0; font-family: var(--sans); font-size: 0.74rem; line-height: 1.4; color: var(--ink-soft); }
  .zoomnote button {
    display: inline;
    padding: 0;
    border: 0;
    background: none;
    color: var(--ink);
    font-size: inherit;
    font-weight: 600;
    text-decoration: underline;
    cursor: pointer;
  }

  .step { min-height: 78vh; display: flex; align-items: center; }
  .card { opacity: 0.65; transition: opacity 0.4s; }
  .step.active .card { opacity: 1; }
  .card h2 { font-size: 2.1rem; margin-bottom: 0.7rem; }
  .card p { font-size: 1.15rem; }
  .step.pause { min-height: 100vh; }
  .step.pause .card p { font-size: 2.4rem; font-weight: 700; line-height: 1.15; font-style: italic; }
  .card .small { font-size: 0.95rem; color: var(--ink-soft); line-height: 1.55; }

  @media (max-width: 860px) {
    .story { grid-template-columns: minmax(0, 1fr); gap: 0; padding: 0 1.1rem; }
    .stage {
      grid-area: 1 / 1;
      z-index: 2;
      height: 52svh;
      flex-direction: column;
      gap: 0.4rem;
      padding: 0.4rem 1.1rem;
      margin: 0 -1.1rem;
      background: var(--paper);
      border-bottom: 1px solid var(--rule);
    }
    .panel { width: auto; align-self: stretch; gap: 0.45rem; }
    /* The map owns the top of the screen, so text only needs room to pass beneath it. Spacing
       between cards is padding, not a fixed height, so short lines don't leave a screen of blank. */
    .steps { grid-area: 1 / 1; position: relative; z-index: 1; padding: calc(52svh + 2svh) 0 14svh; }
    .step { min-height: 0; padding: 7svh 0; align-items: center; }
    .card h2 { font-size: 1.5rem; margin-bottom: 0.5rem; }
    .card p { font-size: 1rem; line-height: 1.45; margin-bottom: 0.7em; }
    .card .small { font-size: 0.9rem; }
    .step.pause { min-height: 0; padding: 16svh 0; }
    .step.pause .card p { font-size: 1.7rem; }
    .chart { display: none; }
  }
</style>
