import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import SPEC from "../data/spec.json";

const BOUNDS = { west: 89.55, east: 96.05, south: 24.65, north: 28.35 };
const rgb = (hex) => new THREE.Color(hex);
const riskColor = (tier) => ({ HIGH: "#bd3d34", MODERATE: "#ad6b12", LOW: "#33785e" })[tier] || "#33785e";
const toLocal = ([lat, lon]) => [
  ((lon - BOUNDS.west) / (BOUNDS.east - BOUNDS.west) - 0.5) * 8.2,
  ((lat - BOUNDS.south) / (BOUNDS.north - BOUNDS.south) - 0.5) * 4.6,
];

function terrainHeight(x, z) {
  const xn = x / 8.2 + 0.5;
  const zn = z / 4.6 + 0.5;
  const ridge = 0.6 * Math.exp(-((xn - 0.93) ** 2) / 0.025) * (0.4 + zn);
  const southRise = 0.24 * Math.exp(-((zn - 0.03) ** 2) / 0.03) * (0.5 + 0.5 * Math.sin(xn * 16));
  const foothill = 0.22 * Math.exp(-((zn - (0.69 + 0.1 * Math.sin(xn * 5))) ** 2) / 0.02);
  const valley = 0.2 * Math.exp(-((zn - 0.48) ** 2) / 0.018);
  const grain = 0.035 * (Math.sin(xn * 28 + zn * 9) + Math.cos(zn * 23 - xn * 7));
  return 0.06 + ridge + southRise + foothill - valley + grain;
}

function makeTerrain(districts, selectedId) {
  const cols = 96;
  const rows = 58;
  const width = 8.2;
  const depth = 4.6;
  const positions = [];
  const colors = [];
  const indices = [];
  const low = rgb("#98b1b5");
  const mid = rgb("#c1aa78");
  const high = rgb("#ba8078");
  const districtsById = Object.fromEntries(SPEC.districts.map((d) => [d.id, d]));
  const samples = districts.map((d) => ({
    d,
    ...districtsById[d.id],
    point: toLocal(d.centroid),
    color: rgb(riskColor(d.tier)),
  }));

  for (let j = 0; j <= rows; j += 1) {
    for (let i = 0; i <= cols; i += 1) {
      const x = (i / cols - 0.5) * width;
      const z = (j / rows - 0.5) * depth;
      const h = terrainHeight(x, z);
      positions.push(x, h, z);

      let nearest = null;
      let nearestDist = Infinity;
      for (const s of samples) {
        const dx = (s.point[0] - x) * 0.85;
        const dz = s.point[1] - z;
        const dist = dx * dx + dz * dz;
        if (dist < nearestDist) { nearest = s; nearestDist = dist; }
      }
      const dataColor = nearest?.color || low;
      const elevationTone = low.clone().lerp(rgb("#d4ded8"), Math.max(0, Math.min(0.42, (h - 0.08) * 0.48)));
      const mix = elevationTone.lerp(dataColor, 0.22 + 0.25 * Math.exp(-nearestDist * 0.7));
      colors.push(mix.r, mix.g, mix.b);

      if (i < cols && j < rows) {
        const a = j * (cols + 1) + i;
        const b = a + cols + 1;
        indices.push(a, b, a + 1, b, b + 1, a + 1);
      }
    }
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  const terrain = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.92, metalness: 0.02, side: THREE.DoubleSide }));
  terrain.name = "terrain";

  const group = new THREE.Group();
  group.name = "relief-root";
  group.add(terrain);

  const riverPoints = [];
  for (let i = 0; i <= 64; i += 1) {
    const x = (i / 64 - 0.5) * width;
    const z = 0.12 + 0.14 * Math.sin((i / 64) * Math.PI * 2.5) + 0.04 * Math.cos((i / 64) * Math.PI * 5);
    riverPoints.push(new THREE.Vector3(x, terrainHeight(x, z) + 0.035, z));
  }
  const river = new THREE.Mesh(
    new THREE.TubeGeometry(new THREE.CatmullRomCurve3(riverPoints), 120, 0.025, 6, false),
    new THREE.MeshStandardMaterial({ color: "#4c9bab", roughness: 0.62, metalness: 0.02 })
  );
  river.name = "river";
  group.add(river);

  const pins = new THREE.Group();
  pins.name = "districts";
  const pinGeometry = new THREE.SphereGeometry(0.075, 16, 12);
  samples.forEach((s) => {
    const [x, z] = s.point;
    const selected = s.d.id === selectedId;
    const pin = new THREE.Mesh(pinGeometry, new THREE.MeshStandardMaterial({
      color: riskColor(s.d.tier),
      emissive: riskColor(s.d.tier),
      emissiveIntensity: selected ? 0.38 : 0.12,
      roughness: 0.48,
    }));
    pin.position.set(x, terrainHeight(x, z) + 0.11, z);
    pin.userData = { districtId: s.d.id, districtName: s.d.name };
    pins.add(pin);
    if (selected) {
      const ring = new THREE.Mesh(
        new THREE.TorusGeometry(0.13, 0.012, 6, 32),
        new THREE.MeshBasicMaterial({ color: "#162c3b" })
      );
      ring.rotation.x = Math.PI / 2;
      ring.position.set(x, terrainHeight(x, z) + 0.115, z);
      ring.userData = { districtId: s.d.id, districtName: s.d.name };
      pins.add(ring);
    }
  });
  group.add(pins);

  const frame = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.BoxGeometry(width, 0.015, depth)),
    new THREE.LineBasicMaterial({ color: "#87999d", transparent: true, opacity: 0.65 })
  );
  frame.position.y = -0.035;
  group.add(frame);
  return group;
}

