<template>
    <div class="fish-robotics-container">
      <h1 class="title">Fish Robotics Joint Tracking System</h1>
      
      <div class="layout">
        <div class="simulation-panel">
          <h2>Simulation</h2>
          <canvas 
            ref="canvas" 
            width="600" 
            height="400" 
            class="simulation-canvas"
          ></canvas>
          
          <div class="button-container">
            <button 
              @click="toggleRunning" 
              :class="['control-button', running ? 'pause' : 'resume']"
            >
              {{ running ? 'Pause' : 'Resume' }}
            </button>
            
            <button 
              @click="resetSimulation" 
              class="control-button reset"
            >
              Reset
            </button>
          </div>
        </div>
        
        <div class="controls-panel">
          <h2>Controls</h2>
          
          <div class="slider-control">
            <label>
              Frequency: {{ frequency.toFixed(1) }}
            </label>
            <input 
              type="range" 
              min="0.1" 
              max="3" 
              step="0.1" 
              v-model.number="frequency" 
            />
          </div>
          
          <div class="slider-control">
            <label>
              Amplitude (degrees): {{ amplitude }}
            </label>
            <input 
              type="range" 
              min="5" 
              max="60" 
              step="1" 
              v-model.number="amplitude" 
            />
          </div>
          
          <div class="slider-control">
            <label>
              Phase Shift: {{ phaseShift.toFixed(1) }}
            </label>
            <input 
              type="range" 
              min="0.1" 
              max="1.5" 
              step="0.1" 
              v-model.number="phaseShift" 
            />
          </div>
        </div>
      </div>
      
      <div class="chart-panel">
        <h2>Joint Angle Tracking Data</h2>
        <div class="chart-container">
          <LineChart 
            :chart-data="chartData" 
            :options="chartOptions" 
          />
        </div>
      </div>
      
      <div class="notes-panel">
        <h2>Implementation Notes</h2>
        <ul>
          <li>This simulation represents the joints that would have AprilTags attached in the physical setup</li>
          <li>Red circles represent active joints (motorized/actuated)</li>
          <li>Blue circles represent passive joints (moved by the body's inertia)</li>
          <li>The graph tracks joint angles over time, which is what you would analyze from AprilTag data</li>
          <li>Adjust parameters to simulate different swimming patterns (anguilliform, carangiform, etc.)</li>
          <li>For a full 3D implementation, this could be expanded using Three.js and Rapier.js as suggested</li>
        </ul>
      </div>
    </div>
  </template>
  
  <script>
  import { ref, reactive, onMounted, onBeforeUnmount, watch } from 'vue';
  import { LineChart } from 'vue-chart-3';
  import { Chart, registerables } from 'chart.js';
  
  // Register Chart.js components
  Chart.register(...registerables);
  
  export default {
    name: 'FishTrackingSystem',
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
            backgroundColor: 'rgba(255, 0, 0, 0.2)',
            borderColor: 'rgb(255, 0, 0)',
            data: []
          },
          {
            label: 'Active Joint 2',
            backgroundColor: 'rgba(255, 102, 102, 0.2)',
            borderColor: 'rgb(255, 102, 102)',
            data: []
          },
          {
            label: 'Active Joint 3',
            backgroundColor: 'rgba(255, 170, 170, 0.2)',
            borderColor: 'rgb(255, 170, 170)',
            data: []
          },
          {
            label: 'Passive Joint 1',
            backgroundColor: 'rgba(0, 0, 255, 0.2)',
            borderColor: 'rgb(0, 0, 255)',
            data: []
          },
          {
            label: 'Passive Joint 2',
            backgroundColor: 'rgba(102, 102, 255, 0.2)',
            borderColor: 'rgb(102, 102, 255)',
            data: []
          },
          {
            label: 'Passive Joint 3',
            backgroundColor: 'rgba(170, 170, 255, 0.2)',
            borderColor: 'rgb(170, 170, 255)',
            data: []
          }
        ]
      });
      
      const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            title: {
              display: true,
              text: 'Angle (degrees)'
            }
          },
          x: {
            title: {
              display: true,
              text: 'Time (s)'
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
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.value.width, canvas.value.height);
        
        // Draw head for active system
        ctx.fillStyle = '#333';
        ctx.fillRect(10, 135, 40, 30);
        
        // Draw active joints and connections
        ctx.strokeStyle = '#666';
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
          ctx.fillStyle = '#f00'; // Red for active joints
          ctx.beginPath();
          ctx.arc(joint.x, joint.y, 8, 0, Math.PI * 2);
          ctx.fill();
          
          prevX = joint.x;
          prevY = joint.y;
        });
        
        // Draw head for passive system
        ctx.fillStyle = '#333';
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
          ctx.fillStyle = '#00f'; // Blue for passive joints
          ctx.beginPath();
          ctx.arc(joint.x, joint.y, 8, 0, Math.PI * 2);
          ctx.fill();
          
          prevX = joint.x;
          prevY = joint.y;
        });
        
        // Add labels
        ctx.fillStyle = '#000';
        ctx.font = '16px Arial';
        ctx.fillText('Active System', 10, 120);
        ctx.fillText('Passive System', 10, 270);
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
  };
  </script>
  
  <style scoped>
  .fish-robotics-container {
    font-family: Arial, sans-serif;
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    background-color: #f5f5f5;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  
  .title {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 20px;
    color: #333;
  }
  
  .layout {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  
  @media (min-width: 992px) {
    .layout {
      flex-direction: row;
    }
    
    .simulation-panel, .controls-panel {
      width: 50%;
    }
  }
  
  h2 {
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 15px;
    color: #444;
  }
  
  .simulation-panel, .controls-panel, .chart-panel, .notes-panel {
    padding: 15px;
    background-color: white;
    border-radius: 6px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
  }
  
  .simulation-canvas {
    width: 100%;
    height: auto;
    border: 1px solid #ddd;
    border-radius: 4px;
  }
  
  .button-container {
    display: flex;
    justify-content: space-between;
    margin-top: 15px;
  }
  
  .control-button {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    color: white;
    font-weight: bold;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .control-button.pause {
    background-color: #e53935;
  }
  
  .control-button.pause:hover {
    background-color: #c62828;
  }
  
  .control-button.resume {
    background-color: #43a047;
  }
  
  .control-button.resume:hover {
    background-color: #2e7d32;
  }
  
  .control-button.reset {
    background-color: #1976d2;
  }
  
  .control-button.reset:hover {
    background-color: #1565c0;
  }
  
  .slider-control {
    margin-bottom: 15px;
  }
  
  .slider-control label {
    display: block;
    margin-bottom: 5px;
    font-weight: 500;
  }
  
  .slider-control input {
    width: 100%;
  }
  
  .chart-container {
    height: 250px;
    margin-top: 10px;
  }
  
  .notes-panel ul {
    padding-left: 20px;
    line-height: 1.5;
  }
  
  .notes-panel li {
    margin-bottom: 8px;
  }
  </style>