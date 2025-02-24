<template>
    <div class="bg-gray-100 min-h-screen">
      <div class="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-8 border-b border-gray-200 pb-4">
          Fish Robotics Joint Tracking System
        </h1>
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <!-- Simulation Panel -->
          <div class="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-100">
              <h2 class="text-xl font-semibold text-gray-800">Simulation</h2>
            </div>
            <div class="p-6">
              <canvas 
                ref="canvas" 
                width="600" 
                height="400" 
                class="w-full border border-gray-200 rounded"
              ></canvas>
              
              <div class="flex justify-between mt-6">
                <button 
                  @click="toggleRunning" 
                  :class="[
                    'px-5 py-2 rounded-md text-sm font-medium shadow-sm transition-colors',
                    running 
                      ? 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500' 
                      : 'bg-green-600 text-white hover:bg-green-700 focus:ring-green-500'
                  ]"
                >
                  {{ running ? 'Pause' : 'Resume' }}
                </button>
                
                <button 
                  @click="resetSimulation" 
                  class="px-5 py-2 bg-gray-800 text-white rounded-md text-sm font-medium shadow-sm hover:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-700 transition-colors"
                >
                  Reset
                </button>
              </div>
            </div>
          </div>
          
          <!-- Controls Panel -->
          <div class="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-100">
              <h2 class="text-xl font-semibold text-gray-800">Controls</h2>
            </div>
            <div class="p-6">
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
                  max="3" 
                  step="0.1" 
                  v-model.number="frequency" 
                  class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-gray-800"
                />
              </div>
              
              <div class="mb-6">
                <div class="flex justify-between mb-2">
                  <label class="block text-sm font-medium text-gray-700">
                    Amplitude (degrees)
                  </label>
                  <span class="text-sm text-gray-500">{{ amplitude }}</span>
                </div>
                <input 
                  type="range" 
                  min="5" 
                  max="60" 
                  step="1" 
                  v-model.number="amplitude" 
                  class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-gray-800"
                />
              </div>
              
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
                  class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-gray-800"
                />
              </div>
  
              <div class="mt-8 p-4 bg-gray-50 rounded border border-gray-200">
                <h3 class="text-sm font-medium text-gray-700 mb-2">Joint System Legend</h3>
                <div class="flex items-center space-x-6">
                  <div class="flex items-center">
                    <span class="inline-block w-3 h-3 rounded-full bg-red-600 mr-2"></span>
                    <span class="text-xs text-gray-600">Active Joint</span>
                  </div>
                  <div class="flex items-center">
                    <span class="inline-block w-3 h-3 rounded-full bg-blue-600 mr-2"></span>
                    <span class="text-xs text-gray-600">Passive Joint</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Chart Panel -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden mb-6">
          <div class="px-6 py-4 border-b border-gray-100">
            <h2 class="text-xl font-semibold text-gray-800">Joint Angle Tracking Data</h2>
          </div>
          <div class="p-6">
            <div class="h-64">
              <LineChart 
                :chart-data="chartData" 
                :options="chartOptions" 
              />
            </div>
          </div>
        </div>
        
        <!-- Notes Panel -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100">
            <h2 class="text-xl font-semibold text-gray-800">Implementation Notes</h2>
          </div>
          <div class="p-6">
            <ul class="space-y-2 text-sm text-gray-600">
              <li class="flex items-start">
                <span class="inline-block w-1.5 h-1.5 rounded-full bg-gray-800 mt-1.5 mr-3 flex-shrink-0"></span>
                <span>This simulation represents the joints that would have AprilTags attached in the physical setup</span>
              </li>
              <li class="flex items-start">
                <span class="inline-block w-1.5 h-1.5 rounded-full bg-gray-800 mt-1.5 mr-3 flex-shrink-0"></span>
                <span>Red circles represent active joints (motorized/actuated)</span>
              </li>
              <li class="flex items-start">
                <span class="inline-block w-1.5 h-1.5 rounded-full bg-gray-800 mt-1.5 mr-3 flex-shrink-0"></span>
                <span>Blue circles represent passive joints (moved by the body's inertia)</span>
              </li>
              <li class="flex items-start">
                <span class="inline-block w-1.5 h-1.5 rounded-full bg-gray-800 mt-1.5 mr-3 flex-shrink-0"></span>
                <span>The graph tracks joint angles over time, which is what you would analyze from AprilTag data</span>
              </li>
              <li class="flex items-start">
                <span class="inline-block w-1.5 h-1.5 rounded-full bg-gray-800 mt-1.5 mr-3 flex-shrink-0"></span>
                <span>Adjust parameters to simulate different swimming patterns (anguilliform, carangiform, etc.)</span>
              </li>
              <li class="flex items-start">
                <span class="inline-block w-1.5 h-1.5 rounded-full bg-gray-800 mt-1.5 mr-3 flex-shrink-0"></span>
                <span>For a full 3D implementation, this could be expanded using Three.js and Rapier.js as suggested</span>
              </li>
            </ul>
          </div>
        </div>
  
        <!-- Footer -->
        <div class="mt-8 text-center text-xs text-gray-400">
          <p>Biorobotics Fish Locomotion Tracking System • v1.0</p>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { ref, reactive, onMounted, onBeforeUnmount, watch, defineComponent } from 'vue';
  import { LineChart } from 'vue-chart-3';
  import { Chart, registerables } from 'chart.js';
  
  // Register Chart.js components
  Chart.register(...registerables);
  
  export default defineComponent({
    name: 'Undulation',
    components: {
      LineChart
    },
    setup() {
      // State variables
      const activeJoints = ref([]);
      const passiveJoints = ref([]);
      const time = ref(0);
      const running = ref(true);
      const frequency = ref(1);
      const amplitude = ref(30);
      const phaseShift = ref(0.5);
      const trackingData = ref([]);
      const numJoints = 5;
      const canvas = ref(null);
      let animationInterval = null;
      
      // Chart data
      const chartData = reactive({
        labels: [],
        datasets: [
          {
            label: 'Active Joint 1',
            backgroundColor: 'rgba(220, 38, 38, 0.1)',
            borderColor: 'rgb(220, 38, 38)',
            borderWidth: 2,
            pointRadius: 1,
            tension: 0.4,
            data: []
          },
          {
            label: 'Active Joint 2',
            backgroundColor: 'rgba(220, 38, 38, 0.05)',
            borderColor: 'rgb(239, 68, 68)',
            borderWidth: 2,
            pointRadius: 1,
            tension: 0.4,
            data: []
          },
          {
            label: 'Active Joint 3',
            backgroundColor: 'rgba(220, 38, 38, 0.02)',
            borderColor: 'rgb(248, 113, 113)',
            borderWidth: 2,
            pointRadius: 1,
            tension: 0.4,
            data: []
          },
          {
            label: 'Passive Joint 1',
            backgroundColor: 'rgba(37, 99, 235, 0.1)',
            borderColor: 'rgb(37, 99, 235)',
            borderWidth: 2,
            pointRadius: 1,
            tension: 0.4,
            data: []
          },
          {
            label: 'Passive Joint 2',
            backgroundColor: 'rgba(37, 99, 235, 0.05)',
            borderColor: 'rgb(59, 130, 246)',
            borderWidth: 2,
            pointRadius: 1,
            tension: 0.4,
            data: []
          },
          {
            label: 'Passive Joint 3',
            backgroundColor: 'rgba(37, 99, 235, 0.02)',
            borderColor: 'rgb(96, 165, 250)',
            borderWidth: 2,
            pointRadius: 1,
            tension: 0.4,
            data: []
          }
        ]
      });
      
      const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          legend: {
            position: 'top',
            labels: {
              boxWidth: 12,
              usePointStyle: true,
              pointStyle: 'circle'
            }
          },
          tooltip: {
            backgroundColor: 'rgba(17, 24, 39, 0.9)',
            titleColor: 'rgb(243, 244, 246)',
            bodyColor: 'rgb(209, 213, 219)',
            borderColor: 'rgba(107, 114, 128, 0.3)',
            borderWidth: 1,
            cornerRadius: 4,
            displayColors: true,
            usePointStyle: true,
          }
        },
        scales: {
          y: {
            title: {
              display: true,
              text: 'Angle (degrees)',
              color: '#6B7280'
            },
            grid: {
              color: 'rgba(243, 244, 246, 0.8)',
              borderDash: [3, 3]
            },
            ticks: {
              color: '#6B7280'
            }
          },
          x: {
            title: {
              display: true,
              text: 'Time (s)',
              color: '#6B7280'
            },
            grid: {
              display: false
            },
            ticks: {
              color: '#6B7280'
            }
          }
        }
      };
  
      // Start simulation timer
      const startSimulation = () => {
        stopSimulation();
        animationInterval = setInterval(() => {
          if (running.value) {
            time.value += 0.1;
            calculateJointPositions();
          }
        }, 100);
      };
      
      // Stop simulation timer
      const stopSimulation = () => {
        if (animationInterval) {
          clearInterval(animationInterval);
        }
      };
      
      // Toggle running state
      const toggleRunning = () => {
        running.value = !running.value;
      };
      
      // Reset simulation
      const resetSimulation = () => {
        time.value = 0;
        trackingData.value = [];
        updateChartData();
      };
      
      // Calculate joint positions based on parameters
      const calculateJointPositions = () => {
        const newActiveJoints = [];
        const newPassiveJoints = [];
        
        // Calculate positions for active joints (with powered motion)
        for (let i = 0; i < numJoints; i++) {
          const phase = phaseShift.value * i;
          const angle = amplitude.value * Math.sin(frequency.value * time.value + phase);
          
          // Starting position of the first joint relative to "head"
          let x = 50;
          let y = 150;
          
          // Calculate position based on previous joints
          for (let j = 0; j <= i; j++) {
            const segmentPhase = phaseShift.value * j;
            const segmentAngle = amplitude.value * Math.sin(frequency.value * time.value + segmentPhase);
            
            // Skip the first calculation for the head position
            if (j === 0) {
              x += 40 * Math.cos(segmentAngle * Math.PI / 180);
              y += 40 * Math.sin(segmentAngle * Math.PI / 180);
            } else {
              x += 40 * Math.cos(segmentAngle * Math.PI / 180);
              y += 40 * Math.sin(segmentAngle * Math.PI / 180);
            }
          }
          
          newActiveJoints.push({ x, y, angle });
        }
        
        // Calculate positions for passive joints (respond to environment/flow)
        for (let i = 0; i < numJoints; i++) {
          const phase = phaseShift.value * i;
          // Passive joints have reduced amplitude and delayed response
          const angle = (amplitude.value * 0.7) * Math.sin(frequency.value * time.value * 0.8 + phase);
          
          let x = 50;
          let y = 300; // Position the passive system below the active one
          
          for (let j = 0; j <= i; j++) {
            const segmentPhase = phaseShift.value * j;
            const segmentAngle = (amplitude.value * 0.7) * Math.sin(frequency.value * time.value * 0.8 + segmentPhase);
            
            if (j === 0) {
              x += 40 * Math.cos(segmentAngle * Math.PI / 180);
              y += 40 * Math.sin(segmentAngle * Math.PI / 180);
            } else {
              x += 40 * Math.cos(segmentAngle * Math.PI / 180);
              y += 40 * Math.sin(segmentAngle * Math.PI / 180);
            }
          }
          
          newPassiveJoints.push({ x, y, angle });
        }
        
        activeJoints.value = newActiveJoints;
        passiveJoints.value = newPassiveJoints;
        
        // Record data for the chart (approximately every second)
        if (time.value % 1 < 0.1) {
          const newDataPoint = {
            time: time.value.toFixed(1),
            activeJoint1: newActiveJoints[0]?.angle.toFixed(1) || 0,
            activeJoint2: newActiveJoints[1]?.angle.toFixed(1) || 0,
            activeJoint3: newActiveJoints[2]?.angle.toFixed(1) || 0,
            passiveJoint1: newPassiveJoints[0]?.angle.toFixed(1) || 0,
            passiveJoint2: newPassiveJoints[1]?.angle.toFixed(1) || 0,
            passiveJoint3: newPassiveJoints[2]?.angle.toFixed(1) || 0,
          };
          
          trackingData.value.push(newDataPoint);
          
          // Keep only the last 20 data points
          if (trackingData.value.length > 20) {
            trackingData.value = trackingData.value.slice(trackingData.value.length - 20);
          }
          
          updateChartData();
        }
      };
      
      // Draw the fish on canvas
      const drawCanvas = () => {
        if (!canvas.value) return;
        
        const ctx = canvas.value.getContext('2d');
        
        // Clear canvas with light background
        ctx.fillStyle = '#FAFAFA';
        ctx.fillRect(0, 0, canvas.value.width, canvas.value.height);
        
        // Draw head for active system
        ctx.fillStyle = '#1F2937';
        ctx.fillRect(10, 135, 40, 30);
        
        // Draw active joints and connections
        ctx.strokeStyle = '#4B5563';
        ctx.lineWidth = 5;
        
        // Starting point (head)
        let prevX = 50;
        let prevY = 150;
        
        // Draw joints and connections
        activeJoints.value.forEach((joint, index) => {
          // Draw connection
          ctx.beginPath();
          ctx.moveTo(prevX, prevY);
          ctx.lineTo(joint.x, joint.y);
          ctx.stroke();
          
          // Draw joint
          ctx.fillStyle = '#DC2626'; // Red for active joints
          ctx.beginPath();
          ctx.arc(joint.x, joint.y, 8, 0, Math.PI * 2);
          ctx.fill();
          
          prevX = joint.x;
          prevY = joint.y;
        });
        
        // Draw head for passive system
        ctx.fillStyle = '#1F2937';
        ctx.fillRect(10, 285, 40, 30);
        
        // Draw passive joints and connections
        prevX = 50;
        prevY = 300;
        
        passiveJoints.value.forEach((joint, index) => {
          // Draw connection
          ctx.beginPath();
          ctx.moveTo(prevX, prevY);
          ctx.lineTo(joint.x, joint.y);
          ctx.stroke();
          
          // Draw joint
          ctx.fillStyle = '#2563EB'; // Blue for passive joints
          ctx.beginPath();
          ctx.arc(joint.x, joint.y, 8, 0, Math.PI * 2);
          ctx.fill();
          
          prevX = joint.x;
          prevY = joint.y;
        });
        
        // Add labels with more modern styling
        ctx.fillStyle = '#1F2937';
        ctx.font = '14px Inter, system-ui, sans-serif';
        ctx.fillText('Active System', 10, 120);
        ctx.fillText('Passive System', 10, 270);
        
        // Add time display
        ctx.fillStyle = '#6B7280';
        ctx.font = '12px Inter, system-ui, sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(`Time: ${time.value.toFixed(1)}s`, canvas.value.width - 10, 20);
        ctx.textAlign = 'left';
      };
      
      // Update chart data from tracking data
      const updateChartData = () => {
        // Update labels (time values)
        chartData.labels = trackingData.value.map(item => item.time);
        
        // Update datasets
        chartData.datasets[0].data = trackingData.value.map(item => parseFloat(item.activeJoint1));
        chartData.datasets[1].data = trackingData.value.map(item => parseFloat(item.activeJoint2));
        chartData.datasets[2].data = trackingData.value.map(item => parseFloat(item.activeJoint3));
        chartData.datasets[3].data = trackingData.value.map(item => parseFloat(item.passiveJoint1));
        chartData.datasets[4].data = trackingData.value.map(item => parseFloat(item.passiveJoint2));
        chartData.datasets[5].data = trackingData.value.map(item => parseFloat(item.passiveJoint3));
      };
      
      // Lifecycle hooks
      onMounted(() => {
        startSimulation();
        
        // Initial drawing
        calculateJointPositions();
        drawCanvas();
        
        // Set up window resize listener
        window.addEventListener('resize', drawCanvas);
      });
      
      onBeforeUnmount(() => {
        stopSimulation();
        window.removeEventListener('resize', drawCanvas);
      });
      
      // Watchers
      watch([activeJoints, passiveJoints], () => {
        drawCanvas();
      });
      
      return {
        canvas,
        activeJoints,
        passiveJoints,
        time,
        running,
        frequency,
        amplitude,
        phaseShift,
        trackingData,
        chartData,
        chartOptions,
        toggleRunning,
        resetSimulation
      };
    }
  });
  </script>