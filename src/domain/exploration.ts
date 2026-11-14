import type { BuildingName } from "../content/buildings";
export type WorldMode = "planet" | "region" | "surface";
export type StoryStage =
  | "landing"
  | "outpost"
  | "power"
  | "oxygen"
  | "food"
  | "research"
  | "review"
  | "independent";
export type StoryAction =
  | { type: "land" | "descend" | "commit" }
  | { type: "select"; building: BuildingName }
  | { type: "configure"; system: "oxygen" | "food" | "research" };
export function advanceStory(
  stage: StoryStage,
  action: StoryAction,
): StoryStage {
  if (stage === "landing" && action.type === "land") return "outpost";
  if (stage === "outpost" && action.type === "descend") return "power";
  if (
    stage === "power" &&
    action.type === "select" &&
    action.building === "Power station"
  )
    return "oxygen";
  if (action.type === "configure") {
    if (stage === "oxygen" && action.system === "oxygen") return "food";
    if (stage === "food" && action.system === "food") return "research";
    if (stage === "research" && action.system === "research") return "review";
  }
  if (stage === "review" && action.type === "commit") return "independent";
  return stage;
}
export const STORY: Record<
  StoryStage,
  { speaker: string; title: string; text: string; target?: BuildingName }
> = {
  landing: {
    speaker: "NOVA",
    title: "Your crew is waiting.",
    text: "Welcome, Commander. Find Ares Outpost on Mars to begin your six-turn mission.",
  },
  outpost: {
    speaker: "NOVA",
    title: "A small home. A big mission.",
    text: "This is our illustrated landing region. Select the outpost to meet your crew on the surface.",
  },
  power: {
    speaker: "Alex",
    title: "Bring the base to life.",
    text: "Inspect the solar array. Sunlight powers everything here, but our battery can only store 20 energy.",
    target: "Power station",
  },
  oxygen: {
    speaker: "Alex",
    title: "Help the crew breathe.",
    text: "Open life support and choose its power setting. Oxygen production needs 4 energy; stored oxygen keeps us breathing.",
    target: "Life support",
  },
  food: {
    speaker: "Dr. Maya",
    title: "Plan tomorrow’s meals.",
    text: "Choose greenhouse lighting. Two consecutive powered turns grow food, using 3 energy and 1 water each turn.",
    target: "Greenhouse",
  },
  research: {
    speaker: "Dr. Maya",
    title: "One crew. One task.",
    text: "Visit the science lab. Choose research for 4 energy or conserve power. Review every reserve before committing.",
    target: "Science lab",
  },
  review: {
    speaker: "NOVA",
    title: "Ready to make a decision?",
    text: "Review your plan. Exploration is free. Only advancing the mission spends resources and resolves your decisions.",
  },
  independent: {
    speaker: "NOVA",
    title: "You have the command.",
    text: "Explore your base, choose one crew task, and review your reserves. Every decision matters.",
  },
};
export type Obstacle = { x: number; z: number; halfX: number; halfZ: number };
export function canOccupy(
  x: number,
  z: number,
  obstacles: readonly Obstacle[],
  radius = 0.48,
): boolean {
  return (
    Math.hypot(x, z) < 52 &&
    !obstacles.some(
      (o) =>
        Math.abs(x - o.x) < o.halfX + radius &&
        Math.abs(z - o.z) < o.halfZ + radius,
    )
  );
}
export function moveWithSlide(
  position: [number, number],
  delta: [number, number],
  obstacles: readonly Obstacle[],
): [number, number] {
  let [x, z] = position;
  const steps = Math.max(1, Math.ceil(Math.hypot(...delta) / 0.2));
  for (let i = 0; i < steps; i++) {
    if (canOccupy(x + delta[0] / steps, z, obstacles)) x += delta[0] / steps;
    if (canOccupy(x, z + delta[1] / steps, obstacles)) z += delta[1] / steps;
  }
  return [x, z];
}
