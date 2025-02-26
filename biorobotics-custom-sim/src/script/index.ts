import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

export class FishSimulation {
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  private controls: OrbitControls;
  private clock: THREE.Clock;
  
  // AprilTag camera view components
  private tagScene: THREE.Scene;
  private tagCamera: THREE.OrthographicCamera;
  private tagRenderer: THREE.WebGLRenderer;
  private aprilTags: THREE.Sprite[] = [];
  
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
  private tagContainer: HTMLElement | null = null;
  private isInitialized: boolean = false;
  private animationFrameId: number | null = null;

  constructor(container: HTMLElement, tagContainer: HTMLElement | null = null) {
    this.container = container;
    this.tagContainer = tagContainer;
    
    // Main 3D view
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    
    // AprilTag camera view
    this.tagScene = new THREE.Scene();
    this.tagCamera = new THREE.OrthographicCamera(-5, 5, 5, -5, 0.1, 1000);
    this.tagRenderer = new THREE.WebGLRenderer({ antialias: true });
    
    this.clock = new THREE.Clock();
  }

  public async initialize(): Promise<void> {
    if (this.isInitialized) return;
    
    // Set up main renderer
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    this.renderer.shadowMap.enabled = true;
    this.container.appendChild(this.renderer.domElement);
    
    // Set up main camera
    this.camera.position.set(10, 5, 10);
    this.camera.lookAt(0, 0, 0);
    
    // Set up controls
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    
    // Set up main scene
    this.scene.background = new THREE.Color(0xf0f0f0);
    
    // Add lighting to main scene
    const ambientLight = new THREE.AmbientLight(0x404040, 2);
    this.scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(5, 10, 7);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 1024;
    directionalLight.shadow.mapSize.height = 1024;
    this.scene.add(directionalLight);
    
    // Add grid to main scene
    const gridHelper = new THREE.GridHelper(20, 20);
    this.scene.add(gridHelper);
    
    // Set up AprilTag camera view if container exists
    if (this.tagContainer) {
      // Set up tag renderer
      this.tagRenderer.setSize(this.tagContainer.clientWidth, this.tagContainer.clientHeight);
      this.tagContainer.appendChild(this.tagRenderer.domElement);
      
      // Set up tag camera (top-down view)
      this.tagCamera.position.set(0, 10, 0);
      this.tagCamera.lookAt(0, 0, 0);
      this.tagCamera.rotation.z = Math.PI; // Flip the camera to match the orientation
      
      // Set up tag scene
      this.tagScene.background = new THREE.Color(0x111111); // Dark background for contrast
      
      // Add subtle floor grid to tag scene
      const gridSize = 20;
      const gridDivisions = 20;
      const gridMaterial = new THREE.LineBasicMaterial({ color: 0x333333 });
      
      for (let i = -gridSize/2; i <= gridSize/2; i++) {
        const lineGeometry1 = new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(i, 0, -gridSize/2),
          new THREE.Vector3(i, 0, gridSize/2)
        ]);
        const lineGeometry2 = new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(-gridSize/2, 0, i),
          new THREE.Vector3(gridSize/2, 0, i)
        ]);
        
        const line1 = new THREE.Line(lineGeometry1, gridMaterial);
        const line2 = new THREE.Line(lineGeometry2, gridMaterial);
        
        this.tagScene.add(line1);
        this.tagScene.add(line2);
      }
      
      // Add dim lighting to tag scene
      const tagAmbientLight = new THREE.AmbientLight(0x555555);
      this.tagScene.add(tagAmbientLight);
      
      const tagDirectionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
      tagDirectionalLight.position.set(0, 10, 0);
      this.tagScene.add(tagDirectionalLight);
    }
    
    // Create fish robot
    this.createSimpleFishRobot();
    
    // Set up resize listener
    window.addEventListener('resize', this.handleResize);
    
    this.isInitialized = true;
    
    // Start animation loop
    this.animate();
  }

  public captureTagViewAsBase64(): string | null {
    if (!this.tagRenderer) return null;
    
    // Render the scene to make sure it's up to date
    this.tagRenderer.render(this.tagScene, this.tagCamera);
    
    // Get the canvas element from the renderer
    const canvas = this.tagRenderer.domElement;
    
    // Convert the canvas to a base64-encoded image
    try {
      // Use toDataURL to get base64 image data (JPEG format with 0.8 quality for smaller size)
      return canvas.toDataURL('image/jpeg', 0.8);
    } catch (error) {
      console.error('Error capturing tag view:', error);
      return null;
    }
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
    
    // Create a copy for the tag scene
    if (this.tagContainer) {
      const tagHead = new THREE.Mesh(headGeometry, headMaterial);
      tagHead.position.copy(this.fishHead.position);
      this.tagScene.add(tagHead);
      
      // Add AprilTag to the head (just a visual representation)
      this.createAprilTag(0, this.fishHead.position);
    }
    
    // Create fish joints and lines
    const numJoints = 5;
    const jointRadius = 0.2;
    
    // Initialize arrays
    this.fishJoints = [];
    this.fishLines = [];
    this.aprilTags = [];
    
    // Position of back of the head
    let prevJointPosition = new THREE.Vector3(0.5, 0.5, 0);
    
    // Create a line material
    const lineMaterial = new THREE.LineBasicMaterial({ 
      color: 0x000000, 
      linewidth: 2
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
      
      // Create a copy for the tag scene
      if (this.tagContainer) {
        const tagJoint = new THREE.Mesh(jointGeometry, jointMaterial);
        tagJoint.position.copy(jointPosition);
        this.tagScene.add(tagJoint);
        
        // Add AprilTag to this joint
        this.createAprilTag(i + 1, jointPosition);
      }
      
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
      
      // Create a copy for the tag scene
      if (this.tagContainer) {
        const tagLineGeometry = new THREE.BufferGeometry().setFromPoints(points);
        const tagLine = new THREE.Line(tagLineGeometry, lineMaterial);
        tagLine.visible = this.showConnections;
        this.tagScene.add(tagLine);
      }
      
      prevJointPosition = jointPosition.clone();
    }
  }
  
  private createAprilTag(id: number, position: THREE.Vector3): void {
    // Create a canvas for the AprilTag
    const canvas = document.createElement('canvas');
    canvas.width = 64;
    canvas.height = 64;
    const ctx = canvas.getContext('2d');
    
    if (!ctx) return;
    
    // Draw AprilTag pattern (simplified representation)
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, 64, 64);
    
    ctx.fillStyle = 'black';
    ctx.fillRect(8, 8, 48, 48);
    
    ctx.fillStyle = 'white';
    ctx.fillRect(16, 16, 32, 32);
    
    // Draw ID number in the center
    ctx.fillStyle = 'black';
    ctx.font = 'bold 24px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(id.toString(), 32, 32);
    
    // Create a texture from the canvas
    const texture = new THREE.CanvasTexture(canvas);
    
    // Create a sprite material with the texture
    const material = new THREE.SpriteMaterial({ map: texture });
    
    // Create a sprite with the material
    const sprite = new THREE.Sprite(material);
    sprite.position.copy(position);
    sprite.position.y += 0.25; // Position slightly above the joint
    sprite.scale.set(0.5, 0.5, 1);
    
    // Add the sprite to the tag scene
    this.tagScene.add(sprite);
    this.aprilTags.push(sprite);
  }

  private handleResize = (): void => {
    if (!this.container) return;
    
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    
    // Update main view
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
    
    // Update tag view if available
    if (this.tagContainer) {
      const tagWidth = this.tagContainer.clientWidth;
      const tagHeight = this.tagContainer.clientHeight;
      
      this.tagCamera.left = -tagWidth / tagHeight * 5;
      this.tagCamera.right = tagWidth / tagHeight * 5;
      this.tagCamera.top = 5;
      this.tagCamera.bottom = -5;
      this.tagCamera.updateProjectionMatrix();
      
      this.tagRenderer.setSize(tagWidth, tagHeight);
    }
  }

  private animate = (): void => {
    this.animationFrameId = requestAnimationFrame(this.animate);
    
    const time = this.clock.getElapsedTime();
    
    // Simulate fish swimming motion
    this.simulateSwimmingMotion(time);
    
    // Update main view
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
    
    // Update tag view if available
    if (this.tagContainer) {
      this.updateTagView();
      this.tagRenderer.render(this.tagScene, this.tagCamera);
    }
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
  
  private updateTagView(): void {
    // Update AprilTag positions to match the fish joints
    this.aprilTags.forEach((tag, index) => {
      if (index === 0) {
        // Head tag
        tag.position.x = this.fishHead!.position.x;
        tag.position.z = this.fishHead!.position.z;
        tag.position.y = this.fishHead!.position.y + 0.25;
      } else {
        // Joint tags
        const joint = this.fishJoints[index - 1];
        tag.position.x = joint.position.x;
        tag.position.z = joint.position.z;
        tag.position.y = joint.position.y + 0.25;
      }
    });
    
    // Update tag scene lines to match the main scene
    let lineIndex = 0;
    
    // Find the line objects in tag scene and update them
    this.tagScene.traverse((object) => {
      if (object instanceof THREE.Line && !(object instanceof THREE.LineSegments) && lineIndex < this.fishLines.length) {
        const mainLine = this.fishLines[lineIndex];
        
        if (mainLine.geometry instanceof THREE.BufferGeometry) {
          // Get the positions from the main line
          const positions = mainLine.geometry.getAttribute('position').array;
          const points = [];
          
          for (let i = 0; i < positions.length; i += 3) {
            points.push(new THREE.Vector3(positions[i], positions[i+1], positions[i+2]));
          }
          
          // Update tag line geometry
          object.geometry.dispose();
          object.geometry = new THREE.BufferGeometry().setFromPoints(points);
          object.visible = this.showConnections;
          
          lineIndex++;
        }
      }
    });
    
    // Add a simulated camera noise effect to make it look more realistic
    this.aprilTags.forEach(tag => {
      if (Math.random() > 0.95) {
        // Occasionally make a tag flicker
        tag.visible = Math.random() > 0.5;
        setTimeout(() => {
          tag.visible = true;
        }, 100);
      }
    });
  }

  // Public method to toggle line visibility
  public toggleConnections(visible: boolean): void {
    this.showConnections = visible;
    
    // Update visibility of all lines in main scene
    this.fishLines.forEach(line => {
      line.visible = visible;
    });
    
    // Update visibility in tag scene
    if (this.tagContainer) {
      this.tagScene.traverse((object) => {
        if (object instanceof THREE.Line && !(object instanceof THREE.LineSegments)) {
          object.visible = visible;
        }
      });
    }
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
    
    // Remove renderers from DOM
    if (this.renderer.domElement.parentNode) {
      this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
    }
    
    if (this.tagRenderer.domElement.parentNode) {
      this.tagRenderer.domElement.parentNode.removeChild(this.tagRenderer.domElement);
    }
    
    // Clear references
    this.fishJoints = [];
    this.fishLines = [];
    this.aprilTags = [];
    this.fishHead = null;
    
    this.isInitialized = false;
  }
}