export default function TerrainRelief({ districts, selectedId, onSelect }) {
  const hostRef = useRef(null);
  const sceneRef = useRef(null);
  const callbackRef = useRef(onSelect);
  callbackRef.current = onSelect;

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return undefined;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#edf1ef");
    scene.fog = new THREE.Fog("#edf1ef", 10, 20);

    const camera = new THREE.PerspectiveCamera(33, 1, 0.1, 40);
    camera.position.set(6.2, 6.6, 7.6);
    camera.lookAt(0, 0.1, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: "low-power" });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    renderer.domElement.setAttribute("aria-label", "Interactive three-dimensional Assam terrain relief; drag to rotate and click a marker to select a district");
    host.appendChild(renderer.domElement);

    scene.add(new THREE.HemisphereLight("#ffffff", "#788b8a", 2.0));
    const key = new THREE.DirectionalLight("#ffffff", 2.2);
    key.position.set(-3, 8, 5);
    scene.add(key);
    const fill = new THREE.DirectionalLight("#b5cbd0", 0.7);
    fill.position.set(4, 4, -5);
    scene.add(fill);

    const grid = new THREE.GridHelper(8.2, 16, "#b6c4c5", "#d7e0df");
    grid.position.y = -0.045;
    grid.material.transparent = true;
    grid.material.opacity = 0.38;
    scene.add(grid);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.enablePan = false;
    controls.minDistance = 7.5;
    controls.maxDistance = 14;
    controls.minPolarAngle = 0.46;
    controls.maxPolarAngle = 1.3;
    controls.target.set(0, 0.1, 0);

    const terrain = makeTerrain(districts, selectedId);
    scene.add(terrain);
    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    let frameId;

    const resize = () => {
      const width = Math.max(1, host.clientWidth);
      const height = Math.max(1, host.clientHeight);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height, false);
    };
    const observer = new ResizeObserver(resize);
    observer.observe(host);
    resize();

    let pointerDown = null;
    const rememberPointer = (event) => { pointerDown = [event.clientX, event.clientY]; };
    const pick = (event) => {
      if (pointerDown && Math.hypot(event.clientX - pointerDown[0], event.clientY - pointerDown[1]) > 5) return;
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      const pins = terrain.getObjectByName("districts");
      const hit = raycaster.intersectObjects(pins.children, false)[0];
      if (hit?.object.userData.districtId) callbackRef.current(hit.object.userData.districtId);
    };
    renderer.domElement.addEventListener("pointerdown", rememberPointer);
    renderer.domElement.addEventListener("dblclick", pick);
    renderer.domElement.addEventListener("click", pick);

    const draw = () => {
      frameId = requestAnimationFrame(draw);
      controls.update();
      renderer.render(scene, camera);
    };
    draw();
    sceneRef.current = { scene, renderer, controls };

    return () => {
      cancelAnimationFrame(frameId);
      observer.disconnect();
      renderer.domElement.removeEventListener("pointerdown", rememberPointer);
      renderer.domElement.removeEventListener("click", pick);
      renderer.domElement.removeEventListener("dblclick", pick);
      controls.dispose();
      scene.traverse((object) => {
        object.geometry?.dispose?.();
        if (Array.isArray(object.material)) object.material.forEach((m) => m.dispose());
        else object.material?.dispose?.();
      });
      renderer.dispose();
      renderer.domElement.remove();
      sceneRef.current = null;
    };
  }, []);

  useEffect(() => {
    const current = sceneRef.current;
    if (!current) return;
    const previous = current.scene.getObjectByName("relief-root");
    if (previous) {
      current.scene.remove(previous);
      previous.traverse((object) => {
        object.geometry?.dispose?.();
        if (Array.isArray(object.material)) object.material.forEach((m) => m.dispose());
        else object.material?.dispose?.();
      });
    }
    current.scene.add(makeTerrain(districts, selectedId));
  }, [districts, selectedId]);

  const selected = districts.find((d) => d.id === selectedId) || districts[0];
  return (
    <section className="terrain-inset" aria-label="Three-dimensional Assam terrain relief">
      <div className="terrain-inset__head">
        <div className="min-w-0">
          <div className="lbl">Assam terrain · 3D relief</div>
          <div className="terrain-inset__sub num">BRAHMAPUTRA BASIN / {selected?.name?.toUpperCase()}</div>
        </div>
        <span className="terrain-inset__mode">DEMO RELIEF</span>
      </div>
      <div className="terrain-inset__viewport" ref={hostRef} />
      <div className="terrain-inset__foot">
        <span className="terrain-legend"><i className="terrain-legend__marker" /> Risk tier</span>
        <span className="terrain-inset__hint">ILLUSTRATIVE · DRAG ROTATE · CLICK DISTRICT</span>
      </div>
    </section>
  );
}
