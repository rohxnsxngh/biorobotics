import { createRouter, createWebHistory } from 'vue-router'
import Undulation from '@/components/Undulation.vue'
import ThreeDSimulation from '@/components/3DSimulation.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: Undulation
  },
  {
    path: '/3d-simulation',
    name: 'threedSimulation',
    component: ThreeDSimulation
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router