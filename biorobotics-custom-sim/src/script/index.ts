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
  private fishSegments: THREE.Mesh[] = [];
  
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
    this.camera.position.set(0, 5, 10);
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
    this.scene.add(this.fishHead);
    
    // Create fish joints and segments
    const numJoints = 5;
    const jointRadius = 0.2;
    const segmentLength = 0.8;
    const segmentRadius = 0.2;
    
    let prevJointPosition = new THREE.Vector3(0, 0, 0);
    
    for (let i = 0; i < numJoints; i++) {
      // Calculate joint position
      const jointPosition = new THREE.Vector3((i + 1) * segmentLength, 0, 0);
      
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
      
      // Create segment (connection between joints)
      const segmentGeometry = new THREE.CylinderGeometry(segmentRadius, segmentRadius, segmentLength, 16);
      const segmentMaterial = new THREE.MeshStandardMaterial({ color: 0x666666 });
      const segment = new THREE.Mesh(segmentGeometry, segmentMaterial);
      
      // Position and rotate the segment to connect the joints
      segment.rotation.z = Math.PI / 2;
      segment.position.set(
        prevJointPosition.x + segmentLength / 2,
        prevJointPosition.y,
        prevJointPosition.z
      );
      
      segment.castShadow = true;
      segment.receiveShadow = true;
      this.scene.add(segment);
      this.fishSegments.push(segment);
      
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
    // Apply undulating motion to the joints
    this.fishJoints.forEach((joint, index) => {
      // Phase shift increases along the body for wave-like motion
      const phaseShift = index * 0.5;
      const amplitude = 0.5; // Maximum displacement
      const frequency = 2; // Speed of undulation
      
      // Calculate y position using sine wave
      const y = amplitude * Math.sin(time * frequency + phaseShift);
      
      // Apply the position change
      joint.position.y = y;
      
      // Update the segment connecting to this joint
      if (index < this.fishSegments.length) {
        const segment = this.fishSegments[index];
        
        // Calculate previous joint position (head or previous joint)
        const prevJointPos = index === 0 
          ? new THREE.Vector3(0, 0, 0) 
          : this.fishJoints[index - 1].position;
          
        // Calculate segment position and rotation
        const midPoint = new THREE.Vector3().addVectors(prevJointPos, joint.position).multiplyScalar(0.5);
        segment.position.copy(midPoint);
        
        // Calculate the direction vector from prev to current joint
        const direction = new THREE.Vector3().subVectors(joint.position, prevJointPos).normalize();
        
        // Calculate rotation to align cylinder with direction
        // This is simplified and might need adjustment
        // const axis = new THREE.Vector3(0, 0, 1);
        const angle = Math.atan2(direction.y, direction.x);
        segment.rotation.z = angle;
        
        // Scale segment to connect joints perfectly
        const distance = prevJointPos.distanceTo(joint.position);
        segment.scale.x = distance / 0.8; // 0.8 is the original segment length
      }
    });
    
    // Adjust segment positions to connect joints properly
    this.fishSegments.forEach((segment, i) => {
      if (i === 0) {
        // First segment connects head to first joint
        const midPoint = new THREE.Vector3().addVectors(
          this.fishHead!.position, 
          this.fishJoints[0].position
        ).multiplyScalar(0.5);
        
        segment.position.copy(midPoint);
        
        // Calculate rotation
        const direction = new THREE.Vector3().subVectors(
          this.fishJoints[0].position, 
          this.fishHead!.position
        ).normalize();
        
        const angle = Math.atan2(direction.y, direction.x);
        segment.rotation.z = angle;
        
        // Adjust length
        const distance = this.fishHead!.position.distanceTo(this.fishJoints[0].position);
        segment.scale.x = distance / 0.8;
      }
    });
  }

  public dispose(): void {
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
    }
    
    window.removeEventListener('resize', this.handleResize);
    
    // Dispose of Three.js resources
    this.renderer.dispose();
    
    // Remove renderer from DOM
    if (this.renderer.domElement.parentNode) {
      this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
    }
    
    // Clear references
    this.fishJoints = [];
    this.fishSegments = [];
    this.fishHead = null;
    
    this.isInitialized = false;
  }
}