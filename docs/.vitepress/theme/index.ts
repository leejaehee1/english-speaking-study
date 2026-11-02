import { h } from 'vue'
import DefaultTheme from 'vitepress/theme'
import EnglishListening from '../components/EnglishListening.vue'
import WordCompare from '../components/WordCompare.vue'
import './style.css'

export default {
  extends: DefaultTheme,
  Layout: () => h(DefaultTheme.Layout, null, {
    'doc-before': () => h(EnglishListening)
  }),
  enhanceApp({ app }) {
    app.component('WordCompare', WordCompare)
  }
}
