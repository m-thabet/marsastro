import {
  Canvas,
  useFrame,
  useThree,
  type ThreeEvent,
} from "@react-three/fiber";
import {
  OrbitControls,
  useGLTF,
  useTexture,
  useProgress,
  Html,
  Line,
} from "@react-three/drei";
import {
  Suspense,
  useEffect,
  useMemo,
  useRef,
  useState,
  type MutableRefObject,
} from "react";
import * as THREE from "three";
import type { OrbitControls as OrbitImpl } from "three-stdlib";
import { BUILDINGS, type BuildingName } from "../content/buildings";
import { EVENTS, type Mission, type Plan } from "../domain/mission";
import { TARGETS, type TargetId } from "../domain/guidance";
import { moveWithSlide, type WorldMode } from "../domain/exploration";

export type WorldProps = {
  mode: WorldMode;
  cameraMode: "orbit" | "walk";
  selected: BuildingName | null;
  onSelect: (name: BuildingName) => void;
  onLand: () => void;
  onDescend: () => void;
  mission: Mission;
  plan: Plan;
  quality: "high" | "low";
  paused: boolean;
  onFail: () => void;
  onNear: (name: TargetId | null) => void;
  onInteract: (target: TargetId) => void;
  guideTarget?: TargetId;
  focus: { target: TargetId; serial: number } | null;
  cinematic: boolean;
  onArrival: () => void;
  routePreview: boolean;
  movement: MutableRefObject<[number, number]>;
  recenter: number;
  onSample: () => void;
};
const MODEL = "/assets/models/";
const OBSTACLES = [...BUILDINGS, { x: 0, z: 20, halfX: 3.6, halfZ: 3.6 }];
function useReducedMotion() {
  const [reduced, setReduced] = useState(
    () => window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  );
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(mq.matches);
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);
  return reduced;
}
function useModel(asset: string) {
  const { scene } = useGLTF(`${MODEL}${asset}.glb`);
  return useMemo(() => {
    const clone = scene.clone(true);
    clone.traverse((o) => {
      if (o instanceof THREE.Mesh) {
        // Large solid surfaces cast shadows; fine trim and glazing do not.
        o.castShadow =
          (!!o.geometry.index && o.geometry.index.count > 6000) ||
          (asset === "commander" && o.name.includes("Commander"));
        o.receiveShadow = true;
        o.material = Array.isArray(o.material)
          ? o.material.map((m) => m.clone())
          : o.material.clone();
        // Tinted alpha glazing keeps the view into facilities without rendering
        // the entire outpost a second time for physical refraction.
        for (const material of Array.isArray(o.material)
          ? o.material
          : [o.material]) {
          if (material instanceof THREE.MeshPhysicalMaterial)
            material.transmission = 0;
        }
      }
    });
    return clone;
  }, [scene, asset]);
}
function Model({
  asset,
  ...props
}: { asset: string } & Omit<React.ComponentProps<"group">, "ref">) {
  const scene = useModel(asset);
  return (
    <group {...props}>
      <primitive object={scene} />
    </group>
  );
}
function Ready({ onReady }: { onReady: () => void }) {
  useEffect(onReady, [onReady]);
  return null;
}
function FrameBudget({ paused }: { paused: boolean }) {
  const { invalidate } = useThree();
  useEffect(() => {
    const timer = window.setInterval(() => invalidate(), paused ? 250 : 33);
    return () => window.clearInterval(timer);
  }, [invalidate, paused]);
  return null;
}
function Globe({ onLand }: { onLand: () => void }) {
  const { camera } = useThree();
  const reduced = useReducedMotion();
  useEffect(() => {
    camera.position.set(0, 1, 11);
    camera.lookAt(0, 0, 0);
  }, [camera]);
  const color = useTexture("/assets/mars-color.jpg");
  color.colorSpace = THREE.SRGBColorSpace;
  return (
    <>
      <color attach="background" args={["#060e19"]} />
      <ambientLight intensity={0.45} />
      <directionalLight position={[-8, 5, 8]} intensity={3.8} color="#ffe5ca" />
      <mesh rotation={[0.12, -0.5, 0]}>
        <sphereGeometry args={[4, 96, 64]} />
        <meshStandardMaterial map={color} roughness={1} />
        <mesh
          position={[1.6, 0.7, 3.6]}
          onClick={(e) => {
            e.stopPropagation();
            if (e.delta < 5) onLand();
          }}
        >
          <sphereGeometry args={[0.07, 16, 12]} />
          <meshBasicMaterial color="#75e7db" />
          <Html distanceFactor={5} position={[0, 0.2, 0]} center>
            <button className="world-marker" onClick={onLand}>
              <span className="marker-dot" /> ARES OUTPOST{" "}
              <small>Begin your mission →</small>
            </button>
          </Html>
        </mesh>
      </mesh>
      <OrbitControls
        enablePan={false}
        minDistance={7}
        maxDistance={16}
        autoRotate={!reduced}
        autoRotateSpeed={0.15}
      />
    </>
  );
}
function Facility({
  b,
  selected,
  showLabel,
  onSelect,
  plan,
  event,
  mission,
}: {
  b: (typeof BUILDINGS)[number];
  selected: boolean;
  showLabel: boolean;
  onSelect: WorldProps["onSelect"];
  plan: Plan;
  event: string;
  mission: Mission;
}) {
  const [hover, setHover] = useState(false);
  const scene = useModel(b.asset);
  const active =
    b.asset === "life-support"
      ? plan.oxygenOn
      : b.asset === "greenhouse"
        ? plan.greenhouseOn
        : b.asset === "shelter"
          ? plan.task === "shelter"
          : b.asset === "communications"
            ? !!mission.pendingHint || plan.task === "askEarth"
            : true;
  useEffect(() => {
    scene.traverse((o) => {
      if (o instanceof THREE.Mesh) {
        const mats = Array.isArray(o.material) ? o.material : [o.material];
        for (const m of mats)
          if (
            m instanceof THREE.MeshStandardMaterial &&
            (m.emissiveIntensity > 0 || /emiss|status|grow|cyan/i.test(m.name))
          ) {
            m.emissiveIntensity = active
              ? event === "dust"
                ? 0.3
                : 0.8
              : 0.02;
          }
      }
    });
  }, [scene, active, event]);
  const select = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation();
    if (e.delta < 5) onSelect(b.name);
  };
  return (
    <group
      position={[b.x, 0, b.z]}
      onClick={select}
      onPointerOver={(e) => {
        e.stopPropagation();
        setHover(true);
      }}
      onPointerOut={() => setHover(false)}
    >
      <primitive object={scene} />
      {(b.asset === "power" || b.asset === "storage") && (
        <Model asset={`${b.asset}-equipment`} />
      )}
      {(selected || hover) && (
        <>
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.05, 0]}>
            <ringGeometry
              args={[
                Math.max(b.halfX, b.halfZ) + 0.4,
                Math.max(b.halfX, b.halfZ) + 0.53,
                64,
              ]}
            />
            <meshBasicMaterial
              color="#85f4e6"
              transparent
              opacity={0.75}
              depthWrite={false}
            />
          </mesh>
          {showLabel && (
            <Html
              center
              position={[0, 7, 0]}
              distanceFactor={45}
              style={{ pointerEvents: "none" }}
            >
              <div className="object-label">
                {b.name}
                <small>{active ? "PLANNED ACTIVE" : "PLANNED STANDBY"}</small>
              </div>
            </Html>
          )}
        </>
      )}
    </group>
  );
}
function Rocks() {
  const { scene } = useGLTF(`${MODEL}rock.glb`);
  const mesh = useMemo(() => {
    let found: THREE.Mesh | undefined;
    scene.traverse((o) => {
      if (o instanceof THREE.Mesh) found = o;
    });
    return found!;
  }, [scene]);
  const ref = useRef<THREE.InstancedMesh>(null);
  useEffect(() => {
    let seed = 261;
    const rand = () => {
      seed = (seed * 16807) % 2147483647;
      return seed / 2147483647;
    };
    const dummy = new THREE.Object3D();
    for (let i = 0; i < 220; i++) {
      const a = rand() * Math.PI * 2;
      const r = 47 + rand() * 68;
      const s = 0.25 + rand() * 1.5;
      dummy.position.set(Math.cos(a) * r, 0, Math.sin(a) * r);
      dummy.scale.set(s, s, s);
      dummy.rotation.set(0, rand() * 6.28, 0);
      dummy.updateMatrix();
      ref.current!.setMatrixAt(i, dummy.matrix);
    }
    ref.current!.instanceMatrix.needsUpdate = true;
  }, []);
  return (
    <instancedMesh
      ref={ref}
      args={[mesh.geometry, mesh.material, 220]}
      castShadow
      receiveShadow
    />
  );
}
function Dust({ strong }: { strong: boolean }) {
  const reduced = useReducedMotion();
  const ref = useRef<THREE.Points>(null);
  const points = useMemo(() => {
    const a = new Float32Array(180 * 3);
    for (let i = 0; i < 180; i++) {
      a[i * 3] = Math.sin(i * 83.1) * 65;
      a[i * 3 + 1] = 0.3 + (i % 13) * 0.4;
      a[i * 3 + 2] = Math.cos(i * 63.9) * 65;
    }
    return a;
  }, []);
  useFrame((_, dt) => {
    if (ref.current && !reduced) {
      ref.current.position.x =
        (ref.current.position.x + dt * (strong ? 1.5 : 0.15)) % 20;
    }
  });
  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[points, 3]} />
      </bufferGeometry>
      <pointsMaterial
        size={strong ? 0.085 : 0.035}
        color="#e9b088"
        transparent
        opacity={strong ? 0.35 : 0.12}
        depthWrite={false}
      />
    </points>
  );
}
function Astronaut({
  scene,
  phase,
  walking,
  tint,
}: {
  scene: THREE.Group;
  phase: number;
  walking: boolean;
  tint?: string;
}) {
  const g = useRef<THREE.Group>(null);
  const blend = useRef(0);
  useEffect(() => {
    if (tint)
      scene.traverse((o) => {
        if (o instanceof THREE.Mesh) {
          const mats = Array.isArray(o.material) ? o.material : [o.material];
          for (const m of mats)
            if (/ochre/i.test(m.name))
              (m as THREE.MeshStandardMaterial).color.set(tint);
        }
      });
  }, [scene, tint]);
  useFrame(({ clock }, dt) => {
    blend.current = THREE.MathUtils.damp(blend.current, walking ? 1 : 0, 9, dt);
    const t = clock.elapsedTime * 9 + phase;
    const swing =
      Math.sin(t) * 0.45 * blend.current +
      Math.sin(clock.elapsedTime + phase) * 0.025 * (1 - blend.current);
    for (const [name, angle] of [
      ["LeftLeg", swing],
      ["RightLeg", -swing],
      ["LeftArm", -swing * 0.7],
      ["RightArm", swing * 0.7],
    ] as const) {
      const node = scene.getObjectByName(name);
      if (node) node.rotation.x = angle;
    }
    if (g.current)
      g.current.position.y = walking ? Math.abs(Math.cos(t)) * 0.035 : 0;
  });
  return (
    <group ref={g}>
      <primitive object={scene} />
    </group>
  );
}
function DestinationMarker({
  target,
  onInteract,
}: {
  target: TargetId;
  onInteract: (t: TargetId) => void;
}) {
  const beacon = useRef<THREE.Group>(null);
  const reduced = useReducedMotion();
  useFrame(({ clock }) => {
    if (beacon.current)
      beacon.current.position.y = reduced
        ? 7
        : 7 + Math.sin(clock.elapsedTime * 2) * 0.35;
  });
  return (
    <group position={TARGETS[target].position}>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.12, 0]}>
        <ringGeometry args={[2.5, 2.7, 48]} />
        <meshBasicMaterial
          color="#69ffe4"
          transparent
          opacity={0.85}
          depthWrite={false}
        />
      </mesh>
      <group ref={beacon} position={[0, 7, 0]}>
        <mesh rotation={[Math.PI, 0, 0]}>
          <coneGeometry args={[0.55, 1.1, 4]} />
          <meshBasicMaterial color="#80ffe7" />
        </mesh>
      </group>
      <Html center position={[0, 8.7, 0]} distanceFactor={35}>
        <button
          className="destination-beacon"
          onClick={() => onInteract(target)}
        >
          GO: {TARGETS[target].name}
          <small>
            {target === "maya" || target === "alex"
              ? "Talk / E / tap"
              : "Inspect / E / tap"}
          </small>
        </button>
      </Html>
    </group>
  );
}
function Flight({
  onComplete,
  paused,
}: {
  onComplete: () => void;
  paused: boolean;
}) {
  const { camera } = useThree();
  const t = useRef(0);
  const craft = useRef<THREE.Group>(null);
  const done = useRef(false);
  const [color, earthColor] = useTexture([
    "/assets/mars-color.jpg",
    "/assets/earth-color.jpg",
  ]);
  color.colorSpace = earthColor.colorSpace = THREE.SRGBColorSpace;
  const stars = useMemo(() => {
    const a = new Float32Array(900);
    for (let i = 0; i < 300; i++) {
      a[i * 3] = Math.sin(i * 73.7) * 100;
      a[i * 3 + 1] = Math.cos(i * 39.9) * 70;
      a[i * 3 + 2] = -45 - Math.abs(Math.sin(i * 9.3)) * 60;
    }
    return a;
  }, []);
  useEffect(() => {
    camera.position.set(
      0,
      6,
      camera instanceof THREE.PerspectiveCamera
        ? Math.max(
            32,
            22 / (Math.tan(THREE.MathUtils.degToRad(24)) * camera.aspect),
          )
        : 32,
    );
    camera.lookAt(0, 0, 0);
  }, [camera]);
  useFrame((_, dt) => {
    if (paused) return;
    t.current += Math.min(dt, 0.25);
    const p = Math.min(1, t.current / 6);
    if (craft.current) {
      craft.current.position.set(-8 + 16 * p, Math.sin(p * Math.PI) * 2, 2);
      craft.current.rotation.z = -0.2;
    }
    if (p === 1 && !done.current) {
      done.current = true;
      onComplete();
    }
  });
  return (
    <>
      <color attach="background" args={["#050d1b"]} />
      <points>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[stars, 3]} />
        </bufferGeometry>
        <pointsMaterial
          color="#d7e9f3"
          size={0.16}
          sizeAttenuation
          transparent
          opacity={0.7}
        />
      </points>
      <ambientLight intensity={1.2} />
      <directionalLight position={[-4, 8, 10]} intensity={3} />
      <mesh position={[-14, 0, -7]}>
        <sphereGeometry args={[5, 48, 32]} />
        <meshStandardMaterial map={earthColor} roughness={0.8} />
        <Html center position={[0, -6, 0]}>
          <span className="planet-name">EARTH</span>
        </Html>
      </mesh>
      <mesh position={[13, 0, -9]}>
        <sphereGeometry args={[5.5, 64, 48]} />
        <meshStandardMaterial map={color} />
        <Html center position={[0, -6.5, 0]}>
          <span className="planet-name">MARS</span>
        </Html>
      </mesh>
      <group ref={craft} scale={0.3}>
        <Model asset="lander" />
      </group>
    </>
  );
}
function Arrival(props: WorldProps) {
  const [flight, setFlight] = useState(true);
  return flight ? (
    <Flight paused={props.paused} onComplete={() => setFlight(false)} />
  ) : (
    <Surface {...props} />
  );
}
function Surface(props: WorldProps) {
  const reduced = useReducedMotion();
  const landingCraft = useRef<THREE.Group>(null);
  const arrivalClock = useRef(0);
  const arrivalDone = useRef(false);
  const focusTween = useRef<{
    position: THREE.Vector3;
    target: THREE.Vector3;
  } | null>(null);
  const { camera, gl } = useThree();
  const orbit = useRef<OrbitImpl>(null);
  const player = useRef<THREE.Group>(null);
  const pos = useRef(new THREE.Vector3(6, 0, 11));
  const cameraRecoveryHeight = useRef<number | null>(null);
  const keys = useRef(new Set<string>());
  const yaw = useRef(Math.PI);
  const [walking, setWalking] = useState(false);
  const lastWalk = useRef(false);
  const commander = useModel("commander");
  const alex = useModel("commander");
  const maya = useModel("commander");
  const nearRef = useRef<TargetId | null>(null);
  const dusty = EVENTS[Math.min(props.mission.turn - 1, 5)] === "dust";
  const rover = useRef<THREE.Group>(null);
  const journey = useRef(0);
  const sampleCount = props.mission.samples;
  const previousSample = useRef(sampleCount);
  const sample = useRef<THREE.Group>(null);
  const [travel, setTravel] = useState(false);
  useEffect(() => {
    if (sampleCount > previousSample.current) {
      journey.current = reduced ? 1 : 0;
      setTravel(true);
    }
    previousSample.current = sampleCount;
  }, [sampleCount, reduced]);
  useEffect(() => {
    if (props.routePreview && sampleCount === 0) {
      journey.current = reduced ? 1 : 0;
      setTravel(true);
    }
  }, [props.routePreview, sampleCount, reduced]);
  useEffect(() => {
    const keydown = (e: KeyboardEvent) => {
      if (
        props.paused ||
        props.cinematic ||
        document.querySelector("dialog[open]") ||
        (e.target instanceof HTMLElement &&
          (/INPUT|SELECT|TEXTAREA/.test(e.target.tagName) ||
            e.target.isContentEditable))
      )
        return;
      if (
        [
          "KeyW",
          "KeyA",
          "KeyS",
          "KeyD",
          "ArrowUp",
          "ArrowDown",
          "ArrowLeft",
          "ArrowRight",
          "KeyE",
        ].includes(e.code)
      ) {
        e.preventDefault();
        keys.current.add(e.code);
      }
      if (e.code === "KeyE" && nearRef.current)
        props.onInteract(nearRef.current);
    };
    const keyup = (e: KeyboardEvent) => keys.current.delete(e.code);
    const clear = () => keys.current.clear();
    window.addEventListener("keydown", keydown);
    window.addEventListener("keyup", keyup);
    window.addEventListener("blur", clear);
    document.addEventListener("visibilitychange", clear);
    return () => {
      window.removeEventListener("keydown", keydown);
      window.removeEventListener("keyup", keyup);
      window.removeEventListener("blur", clear);
      document.removeEventListener("visibilitychange", clear);
    };
  }, [props.paused, props.onInteract]);
  useEffect(() => {
    keys.current.clear();
    if (props.cameraMode === "orbit" || props.mode === "region") {
      camera.position.set(62, 53, 72);
      orbit.current?.target.set(0, 0, -7);
    } else {
      camera.position
        .copy(pos.current)
        .add(
          new THREE.Vector3(
            0,
            4.3,
            camera instanceof THREE.PerspectiveCamera && camera.aspect < 0.8
              ? 10
              : 7,
          ),
        );
      orbit.current?.target.copy(pos.current).add(new THREE.Vector3(0, 1.2, 0));
    }
    orbit.current?.update();
  }, [camera, props.cameraMode, props.mode, props.recenter]);
  useEffect(() => {
    if (!props.focus || props.cinematic) return;
    const p = TARGETS[props.focus.target].position;
    focusTween.current = {
      position: new THREE.Vector3(p[0] + 14, 16, p[2] + 20),
      target: new THREE.Vector3(p[0], 1.5, p[2]),
    };
  }, [props.focus, props.cinematic]);
  useEffect(() => {
    if (props.cinematic) {
      camera.position.set(18, 15, 48);
      orbit.current?.target.set(0, 5, 20);
      orbit.current?.update();
    }
  }, [props.cinematic, camera]);
  useFrame((state, rawDt) => {
    const dt = Math.min(rawDt, 0.1);
    if (props.cinematic && !props.paused) {
      arrivalClock.current += Math.min(rawDt, 0.25);
      const t = Math.min(1, arrivalClock.current / 6);
      if (landingCraft.current)
        landingCraft.current.position.y = 0.7 + 32 * (1 - t) * (1 - t);
      const settle = THREE.MathUtils.smoothstep(t, 0.65, 1);
      const followDistance =
        camera instanceof THREE.PerspectiveCamera && camera.aspect < 0.8
          ? 10
          : 7;
      camera.position.set(
        THREE.MathUtils.lerp(18, pos.current.x, settle),
        THREE.MathUtils.lerp(15, 4.3, settle),
        THREE.MathUtils.lerp(48, pos.current.z + followDistance, settle),
      );
      camera.lookAt(
        THREE.MathUtils.lerp(0, pos.current.x, settle),
        THREE.MathUtils.lerp(5, 1.2, settle),
        THREE.MathUtils.lerp(20, pos.current.z, settle),
      );
      if (t === 1 && !arrivalDone.current) {
        arrivalDone.current = true;
        props.onArrival();
      }
    }
    if (focusTween.current && !props.cinematic) {
      const f = focusTween.current;
      const a = reduced ? 1 : 1 - Math.exp(-dt * 4);
      camera.position.lerp(f.position, a);
      orbit.current?.target.lerp(f.target, a);
      if (camera.position.distanceTo(f.position) < 0.05)
        focusTween.current = null;
      orbit.current?.update();
    }
    const isWalk =
      props.cameraMode === "walk" &&
      props.mode === "surface" &&
      !props.paused &&
      !props.cinematic;
    const k = keys.current;
    let dx = isWalk
      ? Number(k.has("KeyD") || k.has("ArrowRight")) -
        Number(k.has("KeyA") || k.has("ArrowLeft")) +
        props.movement.current[0]
      : 0;
    let dz = isWalk
      ? Number(k.has("KeyS") || k.has("ArrowDown")) -
        Number(k.has("KeyW") || k.has("ArrowUp")) +
        props.movement.current[1]
      : 0;
    const moving = Math.hypot(dx, dz) > 0.01;
    if (moving) {
      const length = Math.hypot(dx, dz);
      dx /= length;
      dz /= length;
      const forward = new THREE.Vector3();
      camera.getWorldDirection(forward);
      forward.y = 0;
      forward.normalize();
      const right = new THREE.Vector3().crossVectors(
        forward,
        new THREE.Vector3(0, 1, 0),
      );
      const delta = right
        .multiplyScalar(dx)
        .add(forward.multiplyScalar(-dz))
        .multiplyScalar(dt * 2.4);
      const [x, z] = moveWithSlide(
        [pos.current.x, pos.current.z],
        [delta.x, delta.z],
        OBSTACLES,
      );
      const shift = new THREE.Vector3(x - pos.current.x, 0, z - pos.current.z);
      pos.current.set(x, 0, z);
      camera.position.add(shift);
      orbit.current?.target.add(shift);
      const target = Math.atan2(delta.x, delta.z);
      yaw.current +=
        Math.atan2(
          Math.sin(target - yaw.current),
          Math.cos(target - yaw.current),
        ) * Math.min(1, dt * 12);
    }
    if (lastWalk.current !== moving) {
      lastWalk.current = moving;
      setWalking(moving);
    }
    if (player.current) {
      player.current.position.copy(pos.current);
      player.current.rotation.y = yaw.current;
    }
    let near: TargetId | null = null;
    let best = 4;
    for (const b of BUILDINGS) {
      const d = Math.hypot(
        Math.max(0, Math.abs(pos.current.x - b.x) - b.halfX),
        Math.max(0, Math.abs(pos.current.z - b.z) - b.halfZ),
      );
      if (d < best) {
        best = d;
        near = b.name;
      }
    }
    for (const id of ["maya", "alex", "rover", "sample"] as const) {
      const t = TARGETS[id].position;
      const d = Math.hypot(pos.current.x - t[0], pos.current.z - t[2]);
      if (d < best) {
        best = d;
        near = id;
      }
    }
    if (near !== nearRef.current) {
      nearRef.current = near;
      props.onNear(near);
    }
    if (isWalk) {
      // Keep the camera above structures along the player-to-camera segment.
      let safeY = 2;
      for (let i = 1; i <= 12; i++) {
        const t = i / 12;
        const x = THREE.MathUtils.lerp(pos.current.x, camera.position.x, t);
        const z = THREE.MathUtils.lerp(pos.current.z, camera.position.z, t);
        if (
          OBSTACLES.some(
            (b) =>
              Math.abs(x - b.x) < b.halfX + 0.3 &&
              Math.abs(z - b.z) < b.halfZ + 0.3,
          )
        )
          safeY = 10;
      }
      if (safeY === 10 && cameraRecoveryHeight.current === null)
        cameraRecoveryHeight.current = camera.position.y;
      if (safeY === 10 && camera.position.y < safeY)
        camera.position.y = THREE.MathUtils.damp(
          camera.position.y,
          safeY,
          10,
          dt,
        );
      if (safeY !== 10 && cameraRecoveryHeight.current !== null) {
        camera.position.y = THREE.MathUtils.damp(
          camera.position.y,
          cameraRecoveryHeight.current,
          8,
          dt,
        );
        if (Math.abs(camera.position.y - cameraRecoveryHeight.current) < 0.02)
          cameraRecoveryHeight.current = null;
      }
    }
    if (travel && rover.current) {
      journey.current = Math.min(1, journey.current + dt / 9);
      const t = journey.current;
      const x = THREE.MathUtils.lerp(29, 43, t);
      const z = THREE.MathUtils.lerp(26, -5, t);
      rover.current.position.set(x, 0, z);
      rover.current.rotation.y = -0.42;
      if (t === 1) setTravel(false);
    }
    if (sample.current)
      sample.current.rotation.y = state.clock.elapsedTime * 0.15;
    // Diagnostics use the actual renderer counters, refreshed without React updates.
    const diagnostics = document.getElementById("render-stats");
    if (diagnostics && Math.floor(state.clock.elapsedTime * 2) % 2 === 0)
      diagnostics.textContent = `${gl.info.render.calls} draws · ${(gl.info.render.triangles / 1000).toFixed(0)}K tris`;
  });
  const select =
    props.mode === "region" ? () => props.onDescend() : props.onSelect;
  return (
    <>
      <color attach="background" args={[dusty ? "#b89076" : "#d9b59b"]} />
      <fog
        attach="fog"
        args={[
          dusty ? "#b89076" : "#d9b59b",
          dusty ? 45 : 100,
          dusty ? 160 : 280,
        ]}
      />
      <hemisphereLight args={["#ecd8bc", "#7a4431", 1.6]} />
      <directionalLight
        position={[-40, 65, 35]}
        intensity={dusty ? 1.7 : 3.2}
        color="#fff0d2"
        castShadow={props.quality === "high"}
        shadow-mapSize={[2048, 2048]}
        shadow-camera-left={-55}
        shadow-camera-right={55}
        shadow-camera-top={55}
        shadow-camera-bottom={-55}
        shadow-normalBias={0.04}
        shadow-bias={-0.0002}
      />
      <Model asset="terrain" />
      <Model asset="paths" />
      <Rocks />
      {BUILDINGS.map((b) => (
        <Facility
          key={b.name}
          b={b}
          selected={props.selected === b.name || props.guideTarget === b.name}
          showLabel={props.guideTarget !== b.name}
          onSelect={select}
          plan={props.plan}
          event={dusty ? "dust" : "ordinary"}
          mission={props.mission}
        />
      ))}
      <Model asset="landing-pad" position={[0, -0.05, 20]} />
      <group ref={landingCraft} position={[0, 0.7, 20]}>
        <Model asset="lander" />
      </group>
      <group
        ref={rover}
        position={sampleCount > 0 ? [43, 0, -5] : [29, 0, 26]}
        onClick={(e) => {
          e.stopPropagation();
          if (e.delta < 5) props.onInteract("rover");
        }}
      >
        <Model asset="rover" />
      </group>
      <Line
        points={[
          [29, 0.07, 26],
          [36, 0.07, 13],
          [43, 0.07, -5],
        ]}
        color={sampleCount ? "#73d4c8" : "#cba778"}
        lineWidth={1}
        dashed
        dashSize={0.8}
        gapSize={0.6}
      />
      <group
        ref={sample}
        position={[43, 0, -5]}
        onClick={(e) => {
          e.stopPropagation();
          if (e.delta < 5) props.onInteract("sample");
        }}
      >
        <Model asset="rock" scale={[1.2, 1.6, 1.2]} />
        <Html center position={[0, 2, 0]} distanceFactor={45}>
          <button
            className="sample-marker"
            onClick={() => props.onInteract("sample")}
          >
            {sampleCount ? "Sample recovered" : "Geology stop"}{" "}
            <small>
              {sampleCount ? "Research logged" : "Inspect rover mission"}
            </small>
          </button>
        </Html>
      </group>
      <group ref={player}>
        <Astronaut scene={commander} phase={0} walking={walking} />
      </group>
      <group
        position={[-7, 0, 8]}
        rotation={[0, -0.6, 0]}
        onClick={(e) => {
          e.stopPropagation();
          if (e.delta < 5) props.onInteract("alex");
        }}
      >
        <Astronaut scene={alex} phase={2} walking={false} tint="#dd7b35" />
        <Html position={[0, 2.4, 0]} center distanceFactor={20}>
          <button
            className="crew-label"
            onClick={() => props.onInteract("alex")}
          >
            Talk to Alex
          </button>
        </Html>
      </group>
      <group
        position={[6, 0, 6]}
        rotation={[0, 1, 0]}
        onClick={(e) => {
          e.stopPropagation();
          if (e.delta < 5) props.onInteract("maya");
        }}
      >
        <Astronaut scene={maya} phase={4} walking={false} tint="#46bdb6" />
        <Html position={[0, 2.4, 0]} center distanceFactor={20}>
          <button
            className="crew-label"
            onClick={() => props.onInteract("maya")}
          >
            Talk to Dr. Maya
          </button>
        </Html>
      </group>
      {props.guideTarget && !props.cinematic && (
        <DestinationMarker
          target={props.guideTarget}
          onInteract={props.onInteract}
        />
      )}
      {props.routePreview && (
        <Line
          points={[
            [29, 0.15, 26],
            [36, 0.15, 13],
            [43, 0.15, -5],
          ]}
          color="#79f4de"
          lineWidth={3}
          dashed
          dashSize={1}
          gapSize={0.4}
        />
      )}
      <Dust strong={dusty} />
      {props.mode === "region" && (
        <Html center position={[0, 12, 0]}>
          <button className="world-marker" onClick={props.onDescend}>
            ARES OUTPOST <small>Descend to the base →</small>
          </button>
        </Html>
      )}
      <OrbitControls
        ref={orbit}
        enabled={!props.paused && !props.cinematic}
        onStart={() => {
          focusTween.current = null;
        }}
        enablePan={props.cameraMode === "orbit"}
        enableDamping
        dampingFactor={0.08}
        minDistance={props.cameraMode === "walk" ? 4 : 25}
        maxDistance={props.cameraMode === "walk" ? 12 : 150}
        minPolarAngle={0.2}
        maxPolarAngle={props.cameraMode === "walk" ? 1.42 : 1.35}
        target={[0, 0, -7]}
        mouseButtons={{
          LEFT: THREE.MOUSE.ROTATE,
          MIDDLE: THREE.MOUSE.DOLLY,
          RIGHT: THREE.MOUSE.PAN,
        }}
      />
    </>
  );
}
export default function Outpost(props: WorldProps) {
  const [ready, setReady] = useState(false);
  const { active, progress } = useProgress();
  const reduced = useReducedMotion();
  useEffect(() => {
    if (props.cinematic && reduced) props.onArrival();
  }, [props.cinematic, reduced, props.onArrival]);
  return (
    <>
      <Canvas
        frameloop="demand"
        shadows={props.quality === "high" ? "percentage" : false}
        dpr={[1, props.quality === "high" ? 1.5 : 1]}
        camera={{ position: [0, 1, 11], fov: 48, near: 0.1, far: 500 }}
        gl={{
          antialias: true,
          powerPreference: "high-performance",
        }}
        onCreated={({ gl }) => {
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = 1;
          gl.domElement.addEventListener(
            "webglcontextlost",
            (e) => {
              e.preventDefault();
              props.onFail();
            },
            { once: true },
          );
        }}
        onPointerMissed={() => {}}
        aria-label="Interactive 3D Mars. Select facilities with the object chooser or explore with WASD and E."
      >
        <FrameBudget paused={props.paused} />
        <Suspense fallback={null}>
          {props.cinematic ? (
            <Arrival {...props} />
          ) : props.mode === "planet" ? (
            <Globe onLand={props.onLand} />
          ) : (
            <Surface {...props} />
          )}
          <Ready onReady={() => setReady(true)} />
        </Suspense>
      </Canvas>
      {(!ready || active) && (
        <div className="world-loading">
          <span className="loading-orbit" />
          Preparing your expedition…
          <small>Loading local 3D models · {Math.round(progress)}%</small>
        </div>
      )}
    </>
  );
}
