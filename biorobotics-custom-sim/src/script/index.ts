import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

export class FishSimulation {
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  private controls: OrbitControls;
  private clock: THREE.Clock;
  
  // Fish components
  private fishHead: THREE.Mesh | null = null;
  private fishJoints: THREE.Mesh[] = [];
  
  // Lines instead of cylinders
  private fishLines: THREE.Line[] = [];
  
  // Swimming parameters
  private frequency: number = 2.0;
  private amplitude: number = 0.5;
  private phaseShift: number = 0.5;
  
  // Configuration options
  private showConnections: boolean = true;
  
  private container: HTMLElement;
  private isInitialized: boolean = false;
  private animationFrameId: number | null = null;

  constructor(container: HTMLElement) {
    this.container = container;
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.clock = new THREE.Clock();
  }

  public async initialize(): Promise<void> {
    if (this.isInitialized) return;
    
    // Set up renderer
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    this.renderer.shadowMap.enabled = true;
    this.container.appendChild(this.renderer.domElement);
    
    // Set up camera
    this.camera.position.set(10, 5, 10);
    this.camera.lookAt(0, 0, 0);
    
    // Set up controls
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    
    // Set up scene
    this.scene.background = new THREE.Color(0xf0f0f0);
    
    // Add lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 2);
    this.scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(5, 10, 7);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 1024;
    directionalLight.shadow.mapSize.height = 1024;
    this.scene.add(directionalLight);
    
    // Add grid
    const gridHelper = new THREE.GridHelper(20, 20);
    this.scene.add(gridHelper);
    
    // Create fish robot without physics for now
    this.createSimpleFishRobot();
    
    // Set up resize listener
    window.addEventListener('resize', this.handleResize);
    
    this.isInitialized = true;
    
    // Start animation loop
    this.animate();
  }

  private createSimpleFishRobot(): void {
    // Create fish head
    const headGeometry = new THREE.BoxGeometry(1, 1, 1);
    const headMaterial = new THREE.MeshStandardMaterial({ color: 0x333333 });
    this.fishHead = new THREE.Mesh(headGeometry, headMaterial);
    this.fishHead.castShadow = true;
    this.fishHead.receiveShadow = true;
    this.fishHead.position.set(0, 0.5, 0); // Lifted slightly so it sits on the grid
    this.scene.add(this.fishHead);
    
    // Create fish joints and lines
    const numJoints = 5;
    const jointRadius = 0.2;
    
    // Initialize arrays
    this.fishJoints = [];
    this.fishLines = [];
    
    // Position of back of the head
    let prevJointPosition = new THREE.Vector3(0.5, 0.5, 0);
    
    // Create a line material
    const lineMaterial = new THREE.LineBasicMaterial({ 
      color: 0x000000, 
      linewidth: 2 // Note: linewidth may not work in all browsers due to WebGL limitations
    });
    
    // First line will connect head to first joint
    for (let i = 0; i < numJoints; i++) {
      // Calculate joint position - extending along positive X-axis
      const jointPosition = new THREE.Vector3(
        prevJointPosition.x + 0.8, // 0.8 spacing between joints
        0.5, 
        0
      );
      
      // Create joint sphere (visual representation of joint)
      const jointGeometry = new THREE.SphereGeometry(jointRadius, 16, 16);
      const jointMaterial = new THREE.MeshStandardMaterial({ 
        color: i % 2 === 0 ? 0xff0000 : 0x0000ff // Alternate between red and blue
      });
      const joint = new THREE.Mesh(jointGeometry, jointMaterial);
      joint.position.copy(jointPosition);
      joint.castShadow = true;
      joint.receiveShadow = true;
      this.scene.add(joint);
      this.fishJoints.push(joint);
      
      // Create a line to connect from previous position to this joint
      const points = [];
      
      if (i === 0) {
        // First line connects from the head
        points.push(this.fishHead.position);
      } else {
        // Connect from previous joint
        points.push(this.fishJoints[i-1].position);
      }
      
      points.push(jointPosition);
      
      const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);
      const line = new THREE.Line(lineGeometry, lineMaterial);
      line.visible = this.showConnections;
      this.scene.add(line);
      this.fishLines.push(line);
      
      prevJointPosition = jointPosition.clone();
    }
  }

  private handleResize = (): void => {
    if (!this.container) return;
    
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  private animate = (): void => {
    this.animationFrameId = requestAnimationFrame(this.animate);
    
    const time = this.clock.getElapsedTime();
    
    // Simulate fish swimming motion without physics
    this.simulateSwimmingMotion(time);
    
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }
  
  private simulateSwimmingMotion(time: number): void {
    // Apply undulating motion to the joints - moving side to side in the Z direction
    this.fishJoints.forEach((joint, index) => {
      // Phase shift increases along the body for wave-like motion
      const phaseOffset = this.phaseShift * index;
      
      // Calculate the position change along Z-axis (side to side)
      const z = this.amplitude * Math.sin(this.frequency * time + phaseOffset);
      
      // Keep X and Y constant, only change Z
      joint.position.z = z;
    });
    
    // Update all the connecting lines
    this.updateLines();
  }
  
  private updateLines(): void {
    // Update each line to connect between the correct points
    this.fishLines.forEach((line, index) => {
      const points = [];
      
      if (index === 0) {
        // First line connects head to first joint
        points.push(this.fishHead!.position);
        points.push(this.fishJoints[0].position);
      } else {
        // Other lines connect between joints
        points.push(this.fishJoints[index-1].position);
        points.push(this.fishJoints[index].position);
      }
      
      // Update the line geometry
      line.geometry.dispose(); // Dispose old geometry to prevent memory leaks
      line.geometry = new THREE.BufferGeometry().setFromPoints(points);
    });
  }

  // Public method to toggle line visibility
  public toggleConnections(visible: boolean): void {
    this.showConnections = visible;
    
    // Update visibility of all lines
    this.fishLines.forEach(line => {
      line.visible = visible;
    });
  }
  
  // Getter and setter methods for swimming parameters
  public getFrequency(): number {
    return this.frequency;
  }
  
  public setFrequency(value: number): void {
    this.frequency = value;
  }
  
  public getAmplitude(): number {
    return this.amplitude;
  }
  
  public setAmplitude(value: number): void {
    this.amplitude = value;
  }
  
  public getPhaseShift(): number {
    return this.phaseShift;
  }
  
  public setPhaseShift(value: number): void {
    this.phaseShift = value;
  }

  public dispose(): void {
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
    }
    
    window.removeEventListener('resize', this.handleResize);
    
    // Dispose of Three.js resources
    this.renderer.dispose();
    
    // Dispose of geometries and materials
    this.fishLines.forEach(line => {
      line.geometry.dispose();
    });
    
    // Remove renderer from DOM
    if (this.renderer.domElement.parentNode) {
      this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
    }
    
    // Clear references
    this.fishJoints = [];
    this.fishLines = [];
    this.fishHead = null;
    
    this.isInitialized = false;
  }
}