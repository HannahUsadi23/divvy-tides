// Loads the pipeline output and exposes small helpers for reading station values by hour.

const HOURS = 24

export async function loadData() {
  const get = (name) => fetch(`${import.meta.env.BASE_URL}data/${name}.json`).then((r) => {
    if (!r.ok) throw new Error(`Could not load ${name}.json`)
    return r.json()
  })
  const [stations, hourly, geo, methods] = await Promise.all([
    get('stations'), get('hourly'), get('geo'), get('methods'),
  ])

  const n = stations.length
  const scale = hourly.scale
  // Flatten to Float32Array [station * 24 + hour], in average trips per hour.
  const pack = (rows) => {
    const out = new Float32Array(n * HOURS)
    for (let i = 0; i < n; i++) for (let h = 0; h < HOURS; h++) out[i * HOURS + h] = rows[i][h] / scale
    return out
  }
  const series = {}
  for (const day of ['weekday', 'weekend']) {
    series[day] = {
      dep: pack(hourly[day].dep),
      depPaired: pack(hourly[day].depPaired),
      arrPaired: pack(hourly[day].arrPaired),
    }
  }
  return { stations, geo, methods, series, n, days: hourly.days }
}

// Average value per hour between `from` and `to` (fractional hours, 0-24), weighting each
// hourly bin by how much of it the window covers. Returns the average trips per hour.
export function windowRate(array, i, from, to) {
  const width = to - from
  let total = 0
  for (let h = Math.floor(from); h < Math.ceil(to); h++) {
    const overlap = Math.min(to, h + 1) - Math.max(from, h)
    if (overlap > 0) total += array[i * HOURS + ((h % HOURS) + HOURS) % HOURS] * overlap
  }
  return total / width
}

// Fills `out` with one value per station for a measure over a time window.
// measure: 'dep' | 'net'. Net = arrivals minus departures, paired trips only.
export function fillValues(out, data, { measure, dayType, from, to }) {
  const s = data.series[dayType]
  for (let i = 0; i < data.n; i++) {
    out[i] = measure === 'net'
      ? windowRate(s.arrPaired, i, from, to) - windowRate(s.depPaired, i, from, to)
      : windowRate(s.dep, i, from, to)
  }
  return out
}

// Total average trips per day for each station (used for concentration).
export function dailyTotals(data, dayType = 'weekday') {
  const s = data.series[dayType].dep
  const out = new Float32Array(data.n)
  for (let i = 0; i < data.n; i++) for (let h = 0; h < HOURS; h++) out[i] += s[i * HOURS + h]
  return out
}

// Fixed scale limits so circle sizes stay comparable while time moves.
export function robustMax(data, measure, dayType) {
  const buf = new Float32Array(data.n)
  const samples = []
  for (let h = 0; h < HOURS; h++) {
    fillValues(buf, data, { measure, dayType, from: h, to: h + 1 })
    for (let i = 0; i < data.n; i++) samples.push(Math.abs(buf[i]))
  }
  samples.sort((a, b) => a - b)
  return samples[Math.floor(samples.length * 0.9995)]
}

// Net trips over a window, summed across one community area: arrivals minus departures
// on a typical day of that type.
export function areaNet(data, area, dayType, from, to) {
  const s = data.series[dayType]
  let total = 0
  for (let i = 0; i < data.n; i++) {
    if (data.stations[i].area !== area) continue
    total += (windowRate(s.arrPaired, i, from, to) - windowRate(s.depPaired, i, from, to)) * (to - from)
  }
  return total
}

// Stations with the largest net gain and net loss over a window (trips per typical day).
export function topStations(data, dayType, from, to, k = 8) {
  const values = fillValues(new Float32Array(data.n), data, { measure: 'net', dayType, from, to })
  const rows = Array.from(values, (v, i) => ({
    name: data.stations[i].name,
    area: data.stations[i].area,
    value: v * (to - from),
  }))
  rows.sort((a, b) => b.value - a.value)
  return { gain: rows.slice(0, k), loss: rows.slice(-k).reverse() }
}
