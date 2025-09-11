"use client";

import { useEffect, useRef, useState } from 'react';

const Globe3D = ({ offices, rotationSpeed = 0.001 }) => {
  const containerRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const globeRef = useRef(null);
  const markersRef = useRef(null);
  const mouseRef = useRef({ x: 0, y: 0, isDown: false });
  const rotationRef = useRef({ x: 0, y: 0 });
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (!containerRef.current || !isClient) return;

    // Dynamic import of Three.js and d3-geo to avoid SSR issues
    const initGlobe = async () => {
      const THREE = await import('three');

      // Scene setup
      const scene = new THREE.Scene();
      sceneRef.current = scene;

      // Camera
      const camera = new THREE.PerspectiveCamera(
        50,
        containerRef.current.clientWidth / containerRef.current.clientHeight,
        0.1,
        1000
      );
      camera.position.set(0, 0, 300);

      // Renderer
      const renderer = new THREE.WebGLRenderer({ 
        antialias: true, 
        alpha: true,
        powerPreference: "high-performance"
      });
      renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setClearColor(0x000000, 0);
      containerRef.current.appendChild(renderer.domElement);
      rendererRef.current = renderer;

      // Globe group
      const globeGroup = new THREE.Group();
      globeRef.current = globeGroup;
      scene.add(globeGroup);

      // Load and render world geography from GeoJSON
      const loadWorldGeography = async () => {
        try {
          const response = await fetch('/world.geojson');
          const geoData = await response.json();
          
          const bordersGroup = new THREE.Group();
          
          // Process each country feature
          geoData.features.forEach((feature) => {
            if (feature.geometry.type === 'Polygon') {
              feature.geometry.coordinates.forEach((ring) => {
                createCountryLine(ring, bordersGroup, THREE);
              });
            } else if (feature.geometry.type === 'MultiPolygon') {
              feature.geometry.coordinates.forEach((polygon) => {
                polygon.forEach((ring) => {
                  createCountryLine(ring, bordersGroup, THREE);
                });
              });
            }
          });
          
          globeGroup.add(bordersGroup);
        } catch (error) {
          console.error('Failed to load world geography:', error);
          // Fallback to simple wireframe if GeoJSON fails
          const fallbackGeometry = new THREE.SphereGeometry(100, 32, 16);
          const fallbackWireframe = new THREE.WireframeGeometry(fallbackGeometry);
          const fallbackMaterial = new THREE.LineBasicMaterial({ 
            color: 0xffffff,
            transparent: true,
            opacity: 0.3
          });
          const fallback = new THREE.LineSegments(fallbackWireframe, fallbackMaterial);
          globeGroup.add(fallback);
        }
      };

      // Convert lat/lng coordinates to 3D sphere positions
      const createCountryLine = (coordinates, group, THREE) => {
        if (coordinates.length < 2) return;
        
        const points = [];
        
        coordinates.forEach(([lng, lat]) => {
          const phi = (90 - lat) * (Math.PI / 180);
          const theta = (lng + 180) * (Math.PI / 180);
          
          const x = -(100 * Math.sin(phi) * Math.cos(theta));
          const y = 100 * Math.cos(phi);
          const z = 100 * Math.sin(phi) * Math.sin(theta);
          
          points.push(new THREE.Vector3(x, y, z));
        });
        
        if (points.length >= 2) {
          const geometry = new THREE.BufferGeometry().setFromPoints(points);
          const material = new THREE.LineBasicMaterial({
            color: 0xffffff,
            transparent: true,
            opacity: 0.4
          });
          const line = new THREE.Line(geometry, material);
          group.add(line);
        }
      };

      await loadWorldGeography();

      // Markers group
      const markersGroup = new THREE.Group();
      markersRef.current = markersGroup;
      globeGroup.add(markersGroup);

      // Convert lat/lng to 3D coordinates and create markers
      const markerPositions = [];
      
      offices.forEach((office) => {
        const phi = (90 - office.lat) * (Math.PI / 180);
        const theta = (office.lng + 180) * (Math.PI / 180);
        
        const x = -(100 * Math.sin(phi) * Math.cos(theta));
        const y = 100 * Math.cos(phi);
        const z = 100 * Math.sin(phi) * Math.sin(theta);

        // Store position for connection lines
        markerPositions.push({
          position: new THREE.Vector3(x, y, z),
          office
        });

        // Create marker (red square, smaller size)
        const markerGeometry = new THREE.PlaneGeometry(3, 3);
        const markerMaterial = new THREE.MeshBasicMaterial({ 
          color: 0xFF6B35,
          transparent: true,
          opacity: 1,
          side: THREE.DoubleSide
        });
        const marker = new THREE.Mesh(markerGeometry, markerMaterial);
        
        // Position marker slightly above surface
        const surfaceX = -(102 * Math.sin(phi) * Math.cos(theta));
        const surfaceY = 102 * Math.cos(phi);
        const surfaceZ = 102 * Math.sin(phi) * Math.sin(theta);
        marker.position.set(surfaceX, surfaceY, surfaceZ);
        
        // Billboard effect - always face camera
        marker.lookAt(camera.position);
        markersGroup.add(marker);

        // Create text label
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = 256;
        canvas.height = 128;
        context.fillStyle = '#ffffff';
        context.font = 'bold 20px Arial';
        context.textAlign = 'center';
        
        // Draw city name
        context.fillText(office.city, 128, 40);
        context.font = '16px Arial';
        context.fillText(office.coordinates, 128, 70);

        const texture = new THREE.CanvasTexture(canvas);
        const labelMaterial = new THREE.SpriteMaterial({ map: texture, transparent: true });
        const label = new THREE.Sprite(labelMaterial);
        label.scale.set(30, 15, 1);
        
        // Position label near marker
        const labelX = -(110 * Math.sin(phi) * Math.cos(theta));
        const labelY = 110 * Math.cos(phi);
        const labelZ = 110 * Math.sin(phi) * Math.sin(theta);
        label.position.set(labelX, labelY, labelZ);
        markersGroup.add(label);

        // Store marker and label references for visibility control
        marker.userData = { 
          type: 'marker', 
          office,
          position: new THREE.Vector3(x, y, z),
          surfacePosition: new THREE.Vector3(surfaceX, surfaceY, surfaceZ)
        };
        label.userData = { 
          type: 'label', 
          office,
          position: new THREE.Vector3(x, y, z)
        };
      });

      // Create connection lines between offices
      const connectionGroup = new THREE.Group();
      for (let i = 0; i < markerPositions.length; i++) {
        for (let j = i + 1; j < markerPositions.length; j++) {
          const start = markerPositions[i].position;
          const end = markerPositions[j].position;
          
          // Create curved line using quadratic bezier
          const curve = new THREE.QuadraticBezierCurve3(
            start,
            start.clone().add(end).multiplyScalar(0.6), // Control point above surface
            end
          );
          
          const points = curve.getPoints(50);
          const geometry = new THREE.BufferGeometry().setFromPoints(points);
          const material = new THREE.LineBasicMaterial({
            color: 0xFF6B35,
            transparent: true,
            opacity: 0.6
          });
          const line = new THREE.Line(geometry, material);
          connectionGroup.add(line);
        }
      }
      globeGroup.add(connectionGroup);

      // Lighting
      const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
      scene.add(ambientLight);

      const directionalLight = new THREE.DirectionalLight(0xffffff, 0.4);
      directionalLight.position.set(200, 100, 200);
      scene.add(directionalLight);

      // Tilt the globe
      globeGroup.rotation.x = -0.2;

      // Mouse interaction handlers
      const handleMouseDown = (event) => {
        mouseRef.current.isDown = true;
        mouseRef.current.x = event.clientX;
        mouseRef.current.y = event.clientY;
        containerRef.current.style.cursor = 'grabbing';
      };

      const handleMouseMove = (event) => {
        if (!mouseRef.current.isDown) return;
        
        const deltaX = event.clientX - mouseRef.current.x;
        const deltaY = event.clientY - mouseRef.current.y;
        
        rotationRef.current.y += deltaX * 0.005;
        rotationRef.current.x += deltaY * 0.005;
        
        mouseRef.current.x = event.clientX;
        mouseRef.current.y = event.clientY;
      };

      const handleMouseUp = () => {
        mouseRef.current.isDown = false;
        containerRef.current.style.cursor = 'grab';
      };

      // Add event listeners
      containerRef.current.addEventListener('mousedown', handleMouseDown);
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      containerRef.current.style.cursor = 'grab';

      // Animation loop
      const animate = () => {
        requestAnimationFrame(animate);
        
        if (globeRef.current) {
          // Apply mouse rotation
          globeRef.current.rotation.y = rotationRef.current.y;
          globeRef.current.rotation.x = -0.2 + rotationRef.current.x;
          
          // Auto-rotate only when not dragging
          if (!mouseRef.current.isDown) {
            rotationRef.current.y += rotationSpeed;
          }
        }

        // Update marker and label visibility based on globe rotation
        if (markersRef.current) {
          markersRef.current.children.forEach((child) => {
            if (child.userData?.type === 'marker' || child.userData?.type === 'label') {
              // Calculate if marker is on front or back of globe
              const worldPosition = child.userData.position.clone();
              globeRef.current?.localToWorld(worldPosition);
              
              // Check if position is facing camera (z > 0 in camera space)
              const cameraDirection = worldPosition.clone().sub(camera.position).normalize();
              const dotProduct = cameraDirection.dot(camera.getWorldDirection(new THREE.Vector3()));
              
              // Hide markers and labels on back side of globe
              child.visible = dotProduct > 0;
              
              // Billboard effect for markers
              if (child.userData?.type === 'marker') {
                child.lookAt(camera.position);
              }
            }
          });
        }
        
        renderer.render(scene, camera);
      };
      animate();

      // Handle resize
      const handleResize = () => {
        if (!containerRef.current || !rendererRef.current) return;
        
        const width = containerRef.current.clientWidth;
        const height = containerRef.current.clientHeight;
        
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height);
      };

      window.addEventListener('resize', handleResize);

      // Cleanup function
      return () => {
        window.removeEventListener('resize', handleResize);
        containerRef.current?.removeEventListener('mousedown', handleMouseDown);
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
        if (containerRef.current && renderer.domElement) {
          containerRef.current.removeChild(renderer.domElement);
        }
        renderer.dispose();
      };
    };

    let cleanup;
    initGlobe().then((cleanupFn) => {
      cleanup = cleanupFn;
    });

    return () => {
      if (cleanup) cleanup();
    };
  }, [offices, rotationSpeed, isClient]);

  // Show loading state while Three.js is loading
  if (!isClient) {
    return (
      <div 
        className="w-full h-full min-h-[500px] relative flex items-center justify-center"
        style={{ 
          background: 'radial-gradient(circle at center, rgba(255, 107, 53, 0.05) 0%, transparent 50%)' 
        }}
      >
        <div className="text-muted-foreground">Loading globe...</div>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef} 
      className="w-full h-full min-h-[500px] relative"
      style={{ 
        background: 'radial-gradient(circle at center, rgba(255, 107, 53, 0.05) 0%, transparent 50%)' 
      }}
    />
  );
};

export default Globe3D;