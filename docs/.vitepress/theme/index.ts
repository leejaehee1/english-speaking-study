import { h } from 'vue'
import DefaultTheme from 'vitepress/theme'
import EnglishListening from '../components/EnglishListening.vue'
import WordCompare from '../components/WordCompare.vue'
import SoundBlockTrainer from '../components/SoundBlockTrainer.vue'
import KFoodYoutubeStudio from '../components/KFoodYoutubeStudio.vue'
import './style.css'

export default {
  extends: DefaultTheme,
  Layout: () => h(DefaultTheme.Layout, null, {
    'doc-before': () => h(EnglishListening)
  }),
  enhanceApp({ app }) {
    app.component('WordCompare', WordCompare)
    app.component('SoundBlockTrainer', SoundBlockTrainer)
    app.component('KFoodYoutubeStudio', KFoodYoutubeStudio)
  }
}
