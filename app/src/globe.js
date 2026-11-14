// The 3D Moon with the sites marked on it. Uses three.js.
// The surface picture is NASA's LRO wide-angle camera mosaic, loaded live from Moon Trek's tile
// service. The stars are decoration (random points), not a real star map.
//
// createGlobe(container, sites, onSelect) draws into `container` and returns { select, setView }.
//   sites      the sites index (id, label, lat_deg, lon_deg_east, is_model_site)
//   onSelect   called with a site id when a marker is clicked
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { latLonToXyz, tileGrid, tileUrl } from "./geo.js";

const TILE_PX = 256;
const SURFACE_ZOOM = 3;      // 16 x 8 tiles = a 4096 x 2048 picture
const PREVIEW_ZOOM = 1;      // 4 x 2 tiles, shown first while the sharper ones arrive
const MARKER_RADIUS = 0.004; // on a Moon of radius 1 (about 7 km)
const COLORS = { named: 0x3987e5, model: 0xeb6834, selected: 0xffffff };

// Paint Moon Trek tiles onto one big canvas that three.js uses as the Moon's surface.
function loadSurface(texture, canvas) {
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#6f6f6f";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  const draw = (zoom) => {
    const { cols, rows } = tileGrid(zoom);
    const size = canvas.width / cols; // on-canvas size of one tile at this zoom
    for (let row = 0; row < rows; row++) {
      for (let col = 0; col < cols; col++) {
        const img = new Image();
        img.crossOrigin = "anonymous"; // Moon Trek allows this (Access-Control-Allow-Origin: *)
        img.onload = () => {
          ctx.drawImage(img, col * size, row * size, size, size);
          texture.needsUpdate = true;
        };
        img.src = tileUrl(zoom, row, col);
      }
    }
  };
  draw(PREVIEW_ZOOM);
  draw(SURFACE_ZOOM);
}

function makeStars() {
  const positions = [];
  for (let i = 0; i < 1500; i++) {
    const u = Math.random() * 2 - 1;
    const t = Math.random() * 2 * Math.PI;
    const s = Math.sqrt(1 - u * u);
    positions.push(60 * s * Math.cos(t), 60 * u, 60 * s * Math.sin(t));
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  return new THREE.Points(geometry, new THREE.PointsMaterial({ color: 0xffffff, size: 1.2, sizeAttenuation: false }));
}

export function createGlobe(container, sites, onSelect) {
  const width = () => container.clientWidth || 600;
  const height = () => container.clientHeight || 440;

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(width(), height());
  container.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x000000);
  scene.add(makeStars());

  const camera = new THREE.PerspectiveCamera(40, width() / height(), 0.01, 200);

  // The Moon: a sphere of radius 1 with the picture wrapped around it. It is drawn unlit
  // (no pretend Sun), so every part of the surface can be seen.
  const canvas = document.createElement("canvas");
  canvas.width = tileGrid(SURFACE_ZOOM).cols * TILE_PX;
  canvas.height = tileGrid(SURFACE_ZOOM).rows * TILE_PX;
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
  loadSurface(texture, canvas);
  scene.add(new THREE.Mesh(new THREE.SphereGeometry(1, 128, 96), new THREE.MeshBasicMaterial({ map: texture })));

  // Site markers: a small dot to see, and a bigger invisible ball around it that is easier to click.
  const markers = [];
  const hitTargets = [];
  const labelLayer = document.createElement("div");
  labelLayer.className = "globe-labels";
  container.appendChild(labelLayer);
  for (const site of sites) {
    const position = new THREE.Vector3(...latLonToXyz(site.lat_deg, site.lon_deg_east, 1.003));
    const dot = new THREE.Mesh(
      new THREE.SphereGeometry(MARKER_RADIUS, 16, 12),
      new THREE.MeshBasicMaterial({ color: site.is_model_site ? COLORS.model : COLORS.named })
    );
    dot.position.copy(position);
    scene.add(dot);
    const hit = new THREE.Mesh(new THREE.SphereGeometry(MARKER_RADIUS * 2.2, 8, 6), new THREE.MeshBasicMaterial({ visible: false }));
    hit.position.copy(position);
    hit.userData.siteId = site.id;
    scene.add(hit);
    hitTargets.push(hit);
    const label = document.createElement("span");
    label.className = "globe-label";
    label.textContent = site.label;
    labelLayer.appendChild(label);
    markers.push({ site, dot, hit, label, position });
  }

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enablePan = false;
  controls.enableDamping = true;
  controls.minDistance = 1.06;
  controls.maxDistance = 6;

  const views = {
    // Hovering over the south pole region, where all the sites are.
    pole: () => camera.position.set(...latLonToXyz(-82, 20, 1.5)),
    moon: () => camera.position.set(...latLonToXyz(-25, 20, 3.4)),
  };
  const setView = (name) => {
    views[name]();
    controls.update();
  };
  setView("pole");

  let selectedId = null;
  const select = (siteId) => {
    selectedId = siteId;
    for (const m of markers) {
      const on = m.site.id === siteId;
      m.dot.material.color.setHex(on ? COLORS.selected : m.site.is_model_site ? COLORS.model : COLORS.named);
      m.label.classList.toggle("selected", on);
    }
  };

  // Clicking: find the marker under the pointer. A drag (rotating the Moon) is not a click.
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  const siteUnder = (event) => {
    const box = renderer.domElement.getBoundingClientRect();
    pointer.set(((event.clientX - box.left) / box.width) * 2 - 1, -((event.clientY - box.top) / box.height) * 2 + 1);
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObjects(hitTargets, false);
    return hits.length ? hits[0].object.userData.siteId : null;
  };
  let downAt = null;
  renderer.domElement.addEventListener("pointerdown", (e) => (downAt = [e.clientX, e.clientY]));
  renderer.domElement.addEventListener("pointerup", (e) => {
    if (!downAt || Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) > 5) return;
    const id = siteUnder(e);
    if (id) onSelect(id);
  });
  renderer.domElement.addEventListener("pointermove", (e) => {
    renderer.domElement.style.cursor = siteUnder(e) ? "pointer" : "grab";
  });

  const resize = () => {
    renderer.setSize(width(), height());
    camera.aspect = width() / height();
    camera.updateProjectionMatrix();
  };
  if (typeof ResizeObserver !== "undefined") new ResizeObserver(resize).observe(container);

  const toCamera = new THREE.Vector3();
  const projected = new THREE.Vector3();
  const frame = () => {
    controls.update();
    // Keep markers a steady size on screen as you zoom, and put each name next to its dot.
    const scale = Math.min(6, Math.max(0.35, (camera.position.length() - 1) / 0.5));
    for (const m of markers) {
      const s = m.site.id === selectedId ? scale * 1.5 : scale;
      m.dot.scale.setScalar(s);
      m.hit.scale.setScalar(scale);
      toCamera.copy(camera.position).sub(m.position);
      const facing = toCamera.dot(m.position) > 0; // false when the site is on the far side
      projected.copy(m.position).project(camera);
      m.label.style.display = facing ? "" : "none";
      m.label.style.left = `${((projected.x + 1) / 2) * width()}px`;
      m.label.style.top = `${((1 - projected.y) / 2) * height()}px`;
    }
    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  };
  frame();

  return { select, setView };
}
