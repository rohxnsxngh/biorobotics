<template>
    <nav class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex">
            <div class="flex-shrink-0 flex items-center">
              <!-- Logo/Brand -->
              <span class="text-xl font-semibold text-gray-900">BioRobotics</span>
            </div>
            <div class="hidden sm:ml-6 sm:flex sm:space-x-8">
              <!-- Navigation Links -->
              <router-link 
                to="/" 
                class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                :class="{'border-gray-900 text-gray-900': $route.path === '/'}"
                exact
              >
                2D Simulation
              </router-link>
              <router-link 
                to="/3d-simulation" 
                class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                :class="{'border-gray-900 text-gray-900': $route.path === '/3d-simulation'}"
              >
                3D Simulation
              </router-link>
            </div>
          </div>
          <div class="hidden sm:ml-6 sm:flex sm:items-center">
            <!-- Right side content (if needed) -->
            <span class="text-sm text-gray-500">24755</span>
          </div>
          
          <!-- Mobile menu button -->
          <div class="flex items-center sm:hidden">
            <button 
              @click="mobileMenuOpen = !mobileMenuOpen" 
              class="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-gray-500"
              aria-expanded="false"
            >
              <span class="sr-only">Open main menu</span>
              <!-- Heroicon name: menu -->
              <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
  
      <!-- Mobile menu, show/hide based on menu state -->
      <div class="sm:hidden" v-if="mobileMenuOpen">
        <div class="pt-2 pb-3 space-y-1">
          <router-link 
            to="/" 
            class="bg-white border-transparent text-gray-500 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-700 block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
            :class="{'bg-gray-50 border-gray-900 text-gray-900': $route.path === '/'}"
            exact
            @click="mobileMenuOpen = false"
          >
            2D Simulation
          </router-link>
          <router-link 
            to="/3d-simulation" 
            class="bg-white border-transparent text-gray-500 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-700 block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
            :class="{'bg-gray-50 border-gray-900 text-gray-900': $route.path === '/3d-simulation'}"
            @click="mobileMenuOpen = false"
          >
            3D Simulation
          </router-link>
        </div>
      </div>
    </nav>
  </template>
  
  <script>
  import { ref } from 'vue';
  
  export default {
    name: 'NavBar',
    setup() {
      const mobileMenuOpen = ref(false);
      
      return {
        mobileMenuOpen
      };
    }
  };
  </script>