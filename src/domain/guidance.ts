import type { BuildingName } from "../content/buildings";
import { EVENTS, TASKS, type Mission, type Plan, type Task } from "./mission";
export type TargetId = BuildingName | "maya" | "alex" | "rover" | "sample";
export const TARGETS: Record<
  TargetId,
  { name: string; position: [number, number, number] }
> = {
  maya: { name: "Dr. Maya", position: [6, 0, 6] },
  alex: { name: "Alex", position: [-7, 0, 8] },
  rover: { name: "Rover", position: [29, 0, 26] },
  sample: { name: "Geology stop", position: [43, 0, -5] },
  "Living habitat": { name: "Living habitat", position: [-15, 0, 5] },
  "Life support": { name: "Life support", position: [-17, 0, -13] },
  Greenhouse: { name: "Greenhouse", position: [1, 0, -23] },
  "Science lab": { name: "Science lab", position: [18, 0, -12] },
  "Radiation shelter": { name: "Radiation shelter", position: [20, 0, 10] },
  "Communication center": {
    name: "Communication center",
    position: [-23, 0, -28],
  },
  "Power station": { name: "Power station", position: [18, 0, -30] },
  "Storage center": { name: "Storage center", position: [-17, 0, 24] },
};
export const NODES = [
  "cinematic",
  "maya",
  "alex",
  "nova",
  "power",
  "allocation",
  "oxygen",
  "water",
  "food",
  "research",
  "review",
  "outcome",
  "shelter",
  "protection",
  "dust",
  "rebalance",
  "rover",
  "route",
  "sample",
  "expedition",
  "advice",
  "contact",
  "storm",
  "finalResearch",
  "finalReview",
  "debrief",
  "free",
] as const;
export type NodeId = (typeof NODES)[number];
export type ResourceId = "Energy" | "Oxygen" | "Water" | "Food" | "Exposure";
export type GuideState = {
  version: 2;
  node: NodeId;
  enabled: boolean;
  learned: ResourceId[];
  log: string[];
};
export type GuideAction =
  | {
      type:
        | "arrive"
        | "ready"
        | "water"
        | "markRoute"
        | "collect"
        | "decline"
        | "continue"
        | "commit";
    }
  | { type: "talk"; person: "maya" | "alex" }
  | { type: "select"; target: TargetId }
  | { type: "choose"; at: TargetId };
