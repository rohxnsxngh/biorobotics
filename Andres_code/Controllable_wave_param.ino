#include <Servo.h>
#include <math.h>

// --- SERVOS ---
Servo servo1, servo2, servo3, servo4, servo5, servo6;  // Added servo6

// === USER-TUNABLE PARAMETERS ===
// Tail wave
const float amplitude       = 25.0;    // degrees - increased for more thrust
const float frequency       = 2.0;     // Hz - slightly slower for more powerful strokes
const float phaseShiftDeg   = 45.0;    // degrees between joints - reduced for smoother wave

// Per-joint scaling constants - modified to create a natural fish motion
const float constant1       = 0.6;     // Head/first segment (minimal movement)
const float constant2       = 0.8;     // Second segment
const float constant3       = 1.2;     // Third segment
const float constant4       = 1.3;     // Fourth segment
const float constant5       = 1.4;     // Fifth segment
const float constant6       = 0;     // Tail fin (greatest movement)

// Burst-and-glide settings
const float cyclesPerBurst  = 3.0;     // More cycles per burst for better momentum
const float restTime        = 1.0;     // Shorter glide time
const float transitionSpeed = 2.0;     // Smoothing transition factor

// Control mode
const bool continuous_mode  = true;   // Set to false for burst-and-glide

// === DIRECTION CONTROL ===
// +1 = head->tail wave direction (correct for forward swimming)
const int directionMultiplier = 1;     // Changed to +1 for proper wave direction

// === SCHEDULE TIMINGS (seconds) ===
const float bufferTime      = 25.0;    // initial wait
const float activeTime      = 180.0;    // run tail wave
const float shutdownTime    = 180.0;    // final hold

// === INTERNAL SETTINGS ===
const float centerPos       = 90.0;    // neutral servo angle
const unsigned long updateDelay = 20;  // ms between updates
const float pi              = 3.14159265;

// --- TIMING / STATE ---
unsigned long previousMillis = 0;
float timeSeconds            = 0.0;

void setup() {
  servo1.attach(5);
  servo2.attach(6);
  servo3.attach(9);
  servo4.attach(10);
  servo5.attach(11);
  servo6.attach(3);  // Added servo6 - assuming pin 3 is available
  
  // Initialize all servos to center position
  servo1.write((int)centerPos);
  servo2.write((int)centerPos);
  servo3.write((int)centerPos);
  servo4.write((int)centerPos);
  servo5.write((int)centerPos);
  servo6.write((int)centerPos);
}

void loop() {
  unsigned long m = millis();
  if (m - previousMillis < updateDelay) return;
  previousMillis = m;
  timeSeconds += updateDelay / 1000.0;

  // Determine which phase we are in
  if (timeSeconds < bufferTime) {
    // Startup buffer: hold neutral
    servo1.write((int)centerPos);
    servo2.write((int)centerPos);
    servo3.write((int)centerPos);
    servo4.write((int)centerPos);
    servo5.write((int)centerPos);
    servo6.write((int)centerPos);
    return;
  }
  
  float tActive = timeSeconds - bufferTime;
  if (tActive < activeTime) {
    // Active tail-wave phase
    float t = tActive;  
    // Precompute
    float phaseRad = phaseShiftDeg * pi / 180.0;
    float omega    = 2 * pi * frequency;
    // Envelope (continuous or burst-glide)
    float envelope = 1.0;
    if (!continuous_mode) {
      float burstTime = cyclesPerBurst / frequency;
      float cycleTime = burstTime + restTime;
      float tin = fmod(t, cycleTime);
      int   idx = int(t / cycleTime);
      if (tin < burstTime) {
        float u = tin / burstTime;
        float uu = fmin(1.0, u * transitionSpeed);
        envelope = 0.5 * (1 - cos(pi * uu));
      } else {
        float v = (tin - burstTime) / restTime;
        float vv = fmin(1.0, v * transitionSpeed);
        envelope = 0.5 * (1 + cos(pi * vv));
      }
      if (idx & 1) envelope = 0; // Just rest on alternate cycles instead of reversing
    }
    envelope *= directionMultiplier;
    
    // Joint angles - phase ordering is KEY to correct wave propagation
    // The order here ensures wave travels from head to tail
    float a1 = centerPos + constant1 * envelope * amplitude * sin(omega * t);
    float a2 = centerPos + constant2 * envelope * amplitude * sin(omega * t - phaseRad);     // Note negative phase shift
    float a3 = centerPos + constant3 * envelope * amplitude * sin(omega * t - 2*phaseRad);   // Each joint lags the previous
    float a4 = centerPos + constant4 * envelope * amplitude * sin(omega * t - 3*phaseRad);   // This creates head→tail wave
    float a5 = centerPos + constant5 * envelope * amplitude * sin(omega * t - 4*phaseRad);
    float a6 = centerPos + constant6 * envelope * amplitude * sin(omega * t - 5*phaseRad);   // Last joint has maximum delay
    
    servo1.write((int)a1);
    servo2.write((int)a2);
    servo3.write((int)a3);
    servo4.write((int)a4);
    servo5.write((int)a5);
    servo6.write((int)a6);
    return;
  }
  
  // Shutdown hold: timeSeconds ≥ bufferTime+activeTime, hold neutral
  servo1.write((int)centerPos);
  servo2.write((int)centerPos);
  servo3.write((int)centerPos);
  servo4.write((int)centerPos);
  servo5.write((int)centerPos);
  servo6.write((int)centerPos);
  
  // Optionally: stop updating timeSeconds here to freeze schedule
}