/** @type {import("@sveltejs/vite-plugin-svelte").SvelteConfig} */
export default {
  compilerOptions: {
    // The data, curve and illustration props are loaded once and never change, so reading them
    // once at setup is intended. Keep this filter limited to that single warning.
    warningFilter: (warning) => warning.code !== 'state_referenced_locally',
  },
}
