/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      "colors": {
              "secondary-fixed-dim": "#74dd6e",
              "background": "#fcf9f8",
              "surface-container": "#f0eded",
              "primary-fixed": "#ffe08f",
              "surface-dim": "#dcd9d9",
              "on-primary-fixed": "#241a00",
              "tertiary-fixed": "#aeecff",
              "error": "#ba1a1a",
              "outline-variant": "#d1c5ae",
              "secondary-fixed": "#8ffb87",
              "on-primary-fixed-variant": "#584400",
              "on-error-container": "#93000a",
              "surface-tint": "#755b00",
              "outline": "#7f7662",
              "on-tertiary-fixed-variant": "#004e5d",
              "primary-fixed-dim": "#edc13d",
              "secondary-container": "#8ffb87",
              "surface-bright": "#fcf9f8",
              "on-tertiary": "#ffffff",
              "on-secondary": "#ffffff",
              "on-secondary-container": "#007518",
              "on-error": "#ffffff",
              "surface-container-lowest": "#ffffff",
              "on-tertiary-fixed": "#001f26",
              "tertiary-fixed-dim": "#58d6f5",
              "on-surface-variant": "#4e4634",
              "on-primary-container": "#6e5600",
              "surface-container-highest": "#e5e2e1",
              "surface": "#fcf9f8",
              "surface-variant": "#e5e2e1",
              "tertiary": "#00687b",
              "error-container": "#ffdad6",
              "primary-container": "#f8cb46",
              "on-secondary-fixed": "#002203",
              "on-primary": "#ffffff",
              "on-secondary-fixed-variant": "#00530e",
              "on-surface": "#1b1b1c",
              "surface-container-low": "#f6f3f2",
              "inverse-primary": "#edc13d",
              "primary": "#755b00",
              "on-background": "#1b1b1c",
              "secondary": "#006e16",
              "inverse-surface": "#303030",
              "inverse-on-surface": "#f3f0ef",
              "surface-container-high": "#eae7e7",
              "tertiary-container": "#64e0ff",
              "on-tertiary-container": "#006274",
              "status-green": "#0C831F"
      },
      "borderRadius": {
              "DEFAULT": "0.25rem",
              "lg": "0.5rem",
              "xl": "0.75rem",
              "full": "9999px"
      },
      "spacing": {
              "card-padding": "20px",
              "stack-gap": "12px",
              "gutter": "16px",
              "container-margin": "24px",
              "sidebar-width": "260px"
      },
      "fontFamily": {
              "body-sm": [
                      "Inter", "sans-serif"
              ],
              "data-tabular": [
                      "Inter", "sans-serif"
              ],
              "label-caps": [
                      "Inter", "sans-serif"
              ],
              "display-lg": [
                      "Inter", "sans-serif"
              ],
              "headline-md": [
                      "Inter", "sans-serif"
              ],
              "body-md": [
                      "Inter", "sans-serif"
              ],
              "title-sm": [
                      "Inter", "sans-serif"
              ]
      },
      "fontSize": {
              "body-sm": [
                      "13px",
                      {
                              "lineHeight": "18px",
                              "fontWeight": "400"
                      }
              ],
              "data-tabular": [
                      "14px",
                      {
                              "lineHeight": "20px",
                              "fontWeight": "500"
                      }
              ],
              "label-caps": [
                      "11px",
                      {
                              "lineHeight": "16px",
                              "letterSpacing": "0.05em",
                              "fontWeight": "600"
                      }
              ],
              "display-lg": [
                      "32px",
                      {
                              "lineHeight": "40px",
                              "letterSpacing": "-0.02em",
                              "fontWeight": "700"
                      }
              ],
              "headline-md": [
                      "24px",
                      {
                              "lineHeight": "32px",
                              "letterSpacing": "-0.01em",
                              "fontWeight": "600"
                      }
              ],
              "body-md": [
                      "14px",
                      {
                              "lineHeight": "20px",
                              "fontWeight": "400"
                      }
              ],
              "title-sm": [
                      "18px",
                      {
                              "lineHeight": "24px",
                              "fontWeight": "600"
                      }
              ]
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/container-queries')
  ],
}
