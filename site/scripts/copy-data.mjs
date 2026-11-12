// Copies the pipeline output into public/data so ../data stays the source of truth.
// The copy in public/data is committed, so a build still works where ../data is unavailable
// (for example, if the deploy only has the site folder).
import { cpSync, existsSync, mkdirSync, readdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const from = join(root, '..', 'data')
const to = join(root, 'public', 'data')
const required = ['stations', 'hourly', 'geo', 'methods']

if (existsSync(from)) {
  mkdirSync(to, { recursive: true })
  for (const file of readdirSync(from).filter((f) => f.endsWith('.json'))) {
    cpSync(join(from, file), join(to, file))
  }
  console.log('Copied data to public/data')
} else if (required.every((name) => existsSync(join(to, `${name}.json`)))) {
  console.log('No ../data folder; using the data already in public/data')
} else {
  console.error(`Missing data. Run pipeline/build_data.py, or add the JSON files to ${to}.`)
  process.exit(1)
}
