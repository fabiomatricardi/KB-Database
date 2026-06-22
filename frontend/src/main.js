import { createApp } from 'vue'
import PrimeVue from 'primevue/config'
import 'primeicons/primeicons.css'
import App from './App.vue'
import './styles/main.css'

const app = createApp(App)
app.use(PrimeVue)
app.mount('#app')
