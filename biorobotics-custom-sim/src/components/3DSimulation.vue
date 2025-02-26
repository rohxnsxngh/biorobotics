<template>
  <div class="bg-gray-100 min-h-screen">
    <div class="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-8 border-b border-gray-200 pb-4">
        3D Fish Robotics Simulation
      </h1>
      
      <div class="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden mb-6">
        <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
          <h2 class="text-xl font-semibold text-gray-800">3D Visualization</h2>
          <div class="flex items-center space-x-4">
            <div class="flex items-center">
              <input 
                type="checkbox" 
                id="show-connections" 
                v-model="showConnections"
                @change="toggleConnections"
                class="h-4 w-4 text-gray-800 rounded border-gray-300 focus:ring-gray-700"
              >
              <label for="show-connections" class="ml-2 text-sm text-gray-600">Show Connections</label>
            </div>
            <div class="text-sm text-gray-500">
              Powered by Three.js
            </div>
          </div>
        </div>
        <div class="p-6">
          <!-- This is where our Three.js scene will be rendered -->
          <div 
            ref="threeContainer" 
            class="bg-gray-50 border border-gray-200 rounded-lg w-full" 
            style="height: 500px;"
          ></div>
          
          <div class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <h3 class="text-sm font-medium text-gray-700 mb-2">Simulation Controls</h3>
              <ul class="text-xs text-gray-600 space-y-1">
                <li>• Left-click and drag to rotate the view</li>
                <li>• Right-click and drag to pan</li>
                <li>• Scroll to zoom in/out</li>
                <li>• Toggle "Show Connections" to show/hide the connecting lines</li>
              </ul>
            </div>
            <div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <h3 class="text-sm font-medium text-gray-700 mb-2">AprilTag Simulation</h3>
              <p class="text-xs text-gray-600">
                This visualization simulates how AprilTags would track the joint movement in an anguilliform swimming pattern. The spheres represent the locations where AprilTags would be attached.
              </p>
            </div>
          </div>
        </div>
      </div>
      
      <div class="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100">
          <h2 class="text-xl font-semibold text-gray-800">Implementation Details</h2>
        </div>
        <div class="p-6">
          <ul class="space-y-2 text-sm text-gray-600">
            <li class="flex items-start">
              <span class="inline-block w-1.5 h-1.5 rounded-full bg-gray-800 mt-1.5 mr-3 flex-shrink-0"></span>
              <span>Red spheres represent active joints that generate propulsive forces</span>
            </li>
            <li class="flex items-start">
              <span class="inline-block w-1.5 h-1.5 rounded-full bg-gray-800 mt-1.5 mr-3 flex-shrink-0"></span>
              <span>Blue spheres represent passive joints that respond to water forces</span>
            </li>
            <li class="flex items-start">
              <span class="inline-block w-1.5 h-1.5 rounded-full bg-gray-800 mt-1.5 mr-3 flex-shrink-0"></span>
              <span>Sinusoidal forces create the undulating motion typical of anguilliform swimming</span>
            </li>
            <li class="flex items-start">
              <span class="inline-block w-1.5 h-1.5 rounded-full bg-gray-800 mt-1.5 mr-3 flex-shrink-0"></span>
              <span>Black lines represent the connections between joints and can be toggled on/off</span>
            </li>
            <li class="flex items-start">
              <span class="inline-block w-1.5 h-1.5 rounded-full bg-gray-800 mt-1.5 mr-3 flex-shrink-0"></span>
              <span>In the physical implementation, AprilTags would be attached to each joint for tracking</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onBeforeUnmount } from 'vue';
import { FishSimulation } from '../script/index';

export default defineComponent({
  name: 'ThreeDSimulation',
  setup() {
    const threeContainer = ref<HTMLElement | null>(null);
    const showConnections = ref(true);
    let simulation: FishSimulation | null = null;

    onMounted(async () => {
      if (threeContainer.value) {
        // Initialize the Three.js simulation
        simulation = new FishSimulation(threeContainer.value);
        await simulation.initialize();
      }
    });
    
    const toggleConnections = () => {
      if (simulation) {
        simulation.toggleConnections(showConnections.value);
      }
    };

    onBeforeUnmount(() => {
      // Clean up resources when component is unmounted
      if (simulation) {
        simulation.dispose();
        simulation = null;
      }
    });

    return {
      threeContainer,
      showConnections,
      toggleConnections
    };
  }
});
</script>