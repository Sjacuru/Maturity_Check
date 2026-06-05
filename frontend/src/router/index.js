import { createRouter, createWebHashHistory } from 'vue-router'
import UploadView from '../views/UploadView.vue'
import AssessmentResultView from '../views/AssessmentResultView.vue'

const routes = [
  { path: '/', component: UploadView },
  { path: '/cases/:processNumber', component: AssessmentResultView },
]

export default createRouter({
  history: createWebHashHistory(),
  routes,
})
