import { createApp } from 'vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import router from './router'
import App from './App.vue'

// Institutional palette sampled directly from docs/logo_tcmrio_horizontal.png
// (navy #092F57, teal #3896B4) — the same two-tone identity used on the
// PPP Maturity Check report artifacts, so the app and its reports read as
// one system.
const tcmrio = {
  dark: false,
  colors: {
    background: '#F3F6F5',
    surface: '#FFFFFF',
    'surface-variant': '#E8EEED',
    primary: '#092F57',
    'primary-darken-1': '#061F3B',
    secondary: '#3896B4',
    'secondary-darken-1': '#2C7690',
    error: '#A23B3B',
    warning: '#9C6B0A',
    success: '#1E7A4C',
    info: '#3896B4',
  },
}

const vuetify = createVuetify({
  components,
  directives,
  icons: { defaultSet: 'mdi' },
  theme: {
    defaultTheme: 'tcmrio',
    themes: { tcmrio },
  },
})

createApp(App).use(vuetify).use(router).mount('#app')
