// Illustration slots. The page looks for these files in public/illustrations/. Run
// `python pipeline/optimize_drawings.py` to make them from the full-size drawings in
// ../drawings. Anything missing is drawn in code, so the page works before you finish art.
//
// The page darkens and lights your drawings itself, so you don't draw night and day versions.

export const illustrations = {
  // Required for the opening and the closing scene.
  skyline: {
    file: 'skyline.webp',
    ratio: '2400 / 880',
    alt: 'The Chicago skyline in silhouette, windows lit.',
    brief: 'Your Chicago skyline. Transparent sky.',
  },
  sun: {
    file: 'sun.webp',
    ratio: '1 / 1',
    alt: 'The sun.',
    brief: 'Your sun, square, centered, transparent background. The page moves it across the sky.',
  },
  foreground: {
    file: 'foreground.webp',
    ratio: '1100 / 1249',
    alt: 'A rider with curly hair cycles a light-blue Divvy bike.',
    brief: 'Your biker. Transparent background, wheels touching the bottom edge.',
  },

  dock: {
    file: 'dock.webp',
    ratio: '1300 / 1241',
    alt: 'Three light-blue Divvy bikes parked at a Divvy dock.',
    brief: 'Your Divvy dock with bikes. Transparent background.',
  },

  wheels: {
    file: 'wheels.webp',
    ratio: '2 / 1',
    alt: 'Bicycle wheels reflected in rippling water.',
    brief: 'Full-bleed picture between the opening text and the map.',
  },

  // Optional: if these are missing, the page paints them in code.
  skyNight: {
    file: 'sky-night.webp',
    ratio: '16 / 9',
    alt: '',
    brief: 'Optional painted night sky, full width.',
  },
  skyDay: {
    file: 'sky-day.webp',
    ratio: '16 / 9',
    alt: '',
    brief: 'Optional painted morning sky, same size as the night sky. The two crossfade.',
  },
  skylineLit: {
    file: 'skyline-lit.webp',
    ratio: '2400 / 880',
    alt: '',
    brief: 'The lit windows, same canvas as the skyline. They sit on the buildings and fade out as the sun rises.',
  },
  rider: {
    file: 'rider-vignette.svg',
    ratio: '4 / 3',
    alt: 'A rider unlocking a Divvy bike at a station.',
    brief: 'Optional small vignette.',
  },
}

export const assetUrl = (id) => `${import.meta.env.BASE_URL}illustrations/${illustrations[id].file}`

// Resolves true if the file for this slot exists and loads.
export const hasAsset = (id) =>
  new Promise((resolve) => {
    const img = new Image()
    img.onload = () => resolve(true)
    img.onerror = () => resolve(false)
    img.src = assetUrl(id)
  })
