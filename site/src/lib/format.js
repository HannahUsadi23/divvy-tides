export function clock(hour) {
  const h = Math.floor(hour) % 24
  const m = Math.floor((hour - Math.floor(hour)) * 60)
  const suffix = h < 12 ? 'am' : 'pm'
  return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${suffix}`
}

export function hourLabel(hour) {
  const h = Math.floor(hour) % 24
  return `${h % 12 || 12} ${h < 12 ? 'am' : 'pm'}`
}

export const number = (value, digits = 0) =>
  value.toLocaleString('en-US', { maximumFractionDigits: digits, minimumFractionDigits: digits })

export const percent = (value, digits = 0) => `${number(value * 100, digits)}%`
