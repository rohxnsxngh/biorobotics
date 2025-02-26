<template>
  <div class="bg-gray-100 min-h-screen">
    <div class="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
      <h1
        class="text-3xl font-bold text-gray-900 mb-8 border-b border-gray-200 pb-4"
      >
        3D Fish Robotics Simulation with AprilTag Tracking
      </h1>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <!-- Main Visualization Panel -->
        <div
          class="lg:col-span-2 bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden"
        >
          <div
            class="px-6 py-4 border-b border-gray-100 flex justify-between items-center"
          >
            <h2 class="text-xl font-semibold text-gray-800">
              3D Visualization
            </h2>
            <div class="flex items-center space-x-4">
              <div class="flex items-center">
                <input
                  type="checkbox"
                  id="show-connections"
                  v-model="showConnections"
                  @change="toggleConnections"
                  class="h-4 w-4 text-gray-800 rounded border-gray-300 focus:ring-gray-700"
                />
                <label for="show-connections" class="ml-2 text-sm text-gray-600"
                  >Show Connections</label
                >
              </div>
              <div class="text-sm text-gray-500">AutoBots</div>
            </div>
          </div>
          <div class="p-6">
            <!-- Three.js scene container -->
            <div
              ref="threeContainer"
              class="bg-gray-50 border border-gray-200 rounded-lg w-full"
              style="height: 500px"
            ></div>

            <div class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <h3 class="text-sm font-medium text-gray-700 mb-2">
                  Simulation Controls
                </h3>
                <ul class="text-xs text-gray-600 space-y-1">
                  <li>• Left-click and drag to rotate the view</li>
                  <li>• Right-click and drag to pan</li>
                  <li>• Scroll to zoom in/out</li>
                  <li>
                    • Toggle "Show Connections" to show/hide the connecting
                    lines
                  </li>
                </ul>
              </div>
              <div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <h3 class="text-sm font-medium text-gray-700 mb-2">
                  AprilTag Simulation
                </h3>
                <p class="text-xs text-gray-600">
                  The top-down camera view shows simulated AprilTags attached to
                  each joint, similar to how you would track motion in a
                  physical implementation.
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Swimming Parameters Panel -->
        <div
          class="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden"
        >
          <div class="px-6 py-4 border-b border-gray-100">
            <h2 class="text-xl font-semibold text-gray-800">
              Swimming Parameters
            </h2>
          </div>
          <div class="p-6">
            <!-- Frequency Control -->
            <div class="mb-6">
              <div class="flex justify-between mb-2">
                <label class="block text-sm font-medium text-gray-700">
                  Frequency
                </label>
                <span class="text-sm text-gray-500">{{
                  frequency.toFixed(1)
                }}</span>
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
                <span class="text-sm text-gray-500">{{
                  amplitude.toFixed(1)
                }}</span>
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
                <span class="text-sm text-gray-500">{{
                  phaseShift.toFixed(1)
                }}</span>
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
              <h3 class="text-sm font-medium text-gray-700 mb-3">
                Swimming Presets
              </h3>
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

      <!-- AprilTag Camera View Panel -->
      <div
        class="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden mb-6"
      >
        <div
          class="px-6 py-4 border-b border-gray-100 flex justify-between items-center"
        >
          <h2 class="text-xl font-semibold text-gray-800">
            AprilTag Camera View
          </h2>
          <div class="text-sm text-gray-500 flex items-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4 mr-1"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            Top-Down View
          </div>
        </div>
        <div class="p-6">
          <!-- AprilTag camera view container -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
            <div class="md:col-span-2">
              <div
                ref="tagContainer"
                class="bg-gray-900 border border-gray-800 rounded-lg w-full overflow-hidden"
                style="height: 280px"
              ></div>
            </div>
            <div
              class="bg-gray-50 p-4 rounded-lg border border-gray-200 h-full"
            >
              <h3 class="text-sm font-medium text-gray-700 mb-2">
                AprilTag Tracking Info
              </h3>
              <div class="space-y-2">
                <div class="text-xs text-gray-600">
                  <span class="font-medium">Tags Detected:</span>
                  {{ aprilTagsDetected }} / 6
                </div>
                <div class="text-xs text-gray-600">
                  <span class="font-medium">Camera FPS:</span>
                  {{ cameraFps.toFixed(1) }}
                </div>
                <div class="text-xs text-gray-600">
                  <span class="font-medium">Tracking Status:</span>
                  <span
                    class="ml-1 px-2 py-0.5 text-xs rounded"
                    :class="
                      trackingStatus === 'Good'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-yellow-100 text-yellow-800'
                    "
                  >
                    {{ trackingStatus }}
                  </span>
                </div>
                <div class="mt-4">
                  <h4 class="text-xs font-medium text-gray-700 mb-1">
                    Joint Positions:
                  </h4>
                  <div class="text-xs text-gray-600 space-y-1">
                    <div v-for="(pos, index) in jointPositions" :key="index">
                      <span class="font-mono"
                        >Tag {{ index }}: x={{ pos.x.toFixed(2) }}, z={{
                          pos.z.toFixed(2)
                        }}</span
                      >
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div
              class="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden mt-6"
              v-if="isStreaming && streamingStats.connected"
            >
              <div
                class="px-6 py-4 border-b border-gray-100 flex justify-between items-center"
              >
                <h2 class="text-xl font-semibold text-gray-800">
                  Backend Processed View
                </h2>
                <div class="text-sm text-gray-500 flex items-center">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-4 w-4 mr-1"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                  Refreshing ({{ fetchImageInterval }}ms)
                </div>
              </div>
              <div class="p-6">
                <div class="max-w-full overflow-hidden">
                  <img
                    v-if="processedImage"
                    :src="processedImage"
                    alt="Processed Camera View"
                    class="w-full rounded-lg border border-gray-200"
                  />
                  <div
                    v-else
                    class="bg-gray-100 h-64 rounded-lg border border-gray-200 flex items-center justify-center text-gray-400"
                  >
                    Loading processed image...
                  </div>
                </div>

                <div
                  class="mt-4 bg-gray-50 p-4 rounded-lg border border-gray-200"
                >
                  <h3 class="text-sm font-medium text-gray-700 mb-2">
                    Debug Information
                  </h3>
                  <p class="text-xs text-gray-600">
                    This view shows the real-time image being processed by your
                    Python backend. Green boxes indicate detected AprilTags. If
                    no tags are detected, you might need to:
                  </p>
                  <ul
                    class="mt-2 text-xs text-gray-600 space-y-1 list-disc pl-5"
                  >
                    <li>
                      Adjust the AprilTag detection parameters in your Python
                      backend
                    </li>
                    <li>
                      Check if the image data is being transmitted correctly
                    </li>
                    <li>
                      Verify that the lighting and contrast in the simulated
                      view are adequate for detection
                    </li>
                  </ul>
                  <div class="mt-2">
                    <button
                      @click="refreshProcessedImage"
                      class="px-3 py-1.5 text-xs font-medium bg-gray-800 text-white rounded hover:bg-gray-700"
                    >
                      Refresh Image Now
                    </button>
                  </div>
                </div>
              </div>
            </div>
            <div class="mt-4">
              <h4 class="text-xs font-medium text-gray-700 mb-2">
                Python Backend Streaming
              </h4>

              <div class="mb-2">
                <label class="block text-xs font-medium text-gray-600 mb-1"
                  >Backend URL:</label
                >
                <input
                  type="text"
                  v-model="backendUrl"
                  class="w-full text-xs p-1 border border-gray-300 rounded"
                  placeholder="http://localhost:5000"
                />
              </div>

              <button
                @click="toggleStreaming"
                class="w-full px-3 py-1.5 text-xs font-medium rounded"
                :class="
                  isStreaming
                    ? 'bg-red-600 text-white hover:bg-red-700'
                    : 'bg-green-600 text-white hover:bg-green-700'
                "
              >
                {{ isStreaming ? "Stop Streaming" : "Start Streaming" }}
              </button>

              <div class="mt-2 space-y-1" v-if="isStreaming">
                <div class="flex justify-between text-xs">
                  <span class="text-gray-600">Connection:</span>
                  <span
                    :class="
                      streamingStats.connected
                        ? 'text-green-600'
                        : 'text-red-600'
                    "
                  >
                    {{
                      streamingStats.connected ? "Connected" : "Disconnected"
                    }}
                  </span>
                </div>

                <div
                  class="flex justify-between text-xs"
                  v-if="streamingStats.connected"
                >
                  <span class="text-gray-600">Backend FPS:</span>
                  <span class="text-gray-800">{{
                    streamingStats.fps.toFixed(1)
                  }}</span>
                </div>

                <div
                  class="flex justify-between text-xs"
                  v-if="streamingStats.connected"
                >
                  <span class="text-gray-600">Tags Detected:</span>
                  <span class="text-gray-800">{{
                    streamingStats.detectedTags.length
                  }}</span>
                </div>

                <div
                  class="text-xs text-red-600"
                  v-if="streamingStats.lastError"
                >
                  Error: {{ streamingStats.lastError }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Details Panel -->
      <div
        class="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden"
      >
        <div class="px-6 py-4 border-b border-gray-100">
          <h2 class="text-xl font-semibold text-gray-800">
            Implementation Details
          </h2>
        </div>
        <div class="p-6">
          <ul class="space-y-2 text-sm text-gray-600">
            <li class="flex items-start">
              <span
                class="inline-block w-1.5 h-1.5 rounded-full bg-gray-800 mt-1.5 mr-3 flex-shrink-0"
              ></span>
              <span
                >Red spheres represent active joints that generate propulsive
                forces</span
              >
            </li>
            <li class="flex items-start">
              <span
                class="inline-block w-1.5 h-1.5 rounded-full bg-gray-800 mt-1.5 mr-3 flex-shrink-0"
              ></span>
              <span
                >Blue spheres represent passive joints that respond to water
                forces</span
              >
            </li>
            <li class="flex items-start">
              <span
                class="inline-block w-1.5 h-1.5 rounded-full bg-gray-800 mt-1.5 mr-3 flex-shrink-0"
              ></span>
              <span>
                The AprilTag camera view simulates what an overhead camera would
                see when tracking the physical system
              </span>
            </li>
            <li class="flex items-start">
              <span
                class="inline-block w-1.5 h-1.5 rounded-full bg-gray-800 mt-1.5 mr-3 flex-shrink-0"
              ></span>
              <span>
                In a real implementation, AprilTags would be printed and
                attached to each joint for tracking
              </span>
            </li>
            <li class="flex items-start">
              <span
                class="inline-block w-1.5 h-1.5 rounded-full bg-gray-800 mt-1.5 mr-3 flex-shrink-0"
              ></span>
              <span>
                The simulation includes realistic tracking features like
                occasional missed detections and measurement noise
              </span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import {
  defineComponent,
  ref,
  onMounted,
  onBeforeUnmount,
  reactive,
} from "vue";
import { FishSimulation } from "../script/index";

export default defineComponent({
  name: "ThreeDSimulation",
  setup() {
    const threeContainer = ref<HTMLElement | null>(null);
    const tagContainer = ref<HTMLElement | null>(null);
    const showConnections = ref(true);
    const frequency = ref(2.0);
    const amplitude = ref(0.5);
    const phaseShift = ref(0.5);

    // AprilTag tracking info
    const aprilTagsDetected = ref(6);
    const cameraFps = ref(30.0);
    const trackingStatus = ref("Good");
    const jointPositions = reactive([
      { x: 0, z: 0 }, // Head
      { x: 0, z: 0 }, // Joint 1
      { x: 0, z: 0 }, // Joint 2
      { x: 0, z: 0 }, // Joint 3
      { x: 0, z: 0 }, // Joint 4
      { x: 0, z: 0 }, // Joint 5
    ]);

    let simulation: FishSimulation | null = null;
    let statsInterval: number | null = null;

    onMounted(async () => {
      if (threeContainer.value) {
        // Initialize the Three.js simulation
        simulation = new FishSimulation(
          threeContainer.value,
          tagContainer.value
        );
        await simulation.initialize();

        // Initialize UI controls with values from simulation
        if (simulation) {
          frequency.value = simulation.getFrequency();
          amplitude.value = simulation.getAmplitude();
          phaseShift.value = simulation.getPhaseShift();
        }

        // Start updating tracking stats
        startTrackingStats();
      }
    });

    const startTrackingStats = () => {
      // Update tracking stats every 500ms
      statsInterval = window.setInterval(() => {
        // Simulate AprilTag detection stats
        aprilTagsDetected.value = Math.min(
          6,
          Math.floor(Math.random() * 2) + 5
        ); // 5 or 6 tags
        cameraFps.value = 30 + (Math.random() * 4 - 2); // 28-32 FPS
        trackingStatus.value =
          aprilTagsDetected.value === 6 ? "Good" : "Partial";

        // Update joint positions based on the simulation
        if (simulation) {
          // Get positions from the simulation's fishHead and fishJoints
          // This assumes the FishSimulation class exposes the positions somehow
          // For now we'll simulate with some random values
          for (let i = 0; i < jointPositions.length; i++) {
            const wobble =
              Math.sin(
                (Date.now() / 1000) * frequency.value + i * phaseShift.value
              ) * amplitude.value;
            jointPositions[i] = {
              x: 0.5 + i * 0.8, // Approximate X positions
              z: wobble, // Z position with wobble
            };
          }
        }
      }, 500);
    };

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
        case "anguilliform": // Eel-like swimming
          frequency.value = 2.0;
          amplitude.value = 0.5;
          phaseShift.value = 0.5;
          break;
        case "carangiform": // Fish-like swimming
          frequency.value = 3.0;
          amplitude.value = 0.3;
          phaseShift.value = 0.7;
          break;
        case "thunniform": // Tuna-like swimming
          frequency.value = 4.0;
          amplitude.value = 0.2;
          phaseShift.value = 1.0;
          break;
        case "custom":
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

    const processedImage = ref(null);
    const fetchImageInterval = ref(1000); // Refresh every 1 second
    let imageRefreshInterval = null;

    // Function to fetch the processed image from the backend
    const fetchProcessedImage = async () => {
      if (!isStreaming.value || !streamingStats.connected) {
        return;
      }

      try {
        const response = await fetch(`${backendUrl.value}/get-processed-image`);

        if (!response.ok) {
          throw new Error(`HTTP error ${response.status}`);
        }

        const data = await response.json();

        if (data.image) {
          processedImage.value = data.image;
          // Update the detected tags count in streaming stats
          streamingStats.detectedTags = new Array(data.num_tags).fill({});
        }
      } catch (error) {
        console.error("Error fetching processed image:", error);
      }
    };

    // Function to manually refresh the image
    const refreshProcessedImage = () => {
      fetchProcessedImage();
    };

    // Start fetching images when streaming starts
    const startImageRefresh = () => {
      stopImageRefresh();
      imageRefreshInterval = setInterval(
        fetchProcessedImage,
        fetchImageInterval.value
      );
    };

    // Stop fetching images
    const stopImageRefresh = () => {
      if (imageRefreshInterval) {
        clearInterval(imageRefreshInterval);
        imageRefreshInterval = null;
      }
    };

    // Update the streaming toggle to also handle image refresh
    const toggleStreaming = () => {
      isStreaming.value = !isStreaming.value;

      if (isStreaming.value) {
        startStreaming();
        startImageRefresh();
      } else {
        stopStreaming();
        stopImageRefresh();
        processedImage.value = null; // Clear the image when stopping
      }
    };

    // Clean up when component is unmounted
    onBeforeUnmount(() => {
      stopStreaming();
      stopImageRefresh();
    });

    const isStreaming = ref(false);
    const backendUrl = ref("http://localhost:5000");
    const streamingStats = reactive({
      fps: 0,
      connected: false,
      lastError: "",
      detectedTags: [],
    });

    let streamingInterval = null;

    const startStreaming = () => {
      if (!simulation) return;

      // Clear any existing interval
      stopStreaming();

      // Start a new interval to capture and send frames
      streamingInterval = setInterval(async () => {
        try {
          // Capture the current frame
          const imageData = simulation.captureTagViewAsBase64();

          if (!imageData) {
            streamingStats.lastError = "Failed to capture frame";
            return;
          }

          // Send the frame to the Python backend
          const response = await fetch(`${backendUrl.value}/process-frame`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ image: imageData }),
          });

          if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
          }

          const data = await response.json();

          // Update streaming stats
          streamingStats.connected = true;
          streamingStats.fps = data.processing_fps;
          streamingStats.detectedTags = data.tag_positions;
          streamingStats.lastError = "";
        } catch (error) {
          console.error("Streaming error:", error);
          streamingStats.lastError = error.message;
          streamingStats.connected = false;
        }
      }, 100); // Send 10 frames per second
    };

    const stopStreaming = () => {
      if (streamingInterval) {
        clearInterval(streamingInterval);
        streamingInterval = null;
      }
      streamingStats.connected = false;
    };

    // Clean up when component is unmounted
    onBeforeUnmount(() => {
      stopStreaming();
    });

    onBeforeUnmount(() => {
      // Clear the tracking stats interval
      if (statsInterval !== null) {
        window.clearInterval(statsInterval);
      }

      // Clean up resources when component is unmounted
      if (simulation) {
        simulation.dispose();
        simulation = null;
      }
    });

    return {
      threeContainer,
      tagContainer,
      showConnections,
      frequency,
      amplitude,
      phaseShift,
      aprilTagsDetected,
      cameraFps,
      trackingStatus,
      jointPositions,
      toggleConnections,
      updateFrequency,
      updateAmplitude,
      updatePhaseShift,
      applyPreset,
      isStreaming,
      backendUrl,
      streamingStats,
      toggleStreaming,
      processedImage,
      fetchImageInterval,
      refreshProcessedImage,
    };
  },
});
</script>
