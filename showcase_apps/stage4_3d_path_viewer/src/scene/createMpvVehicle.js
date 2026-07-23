import * as THREE from "three";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import { VIEWER_COLORS } from "../config/colors.js";

const MM_TO_M = 0.001;

function roundedPart(width, height, length, radius, material) {
  const geometry = new RoundedBoxGeometry(width, height, length, 5, radius);
  const mesh = new THREE.Mesh(geometry, material);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  return mesh;
}

export function createMpvVehicle(vehicle, opacity = 0.42) {
  const dimensions = vehicle.dimensions_mm;
  const proportions = vehicle.body_proportions;
  const length = dimensions.length_mm * MM_TO_M;
  const width = dimensions.width_mm * MM_TO_M;
  const height = dimensions.height_mm * MM_TO_M;
  const wheelbase = dimensions.wheelbase_mm * MM_TO_M;
  const wheelRadius = dimensions.wheel_radius_mm * MM_TO_M;
  const clearance = dimensions.ground_clearance_mm * MM_TO_M;
  const lowerHeight = height * proportions.lower_body_height_ratio;
  const cabinHeight = height * proportions.cabin_height_ratio;
  const cabinLength = length * proportions.cabin_length_ratio;
  const cabinWidth = width * proportions.cabin_width_ratio;
  const hoodLength = length * proportions.hood_length_ratio;

  const group = new THREE.Group();
  group.name = "generic-mpv-display";
  const solids = new THREE.Group();
  const wires = new THREE.Group();
  group.add(solids, wires);

  const bodyMaterial = new THREE.MeshPhysicalMaterial({
    color: VIEWER_COLORS.body,
    roughness: 0.46,
    metalness: 0.26,
    transparent: true,
    opacity,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
  const glassMaterial = new THREE.MeshPhysicalMaterial({
    color: VIEWER_COLORS.windows,
    roughness: 0.15,
    metalness: 0.08,
    transparent: true,
    opacity: Math.min(0.7, opacity + 0.16),
    depthWrite: false,
  });
  const tireMaterial = new THREE.MeshStandardMaterial({
    color: VIEWER_COLORS.tire,
    roughness: 0.86,
    metalness: 0.04,
  });
  const rimMaterial = new THREE.MeshStandardMaterial({
    color: VIEWER_COLORS.rim,
    roughness: 0.35,
    metalness: 0.72,
  });

  const lower = roundedPart(width, lowerHeight, length * 0.94, 0.16, bodyMaterial);
  lower.position.y = clearance + lowerHeight * 0.5;
  solids.add(lower);

  const cabin = roundedPart(cabinWidth, cabinHeight, cabinLength, 0.18, bodyMaterial);
  cabin.position.set(0, clearance + lowerHeight + cabinHeight * 0.43, length * 0.04);
  solids.add(cabin);

  const hood = roundedPart(width * 0.88, lowerHeight * 0.56, hoodLength, 0.1, bodyMaterial);
  hood.position.set(
    0,
    clearance + lowerHeight * 0.72,
    -length * 0.5 + hoodLength * 0.62,
  );
  solids.add(hood);

  const windowHeight = cabinHeight * 0.43;
  const windowY = clearance + lowerHeight + cabinHeight * 0.5;
  const sideWindowLength = cabinLength * 0.72;
  for (const side of [-1, 1]) {
    const windowMesh = roundedPart(0.025, windowHeight, sideWindowLength, 0.025, glassMaterial);
    windowMesh.position.set(
      side * (cabinWidth * 0.5 + 0.011),
      windowY,
      length * 0.07,
    );
    solids.add(windowMesh);
  }

  const windshield = roundedPart(
    cabinWidth * 0.88,
    windowHeight,
    0.035,
    0.025,
    glassMaterial,
  );
  windshield.position.set(0, windowY, -cabinLength * 0.5 + length * 0.04);
  windshield.rotation.x = -0.2;
  solids.add(windshield);

  const rearGlass = windshield.clone();
  rearGlass.position.z = cabinLength * 0.5 + length * 0.04;
  rearGlass.rotation.x = 0.1;
  solids.add(rearGlass);

  const bumperMaterial = new THREE.MeshStandardMaterial({
    color: 0x26333d,
    roughness: 0.72,
    metalness: 0.12,
  });
  for (const end of [-1, 1]) {
    const bumper = roundedPart(width * 0.9, 0.16, 0.13, 0.045, bumperMaterial);
    bumper.position.set(0, clearance + 0.2, end * (length * 0.5 - 0.03));
    solids.add(bumper);
  }

  const wheelGeometry = new THREE.CylinderGeometry(wheelRadius, wheelRadius, 0.22, 32);
  wheelGeometry.rotateZ(Math.PI / 2);
  const rimGeometry = new THREE.CylinderGeometry(wheelRadius * 0.53, wheelRadius * 0.53, 0.235, 24);
  rimGeometry.rotateZ(Math.PI / 2);
  for (const side of [-1, 1]) {
    for (const axle of [-1, 1]) {
      const wheel = new THREE.Mesh(wheelGeometry, tireMaterial);
      wheel.position.set(side * width * 0.49, wheelRadius, axle * wheelbase * 0.5);
      wheel.castShadow = true;
      const rim = new THREE.Mesh(rimGeometry, rimMaterial);
      rim.position.copy(wheel.position);
      solids.add(wheel, rim);
    }
  }

  [lower, cabin, hood].forEach((part) => {
    const wire = new THREE.LineSegments(
      new THREE.EdgesGeometry(part.geometry, 20),
      new THREE.LineBasicMaterial({
        color: VIEWER_COLORS.bodyWire,
        transparent: true,
        opacity: 0.7,
      }),
    );
    wire.position.copy(part.position);
    wire.rotation.copy(part.rotation);
    wires.add(wire);
  });

  function setMode(mode) {
    solids.visible = mode !== "wireframe";
    wires.visible = mode !== "solid";
  }

  setMode("solid-wireframe");
  return { group, solids, wires, setMode, wheelCount: 4 };
}
