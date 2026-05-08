import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { installVueQuery } from './plugins/vueQuery'

const app = createApp(App)
app.use(createPinia())
installVueQuery(app)
app.mount('#app')
