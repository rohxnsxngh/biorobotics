import React, { useState, useEffect, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const BioroboticsFishSimulation = () => {
  const [activeJoints, setActiveJoints] = useState([]);
  const [passiveJoints, setPassiveJoints] = useState([]);
  const [time, setTime] = useState(0);
  const [running, setRunning] = useState(true);
  const [frequency, setFrequency] = useState(1);
  const [amplitude, setAmplitude] = useState(30);
  const [phaseShift, setPhaseShift] = useState(0.5);
  const [trackingData, setTrackingData] = useState([]);
  
  const canvasRef = useRef(null);
  
  // Number of joints in the fish tail
  const numJoints = 5;
  
  useEffect(() => {
    if (!running) return;
    
    const interval = setInterval(() => {
      setTime(prevTime => prevTime + 0.1);
    }, 100);
    
    return () => clearInterval(interval);
  }, [running]);
  
  useEffect(() => {
    // Calculate joint positions based on time and parameters
    const newActiveJoints = [];
    const newPassiveJoints = [];
    
    // Calculate positions for active joints (with powered motion)
    for (let i = 0; i < numJoints; i++) {
      const phase = phaseShift * i;
      const angle = amplitude * Math.sin(frequency * time + phase);
      
      // Starting position of the first joint relative to "head"
      let x = 50;
      let y = 150;
      
      // Calculate position based on previous joints
      for (let j = 0; j <= i; j++) {
        const segmentPhase = phaseShift * j;
        const segmentAngle = amplitude * Math.sin(frequency * time + segmentPhase);
        
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
    // For simulation purposes, we'll dampen the motion to show the difference
    for (let i = 0; i < numJoints; i++) {
      const phase = phaseShift * i;
      // Passive joints have reduced amplitude and delayed response
      const angle = (amplitude * 0.7) * Math.sin(frequency * time * 0.8 + phase);
      
      let x = 50;
      let y = 300; // Position the passive system below the active one
      
      for (let j = 0; j <= i; j++) {
        const segmentPhase = phaseShift * j;
        const segmentAngle = (amplitude * 0.7) * Math.sin(frequency * time * 0.8 + segmentPhase);
        
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
    
    setActiveJoints(newActiveJoints);
    setPassiveJoints(newPassiveJoints);
    
    // Add tracking data for the graph
    if (time % 1 < 0.1) { // Record data every ~1 second
      setTrackingData(prev => {
        const newData = [...prev, {
          time: time.toFixed(1),
          activeJoint1: newActiveJoints[0]?.angle.toFixed(1) || 0,
          activeJoint2: newActiveJoints[1]?.angle.toFixed(1) || 0,
          activeJoint3: newActiveJoints[2]?.angle.toFixed(1) || 0,
          passiveJoint1: newPassiveJoints[0]?.angle.toFixed(1) || 0,
          passiveJoint2: newPassiveJoints[1]?.angle.toFixed(1) || 0,
          passiveJoint3: newPassiveJoints[2]?.angle.toFixed(1) || 0,
        }];
        
        // Keep only the last 20 data points
        if (newData.length > 20) {
          return newData.slice(newData.length - 20);
        }
        return newData;
      });
    }
  }, [time, frequency, amplitude, phaseShift]);
  
  useEffect(() => {
    if (!canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
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
    activeJoints.forEach((joint, index) => {
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
    
    passiveJoints.forEach((joint, index) => {
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
  }, [activeJoints, passiveJoints]);
  
  return (
    <div className="flex flex-col w-full max-w-6xl mx-auto p-4 bg-gray-50 rounded-lg shadow-md">
      <h1 className="text-2xl font-bold mb-4">Fish Robotics Joint Tracking System</h1>
      
      <div className="flex flex-col lg:flex-row gap-4 mb-6">
        <div className="w-full lg:w-1/2 bg-white p-4 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-2">Simulation</h2>
          <canvas 
            ref={canvasRef} 
            width={600} 
            height={400} 
            className="w-full h-auto border border-gray-300 rounded"
          />
          
          <div className="flex justify-between mt-4">
            <button 
              onClick={() => setRunning(!running)} 
              className={`px-4 py-2 rounded ${running ? 'bg-red-500 text-white' : 'bg-green-500 text-white'}`}
            >
              {running ? 'Pause' : 'Resume'}
            </button>
            
            <button 
              onClick={() => {
                setTime(0);
                setTrackingData([]);
              }} 
              className="px-4 py-2 bg-blue-500 text-white rounded"
            >
              Reset
            </button>
          </div>
        </div>
        
        <div className="w-full lg:w-1/2 bg-white p-4 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-2">Controls</h2>
          
          <div className="mb-4">
            <label className="block mb-1">
              Frequency: {frequency.toFixed(1)}
            </label>
            <input 
              type="range" 
              min="0.1" 
              max="3" 
              step="0.1" 
              value={frequency} 
              onChange={(e) => setFrequency(parseFloat(e.target.value))} 
              className="w-full"
            />
          </div>
          
          <div className="mb-4">
            <label className="block mb-1">
              Amplitude (degrees): {amplitude}
            </label>
            <input 
              type="range" 
              min="5" 
              max="60" 
              step="1" 
              value={amplitude} 
              onChange={(e) => setAmplitude(parseInt(e.target.value))} 
              className="w-full"
            />
          </div>
          
          <div className="mb-4">
            <label className="block mb-1">
              Phase Shift: {phaseShift.toFixed(1)}
            </label>
            <input 
              type="range" 
              min="0.1" 
              max="1.5" 
              step="0.1" 
              value={phaseShift} 
              onChange={(e) => setPhaseShift(parseFloat(e.target.value))} 
              className="w-full"
            />
          </div>
        </div>
      </div>
      
      <div className="w-full bg-white p-4 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-2">Joint Angle Tracking Data</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trackingData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" label={{ value: 'Time (s)', position: 'insideBottom', offset: -5 }} />
              <YAxis label={{ value: 'Angle (degrees)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="activeJoint1" stroke="#ff0000" name="Active Joint 1" />
              <Line type="monotone" dataKey="activeJoint2" stroke="#ff6666" name="Active Joint 2" />
              <Line type="monotone" dataKey="activeJoint3" stroke="#ffaaaa" name="Active Joint 3" />
              <Line type="monotone" dataKey="passiveJoint1" stroke="#0000ff" name="Passive Joint 1" />
              <Line type="monotone" dataKey="passiveJoint2" stroke="#6666ff" name="Passive Joint 2" />
              <Line type="monotone" dataKey="passiveJoint3" stroke="#aaaaff" name="Passive Joint 3" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      <div className="mt-6 p-4 bg-white rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-2">Implementation Notes</h2>
        <ul className="list-disc pl-5 space-y-2">
          <li>This simulation represents the joints that would have AprilTags attached in the physical setup</li>
          <li>Red circles represent active joints (motorized/actuated)</li>
          <li>Blue circles represent passive joints (moved by the body's inertia)</li>
          <li>The graph tracks joint angles over time, which is what you would analyze from AprilTag data</li>
          <li>Adjust parameters to simulate different swimming patterns (anguilliform, carangiform, etc.)</li>
          <li>For a full 3D implementation, this could be expanded using Three.js and Rapier.js as you suggested</li>
        </ul>
      </div>
    </div>
  );
};

export default BioroboticsFishSimulation;