export const initialGuide = (enabled = true): GuideState => ({
  version: 2,
  node: enabled ? "cinematic" : "free",
  enabled,
  learned: enabled ? [] : ["Energy", "Oxygen", "Water", "Food", "Exposure"],
  log: [],
});
export function nextTurnNode(m: Mission): NodeId {
  if (m.status !== "playing") return "debrief";
  if (m.turn === 2) return "shelter";
  if (m.turn === 3) return "dust";
  if (m.turn === 4) return m.samples === 0 ? "rover" : "advice";
  if (m.turn === 5) return "storm";
  return "finalResearch";
}
export function canCommitGuide(g: GuideState, m: Mission) {
  return (
    m.status === "playing" &&
    (!g.enabled || ["review", "expedition", "finalReview"].includes(g.node))
  );
}
export function advanceGuide(
  g: GuideState,
  a: GuideAction,
  m: Mission,
  p: Plan,
): GuideState {
  const old = g.node;
  let node = old;
  const learned = new Set(g.learned);
  if (a.type === "commit")
    return {
      ...g,
      node: "outcome",
      learned: [
        ...new Set<ResourceId>([
          ...g.learned,
          "Energy",
          "Oxygen",
          "Water",
          "Food",
          "Exposure",
        ]),
      ],
    };
  if (a.type === "continue" && old === "outcome")
    node = g.enabled
      ? nextTurnNode(m)
      : m.status === "playing"
        ? "free"
        : "debrief";
  if (old === "cinematic" && a.type === "arrive") node = "maya";
  if (old === "maya" && a.type === "talk" && a.person === "maya") node = "alex";
  if (old === "alex" && a.type === "talk" && a.person === "alex") node = "nova";
  if (old === "nova" && a.type === "ready") node = "power";
  if (a.type === "select") {
    if (old === "power" && a.target === "Power station") {
      node = "allocation";
      learned.add("Energy");
      learned.add("Oxygen");
    }
    if (old === "oxygen" && a.target === "Life support") node = "water";
    if (
      (old === "shelter" || old === "storm") &&
      a.target === "Radiation shelter"
    ) {
      node = "protection";
      learned.add("Exposure");
    }
    if (old === "dust" && a.target === "Power station") node = "rebalance";
    if (old === "rover" && a.target === "rover") node = "route";
    if (old === "advice" && a.target === "Communication center")
      node = "contact";
  }
  if (a.type === "choose") {
    if (old === "allocation" && a.at === "Power station") node = "oxygen";
    if (old === "rebalance" && a.at === "Power station") node = "rover";
    if (old === "food" && a.at === "Greenhouse") {
      node = "research";
      learned.add("Food");
    }
    if (
      old === "research" &&
      a.at === "Science lab" &&
      (p.task === "research" || p.task === "rest")
    ) {
      node = "review";
      learned.add("Exposure");
    }
    if (old === "finalResearch" && a.at === "Science lab") node = "finalReview";
    if (old === "protection" && a.at === "Radiation shelter") node = "review";
    if (old === "contact" && a.at === "Communication center") node = "review";
  }
  if (old === "water" && a.type === "water") {
    node = "food";
    learned.add("Water");
    learned.add("Food");
  }
  if (old === "route" && a.type === "markRoute") node = "sample";
  if (old === "sample" && a.type === "collect") node = "expedition";
  if (
    a.type === "decline" &&
    ["rover", "route", "sample", "contact", "advice", "protection"].includes(
      old,
    )
  )
    node = "review";
  if (node === old) return g;
  const previous = guidance(g, m);
  return {
    ...g,
    node,
    learned: [...learned],
    log: [...g.log, `${previous.speaker}: ${previous.line}`].slice(-8),
  };
}
export type Guidance = {
  speaker: string;
  title: string;
  line: string;
  target?: TargetId;
  action: string;
  fact?: string;
};
export function guidance(g: GuideState, m: Mission): Guidance {
  const base: Record<NodeId, Guidance> = {
    cinematic: {
      speaker: "NOVA",
      title: "Earth → Mars",
      line: "Our crew needs you. Every decision shapes this mission.",
      action: "Skip arrival",
    },
    maya: {
      speaker: "NOVA",
      title: "Meet your science lead",
      line: "Follow the marker to Dr. Maya. Press E to talk.",
      target: "maya",
      action: "Find Dr. Maya",
    },
    alex: {
      speaker: "Dr. Maya",
      title: "Welcome, Commander!",
      line: "I'm Dr. Maya. I'll help you explore Mars! Meet Alex next.",
      target: "alex",
      action: "Find Alex",
    },
    nova: {
      speaker: "Alex",
      title: "You have a crew",
      line: "I'm Alex. I keep our base running!",
      action: "Meet NOVA",
    },
    power: {
      speaker: "NOVA",
      title: "Bring the base to life",
      line: "I'm NOVA, your guide. Let's inspect our solar panels.",
      target: "Power station",
      action: "Find power station",
      fact: "moxie",
    },
    allocation: {
      speaker: "Alex",
      title: "Choose where power goes",
      line: "Oxygen needs electricity. Try both settings and watch the preview.",
      target: "Power station",
      action: "Open power controls",
      fact: "moxie",
    },
    oxygen: {
      speaker: "Alex",
      title: "Follow the oxygen connection",
      line: "Your allocation is planned. Visit life support to inspect the tanks.",
      target: "Life support",
      action: "Find life support",
      fact: "moxie",
    },
    water: {
      speaker: "Alex",
      title: "Check our water reserve",
      line: "The crew drinks one water unit each turn. Check the tank.",
      target: "Life support",
      action: "Check water tank",
    },
    food: {
      speaker: "Dr. Maya",
      title: "Grow tomorrow's meals",
      line: "Two powered turns grow food. Lights also use energy and water.",
      target: "Greenhouse",
      action: "Find greenhouse",
      fact: "osdr-plants",
    },
    research: {
      speaker: "Dr. Maya",
      title: "Choose the crew's first job",
      line: "Research uses four energy. Conserving power leaves more for later.",
      target: "Science lab",
      action: "Find science lab",
    },
    review: {
      speaker: "NOVA",
      title: "Check before we act",
      line: "Compare your reserves. Only advancing the mission spends resources.",
      action: "Review mission plan",
    },
    outcome: {
      speaker: "NOVA",
      title: "Your decision changed the mission",
      line: outcomeLines(m)[0],
      action: m.status === "playing" ? "Next objective" : "See mission results",
    },
    shelter: {
      speaker: "NOVA",
      title: "Solar radiation warning",
      line: "Find the shelter. Compare protection with using your crew elsewhere.",
      target: "Radiation shelter",
      action: "Find radiation shelter",
      fact: "donki-flare",
    },
    protection: {
      speaker: "Alex",
      title: "Protection has a cost",
      line: "Shelter lowers exposure, but uses this turn's crew task.",
      target: "Radiation shelter",
      action: "Compare protection",
      fact: "radlab-iss",
    },
    dust: {
      speaker: "NOVA",
      title: "Dust reduces our sunlight",
      line: dustConnection(m),
      target: "Power station",
      action: "Check reduced power",
    },
    rebalance: {
      speaker: "Alex",
      title: "A tighter power budget",
      line: "Try stored oxygen or another crew task. Check every reserve.",
      target: "Power station",
      action: "Rebalance power",
    },
    rover: {
      speaker: "Dr. Maya",
      title: m.samples ? "Another discovery?" : "Our first field sample",
      line: "The rover needs energy and water. Inspect its route before choosing.",
      target: "rover",
      action: "Find rover",
      fact: "jezero-image",
    },
    route: {
      speaker: "Dr. Maya",
      title: "Mark the geology stop",
      line: "This expedition costs four energy, two extra water, and more exposure.",
      target: "rover",
      action: "Mark geology stop",
      fact: "jezero-image",
    },
    sample: {
      speaker: "NOVA",
      title: "Follow the marked route",
      line: "Inspect the sample marker. Confirm the expedition after reviewing its costs.",
      target: "sample",
      action: "Inspect sample",
      fact: "jezero-image",
    },
    expedition: {
      speaker: "Dr. Maya",
      title: "A sample worth planning for",
      line: "The sample is marked. Advance to fund collection and record research.",
      target: "sample",
      action: "Review expedition",
    },
    advice: {
      speaker: "NOVA",
      title: "A message to Earth?",
      line: "Advice arrives next turn. You may save this crew task instead.",
      target: "Communication center",
      action: "Find communications",
    },
    contact: {
      speaker: "Alex",
      title: "Advice or another task?",
      line: "Contact Earth for two energy, or keep your crew available.",
      target: "Communication center",
      action: "Choose communication plan",
    },
    storm: {
      speaker: "NOVA",
      title: "Another solar warning",
      line: m.shieldLevel
        ? "Your earlier shielding reduces exposure. Compare the shelter forecast."
        : "Remember your earlier shelter choice. Compare today's protection options.",
      target: "Radiation shelter",
      action: "Inspect shelter",
      fact: "donki-flare",
    },
    finalResearch: {
      speaker: "Dr. Maya",
      title: "Our final research opportunity",
      line:
        m.research < 3
          ? "Check the lab. We need three research objectives and one sample."
          : "Our research goal is met. Choose a safe final plan.",
      target: "Science lab",
      action: "Visit science lab",
    },
    finalReview: {
      speaker: "NOVA",
      title: "Bring the crew home safely",
      line: "Check all reserves, then advance our final mission turn.",
      action: "Review final plan",
    },
    debrief: {
      speaker: "NOVA",
      title: "Every mission teaches us",
      line:
        m.status === "success"
          ? "You protected the crew and completed our science goals."
          : "Let's compare crew safety, supplies, and discoveries.",
      action: "Mission results",
    },
    free: {
      speaker: "NOVA",
      title: "You have the command",
      line:
        EVENTS[Math.min(m.turn - 1, 5)] === "storm"
          ? "Solar warning: compare shelter and shielding before committing."
          : EVENTS[Math.min(m.turn - 1, 5)] === "dust"
            ? "Dust limits solar power to six energy. Check your stored reserves."
            : "Inspect a facility, choose a crew task, and review the forecast.",
      action: "Review mission plan",
    },
  };
  return base[g.node];
}
export function outcomeLines(m: Mission): string[] {
  const h = m.history.at(-1);
  if (!h) return ["Your crew is ready."];
  const task = TASKS.find((t) => t.id === h.plan.task)!;
  const benefit =
    h.plan.task === "fieldSample"
      ? "Sample recovered: +1 research and +1 sample."
      : h.plan.task === "research"
        ? "Your lab added one research objective."
        : h.plan.task === "shelter"
          ? `Sheltering limited added exposure to ${h.after.exposure - h.before.exposure}.`
          : h.plan.task === "upgradeShield"
            ? "Your shielding now lowers exposure on future turns."
            : h.plan.task === "askEarth"
              ? "Your Earth message is sent. Advice arrives next turn."
              : "Your crew saved energy by giving up another task.";
  const oxygen = h.plan.oxygenOn
    ? `Oxygen: ${h.before.oxygen} → ${h.after.oxygen}. Production used four energy.`
    : `Using stored oxygen saved four energy; ${h.after.oxygen} oxygen remains.`;

  return [
    benefit,
    oxygen,
    `${task.title} used ${task.cost} energy. Water changed ${h.before.water} → ${h.after.water}.`,
    ...(h.after.food - h.before.food === 1
      ? ["Your greenhouse harvested two meal packs."]
      : []),
  ];
}
function dustConnection(m: Mission) {
  const last = m.history.at(-1);
  return last
    ? `Dust gives six energy. Your earlier plan left ${last.after.energy} stored.`
    : "Dust reduces solar generation from ten energy to six.";
}
export const TARGET_TASKS: Partial<Record<BuildingName, Task[]>> = {
  "Living habitat": ["rest"],
  "Science lab": ["research", "rest"],
  "Radiation shelter": ["shelter", "upgradeShield"],
  "Communication center": ["askEarth"],
  "Storage center": ["rest"],
};
