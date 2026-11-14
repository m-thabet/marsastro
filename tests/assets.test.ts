import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
const assets = [
  "terrain",
  "power-equipment",
  "storage-equipment",
  "paths",
  "rock",
  "habitat",
  "power",
  "life-support",
  "greenhouse",
  "landing-pad",
  "laboratory",
  "communications",
  "storage",
  "rover",
  "shelter",
  "commander",
  "lander",
];
type Gltf = {
  buffers: { uri?: string }[];
  images?: { uri?: string }[];
  nodes: {
    name?: string;
    translation?: number[];
    rotation?: number[];
    scale?: number[];
    matrix?: number[];
  }[];
  accessors: {
    bufferView?: number;
    byteOffset?: number;
    componentType: number;
    count: number;
    type: string;
  }[];
  bufferViews: { byteOffset?: number; byteStride?: number }[];
  meshes: { primitives: { attributes: { POSITION: number } }[] }[];
};
describe("actual runtime asset exports", () => {
  for (const asset of assets)
    it(`${asset} is a self-contained GLB with finite positions`, () => {
      const bytes = readFileSync(
        resolve("public/assets/models", asset + ".glb"),
      );
      expect(bytes.toString("ascii", 0, 4)).toBe("glTF");
      expect(bytes.readUInt32LE(4)).toBe(2);
      expect(bytes.readUInt32LE(8)).toBe(bytes.length);
      const jsonSize = bytes.readUInt32LE(12);
      const gltf = JSON.parse(
        bytes.toString("utf8", 20, 20 + jsonSize),
      ) as Gltf;
      expect(gltf.buffers.every((b) => !b.uri)).toBe(true);
      expect((gltf.images ?? []).every((b) => !b.uri)).toBe(true);
      expect(gltf.meshes.length).toBeGreaterThan(0);
      for (const n of gltf.nodes)
        for (const key of [
          "translation",
          "rotation",
          "scale",
          "matrix",
        ] as const)
          expect((n[key] ?? []).every(Number.isFinite)).toBe(true);
      for (const mesh of gltf.meshes)
        for (const primitive of mesh.primitives) {
          const accessor = gltf.accessors[primitive.attributes.POSITION];
          expect(accessor.componentType).toBe(5126);
          const view = gltf.bufferViews[accessor.bufferView!];
          const base =
            20 +
            jsonSize +
            8 +
            (view.byteOffset ?? 0) +
            (accessor.byteOffset ?? 0);
          const stride = view.byteStride ?? 12;
          for (let i = 0; i < accessor.count; i++)
            for (let axis = 0; axis < 3; axis++)
              if (
                !Number.isFinite(
                  bytes.readFloatLE(base + i * stride + axis * 4),
                )
              )
                throw new Error(`${asset}: non-finite geometry`);
        }
      if (asset === "commander")
        for (const name of ["LeftLeg", "RightLeg", "LeftArm", "RightArm"])
          expect(gltf.nodes.some((n) => n.name === name)).toBe(true);
    });
  it("keeps total initial visible geometry under the documented 200K budget", () => {
    const report = JSON.parse(
      readFileSync(resolve("public/assets/models/asset-report.json"), "utf8"),
    ) as { asset: string; triangles: number; bytes: number }[];
    const triangles =
      report.reduce((s, r) => s + r.triangles, 0) + 2 * 5200 + 219 * 80;
    expect(triangles).toBeLessThan(200000);
    expect(report.reduce((s, r) => s + r.bytes, 0)).toBeLessThan(8000000);
  });
});
