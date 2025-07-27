import { createApp } from 'vue'
import App from './App.vue'
import { installVueQuery } from './plugins/vueQuery'

const app = createApp(App)
installVueQuery(app)
app.mount('#app')
