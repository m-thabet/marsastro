import { z } from "zod";
import { decodeSave, loadMission, planSchema, SAVE_KEY } from "./storage";
import { defaultPlan, type Mission, type Plan } from "../domain/mission";
import {
  initialGuide,
  nextTurnNode,
  NODES,
  type GuideState,
} from "../domain/guidance";
const guideSchema = z.object({
  version: z.literal(2),
  node: z.enum(NODES),
  enabled: z.boolean(),
  learned: z.array(z.enum(["Energy", "Oxygen", "Water", "Food", "Exposure"])),
  log: z.array(z.string().max(300)).max(8),
});
export function loadSession(): {
  mission: Mission;
  plan: Plan;
  guide: GuideState;
  message: string;
} {
  const base = loadMission();
  const guide = initialGuide();
  if (base.mission.turn > 1) {
    guide.node = nextTurnNode(base.mission);
    guide.learned = ["Energy", "Oxygen", "Water", "Food", "Exposure"];
  }
  const fallback = { ...base, plan: defaultPlan(), guide };
  try {
    const raw = localStorage.getItem(SAVE_KEY);
    if (!raw) return fallback;
    const parsed = JSON.parse(raw);
    const mission = decodeSave(raw);
    if (parsed.exploration?.guide)
      return {
        ...base,
        mission,
        plan: planSchema.parse(parsed.exploration.plan),
        guide: guideSchema.parse(parsed.exploration.guide),
      };
    // Legacy progress keeps its canonical mission and pending settings.
    return {
      ...fallback,
      plan: parsed.exploration?.plan
        ? planSchema.parse(parsed.exploration.plan)
        : defaultPlan(),
    };
  } catch {
    return fallback;
  }
}
export function saveSession(
  mission: Mission,
  plan: Plan,
  guide: GuideState,
): string {
  try {
    localStorage.setItem(
      SAVE_KEY,
      JSON.stringify({ ...mission, exploration: { plan, guide } }),
    );
    return "";
  } catch {
    return "Saving is unavailable. Keep playing; progress may not survive a refresh.";
  }
}
