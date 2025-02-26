<template>
  <div class="bg-gray-100 min-h-screen">
    <div class="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-8 border-b border-gray-200 pb-4">
        3D Fish Robotics Simulation
      </h1>
      
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <!-- Main Visualization Panel -->
        <div class="lg:col-span-2 bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
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
            <!-- Three.js scene container -->
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
        
        <!-- Swimming Parameters Panel -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100">
            <h2 class="text-xl font-semibold text-gray-800">Swimming Parameters</h2>
          </div>
          <div class="p-6">
            <!-- Frequency Control -->
            <div class="mb-6">
              <div class="flex justify-between mb-2">
                <label class="block text-sm font-medium text-gray-700">
                  Frequency
                </label>
                <span class="text-sm text-gray-500">{{ frequency.toFixed(1) }}</span>
              </div>
              <input 
                type="range" 
                min="0.1" 
                max="5.0" 
                step="0.1" 
                v-model.number="frequency" 
                @input="updateFrequency"
                class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-gray-800"
              />
              <p class="mt-1 text-xs text-gray-500">
                Controls the speed of undulation (oscillations per second)
              </p>
            </div>
            
            <!-- Amplitude Control -->
            <div class="mb-6">
              <div class="flex justify-between mb-2">
                <label class="block text-sm font-medium text-gray-700">
                  Amplitude
                </label>
                <span class="text-sm text-gray-500">{{ amplitude.toFixed(1) }}</span>
              </div>
              <input 
                type="range" 
                min="0.1" 
                max="2.0" 
                step="0.1" 
                v-model.number="amplitude" 
                @input="updateAmplitude"
                class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-gray-800"
              />
              <p class="mt-1 text-xs text-gray-500">
                Controls the maximum lateral displacement of joints
              </p>
            </div>
            
            <!-- Phase Shift Control -->
            <div class="mb-6">
              <div class="flex justify-between mb-2">
                <label class="block text-sm font-medium text-gray-700">
                  Phase Shift
                </label>
                <span class="text-sm text-gray-500">{{ phaseShift.toFixed(1) }}</span>
              </div>
              <input 
                type="range" 
                min="0.1" 
                max="1.5" 
                step="0.1" 
                v-model.number="phaseShift" 
                @input="updatePhaseShift"
                class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-gray-800"
              />
              <p class="mt-1 text-xs text-gray-500">
                Controls the wave propagation along the body
              </p>
            </div>
            
            <!-- Preset buttons -->
            <div class="mt-8">
              <h3 class="text-sm font-medium text-gray-700 mb-3">Swimming Presets</h3>
              <div class="grid grid-cols-2 gap-3">
                <button 
                  @click="applyPreset('anguilliform')" 
                  class="bg-gray-100 text-gray-800 px-3 py-2 rounded text-sm font-medium hover:bg-gray-200 transition"
                >
                  Anguilliform
                </button>
                <button 
                  @click="applyPreset('carangiform')" 
                  class="bg-gray-100 text-gray-800 px-3 py-2 rounded text-sm font-medium hover:bg-gray-200 transition"
                >
                  Carangiform
                </button>
                <button 
                  @click="applyPreset('thunniform')" 
                  class="bg-gray-100 text-gray-800 px-3 py-2 rounded text-sm font-medium hover:bg-gray-200 transition"
                >
                  Thunniform
                </button>
                <button 
                  @click="applyPreset('custom')" 
                  class="bg-gray-100 text-gray-800 px-3 py-2 rounded text-sm font-medium hover:bg-gray-200 transition"
                >
                  Custom
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Details Panel -->
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
              <span>
                <strong>Frequency</strong> determines how fast the undulation occurs
              </span>
            </li>
            <li class="flex items-start">
              <span class="inline-block w-1.5 h-1.5 rounded-full bg-gray-800 mt-1.5 mr-3 flex-shrink-0"></span>
              <span>
                <strong>Amplitude</strong> controls how far the joints move laterally
              </span>
            </li>
            <li class="flex items-start">
              <span class="inline-block w-1.5 h-1.5 rounded-full bg-gray-800 mt-1.5 mr-3 flex-shrink-0"></span>
              <span>
                <strong>Phase shift</strong> determines how the wave travels through the body
              </span>
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
    const frequency = ref(2.0);
    const amplitude = ref(0.5);
    const phaseShift = ref(0.5);
    let simulation: FishSimulation | null = null;

    onMounted(async () => {
      if (threeContainer.value) {
        // Initialize the Three.js simulation
        simulation = new FishSimulation(threeContainer.value);
        await simulation.initialize();
        
        // Initialize UI controls with values from simulation
        if (simulation) {
          frequency.value = simulation.getFrequency();
          amplitude.value = simulation.getAmplitude();
          phaseShift.value = simulation.getPhaseShift();
        }
      }
    });
    
    const toggleConnections = () => {
      if (simulation) {
        simulation.toggleConnections(showConnections.value);
      }
    };
    
    const updateFrequency = () => {
      if (simulation) {
        simulation.setFrequency(frequency.value);
      }
    };
    
    const updateAmplitude = () => {
      if (simulation) {
        simulation.setAmplitude(amplitude.value);
      }
    };
    
    const updatePhaseShift = () => {
      if (simulation) {
        simulation.setPhaseShift(phaseShift.value);
      }
    };
    
    const applyPreset = (presetName: string) => {
      if (!simulation) return;
      
      switch (presetName) {
        case 'anguilliform': // Eel-like swimming
          frequency.value = 2.0;
          amplitude.value = 0.5;
          phaseShift.value = 0.5;
          break;
        case 'carangiform': // Fish-like swimming
          frequency.value = 3.0;
          amplitude.value = 0.3;
          phaseShift.value = 0.7;
          break;
        case 'thunniform': // Tuna-like swimming
          frequency.value = 4.0;
          amplitude.value = 0.2;
          phaseShift.value = 1.0;
          break;
        case 'custom':
          // Random values for "custom" swimming pattern
          frequency.value = Math.random() * 4 + 1; // 1-5
          amplitude.value = Math.random() * 1.5 + 0.2; // 0.2-1.7
          phaseShift.value = Math.random() * 1.2 + 0.2; // 0.2-1.4
          break;
      }
      
      // Update simulation parameters
      updateFrequency();
      updateAmplitude();
      updatePhaseShift();
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
      frequency,
      amplitude,
      phaseShift,
      toggleConnections,
      updateFrequency,
      updateAmplitude,
      updatePhaseShift,
      applyPreset
    };
  }
});
</script>