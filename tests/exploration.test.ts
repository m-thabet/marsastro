import { describe, it, expect } from "vitest";
import {
  advanceStory,
  moveWithSlide,
  canOccupy,
  type StoryStage,
} from "../src/domain/exploration";
import { BUILDINGS } from "../src/content/buildings";
import { initialMission, defaultPlan, commitTurn } from "../src/domain/mission";
import { decodeSave } from "../src/infrastructure/storage";
describe("exploration contracts", () => {
  it("unrelated actions cannot skip teaching gates", () => {
    expect(
      advanceStory("power", { type: "select", building: "Storage center" }),
    ).toBe("power");
    expect(advanceStory("oxygen", { type: "configure", system: "food" })).toBe(
      "oxygen",
    );
    expect(advanceStory("research", { type: "commit" })).toBe("research");
  });
  it("accepts both informed power choices and a conserving task", () => {
    let stage: StoryStage = "landing";
    stage = advanceStory(stage, { type: "land" });
    stage = advanceStory(stage, { type: "descend" });
    stage = advanceStory(stage, { type: "select", building: "Power station" });
    stage = advanceStory(stage, { type: "configure", system: "oxygen" });
    stage = advanceStory(stage, { type: "configure", system: "food" });
    stage = advanceStory(stage, { type: "configure", system: "research" });
    expect(stage).toBe("review");
    expect(advanceStory(stage, { type: "commit" })).toBe("independent");
  });
  it("blocks walls and large frame tunnelling while allowing sliding", () => {
    const obstacles = [{ x: 0, z: 0, halfX: 2, halfZ: 2 }];
    const result = moveWithSlide([-5, 0], [10, 0], obstacles);
    expect(result[0]).toBeLessThan(-2.4);
    expect(canOccupy(...result, obstacles)).toBe(true);
    const slide = moveWithSlide([-3, 0], [2, 3], obstacles);
    expect(slide[1]).toBeCloseTo(3);
    expect(canOccupy(...slide, obstacles)).toBe(true);
  });
  it("keeps spawn and exploration bounds safe", () => {
    expect(canOccupy(0, 3, BUILDINGS)).toBe(true);
    expect(canOccupy(56, 0, BUILDINGS)).toBe(false);
    expect(canOccupy(-15, 5, BUILDINGS)).toBe(false);
  });
  it("exploration envelope keeps replay validation authoritative", () => {
    const mission = commitTurn(initialMission(), defaultPlan(), 1);
    const save = JSON.stringify({
      ...mission,
      energy: 99999,
      exploration: { stage: "independent", plan: defaultPlan() },
    });
    expect(decodeSave(save)).toEqual(mission);
  });
});
