import { describe, it, expect } from "vitest";
import {
  advanceGuide,
  initialGuide,
  canCommitGuide,
  nextTurnNode,
  outcomeLines,
} from "../src/domain/guidance";
import { initialMission, defaultPlan, commitTurn } from "../src/domain/mission";
describe("persistent world guidance", () => {
  it("requires the correct crew and facility actions before commitment", () => {
    let g = initialGuide();
    const m = initialMission(),
      p = defaultPlan();
    expect(canCommitGuide(g, m)).toBe(false);
    g = advanceGuide(g, { type: "arrive" }, m, p);
    expect(advanceGuide(g, { type: "talk", person: "alex" }, m, p)).toBe(g);
    g = advanceGuide(g, { type: "talk", person: "maya" }, m, p);
    g = advanceGuide(g, { type: "talk", person: "alex" }, m, p);
    g = advanceGuide(g, { type: "ready" }, m, p);
    expect(
      advanceGuide(g, { type: "select", target: "Storage center" }, m, p),
    ).toBe(g);
    g = advanceGuide(g, { type: "select", target: "Power station" }, m, p);
    expect(g.learned).toEqual(["Energy", "Oxygen"]);
    g = advanceGuide(g, { type: "choose", at: "Power station" }, m, p);
    g = advanceGuide(g, { type: "select", target: "Life support" }, m, p);
    g = advanceGuide(g, { type: "water" }, m, p);
    g = advanceGuide(g, { type: "choose", at: "Greenhouse" }, m, p);
    g = advanceGuide(g, { type: "choose", at: "Science lab" }, m, p);
    expect(canCommitGuide(g, m)).toBe(true);
    expect(m).toEqual(initialMission());
    expect(g.log).toHaveLength(8);
  });
  it("routes every canonical turn and never awards a sample for marking", () => {
    const m = { ...initialMission(), turn: 3 };
    const p = { ...defaultPlan(), task: "fieldSample" as const };
    const g = { ...initialGuide(), node: "rover" as const };
    let next = advanceGuide(g, { type: "select", target: "rover" }, m, p);
    next = advanceGuide(next, { type: "markRoute" }, m, p);
    expect(m.samples).toBe(0);
    expect(canCommitGuide(next, m)).toBe(false);
    next = advanceGuide(next, { type: "collect" }, m, p);
    expect(next.node).toBe("expedition");
    expect(canCommitGuide(next, m)).toBe(true);
    expect(m.samples).toBe(0);
    expect(nextTurnNode({ ...m, turn: 2 })).toBe("shelter");
    expect(nextTurnNode({ ...m, turn: 4 })).toBe("rover");
    expect(nextTurnNode({ ...m, turn: 4, samples: 1 })).toBe("advice");
    expect(nextTurnNode({ ...m, turn: 5 })).toBe("storm");
    expect(nextTurnNode({ ...m, turn: 6 })).toBe("finalResearch");
    expect(nextTurnNode({ ...m, status: "rescue" })).toBe("debrief");
  });
  it("describes actual harvests and leaves alternate strategies available", () => {
    let m = commitTurn(initialMission(), defaultPlan(), 1);
    expect(outcomeLines(m).join(" ")).not.toContain("harvested");
    m = commitTurn(m, { ...defaultPlan(), task: "shelter" }, 2);
    expect(outcomeLines(m).join(" ")).toContain("harvested two");
    const g = { ...initialGuide(), node: "protection" as const };
    expect(advanceGuide(g, { type: "decline" }, m, defaultPlan()).node).toBe(
      "review",
    );
    expect(canCommitGuide(initialGuide(false), m)).toBe(true);
  });
});
