import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import {
  commitTurn,
  initialMission,
  type Task,
} from "../../src/domain/mission";
const guide = (page: Page) =>
  page.getByRole("region", { name: "Mission guide", exact: true });
async function objective(page: Page) {
  await guide(page).locator("button.primary").click();
}
async function keep(page: Page) {
  await page
    .getByRole("button", { name: "Keep this plan", exact: true })
    .click();
}
async function onboard(page: Page) {
  await page.goto("/?view=map");
  await objective(page);
  await objective(page);
  await page.getByRole("button", { name: "Continue", exact: true }).click();
  await objective(page);
  await page.getByRole("button", { name: "Continue", exact: true }).click();
  await objective(page);
  await keep(page);
  await objective(page);
  await page.getByRole("button", { name: "Water tank checked" }).click();
  await objective(page);
  await keep(page);
  await objective(page);
  await keep(page);
  await expect(guide(page)).toContainText("Check before we act");
}
async function turn(
  page: Page,
  n: number,
  oxygen: boolean,
  green: boolean,
  task: string,
) {
  await page.getByRole("button", { name: "Plan", exact: true }).click();
  const d = page.getByRole("dialog");
  await d
    .getByRole("button", {
      name: oxygen ? "Produce oxygen" : "Use stored oxygen",
      exact: false,
    })
    .click();
  await d
    .getByRole("button", {
      name: green ? "Power growing lights" : "Pause growing",
      exact: false,
    })
    .click();
  await d.getByRole("button", { name: new RegExp("^" + task) }).click();
  await d
    .getByRole("button", { name: `Advance turn ${n}`, exact: true })
    .click();
  await expect(d).toHaveCount(0);
  await expect(guide(page)).toContainText("Your decision changed");
}

test("guided six-turn story preserves canonical outcomes, pending choices and evidence", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await onboard(page);
  await turn(page, 1, true, true, "Lab research");
  await page.reload();
  await expect(guide(page)).toContainText("Your decision changed");
  await objective(page);
  await objective(page);
  await page.getByRole("button", { name: /^Take shelter/ }).click();
  await keep(page);
  await turn(page, 2, true, true, "Take shelter");
  await expect(guide(page)).toContainText("harvested two");
  await objective(page);
  await expect(guide(page)).toContainText("earlier plan left");
  await objective(page);
  await keep(page);
  await objective(page);
  await page.getByRole("button", { name: "Mark geology route" }).click();
  await expect(guide(page)).toContainText("Follow the marked route");
  await page.reload();
  await expect(guide(page)).toContainText("Follow the marked route");
  await objective(page);
  await page.getByRole("button", { name: "Plan sample collection" }).click();
  expect(
    await page.evaluate(
      () => JSON.parse(localStorage.getItem("marsastro.save.v1")!).samples,
    ),
  ).toBe(0);
  await turn(page, 3, false, false, "Rover expedition");
  await objective(page);
  await objective(page);
  await page.getByRole("button", { name: /^Ask Earth/ }).click();
  await keep(page);
  await turn(page, 4, true, false, "Ask Earth");
  await expect(
    page.getByRole("button", { name: "Earth reply received" }),
  ).toBeVisible();
  await objective(page);
  await objective(page);
  await page.getByRole("button", { name: /^Take shelter/ }).click();
  await keep(page);
  await turn(page, 5, false, false, "Take shelter");
  await objective(page);
  await objective(page);
  await page.getByRole("button", { name: /^Lab research/ }).click();
  await keep(page);
  await turn(page, 6, false, false, "Lab research");
  await objective(page);
  await objective(page);
  await expect(
    page.getByRole("heading", { name: "Mission accomplished, Commander." }),
  ).toBeVisible();
  let expected = initialMission();
  const tasks: Task[] = [
    "research",
    "shelter",
    "fieldSample",
    "askEarth",
    "shelter",
    "research",
  ];
  for (let i = 0; i < 6; i++)
    expected = commitTurn(
      expected,
      {
        oxygenOn: [true, true, false, true, false, false][i],
        greenhouseOn: i < 2,
        task: tasks[i],
      },
      i + 1,
    );
  const saved = await page.evaluate(() =>
    JSON.parse(localStorage.getItem("marsastro.save.v1")!),
  );
  expect({ ...saved, exploration: undefined }).toEqual({
    ...expected,
    exploration: undefined,
  });
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.getByRole("button", { name: "Science library" }).click();
  await expect(
    page.getByText("NASA records solar flares.", { exact: false }),
  ).toBeVisible();
  await page
    .locator(".evidence-card")
    .filter({ hasText: "NASA records solar flares." })
    .getByText("Explore the evidence & original source")
    .click();
  await expect(page.getByText("2024-05-10T06:27:00-FLR-001")).toBeVisible();
  expect(errors).toEqual([]);
});

test("wrong destinations do not advance, pending allocations survive, and hints never decide", async ({
  page,
}) => {
  await page.clock.install();
  await page.goto("/?view=map");
  await objective(page);
  await expect(page.locator(".resource-hud>div")).toHaveCount(0);
  await page.getByRole("button", { name: "Plan", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Advance turn 1", exact: true }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page
    .locator(".flat-map")
    .getByRole("button", { name: /Storage center/ })
    .click();
  await page.getByRole("button", { name: "Close facility" }).click();
  await expect(guide(page)).toContainText("Meet your science lead");
  await objective(page);
  await page.getByRole("button", { name: "Continue", exact: true }).click();
  await objective(page);
  await page.getByRole("button", { name: "Continue", exact: true }).click();
  await objective(page);
  await expect(page.locator(".resource-hud>div")).toHaveCount(2);
  await page.getByRole("button", { name: /^Use stored oxygen/ }).click();
  await page.reload();
  await expect(guide(page)).toContainText("Choose where power goes");
  await objective(page);
  await expect(
    page.getByRole("button", { name: /^Use stored oxygen/ }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Close facility" }).click();
  await page.clock.fastForward(26000);
  await expect(guide(page).locator(".inactivity-hint")).toBeVisible();
  await expect(guide(page)).toContainText("Choose where power goes");
});

test("accessible controls support independent strategies and unsafe consequences", async ({
  page,
}) => {
  await onboard(page);
  await page.getByRole("button", { name: "Plan", exact: true }).click();
  const report = await new AxeBuilder({ page }).analyze();
  expect(report.violations).toEqual([]);
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.getByRole("button", { name: "Settings", exact: true }).click();
  await page.getByLabel("Guided objectives").uncheck();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await turn(page, 1, false, false, "Conserve power");
  await objective(page);
  await turn(page, 2, false, false, "Lab research");
  await objective(page);
  await turn(page, 3, false, false, "Rover expedition");
  await objective(page);
  await turn(page, 4, false, false, "Conserve power");
  await objective(page);
  await objective(page);
  await expect(
    page.getByRole("heading", { name: "The crew needed a rescue." }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});

test("corrupt saves recover and storage denial remains playable", async ({
  page,
}) => {
  await page.goto("/?view=map");
  await page.evaluate(() =>
    localStorage.setItem("marsastro.save.v1", "broken"),
  );
  await page.reload();
  await expect(guide(page)).toContainText("Earth → Mars");
  await objective(page);
  await expect(guide(page)).toContainText("Meet your science lead");
  await page.addInitScript(() => {
    Storage.prototype.setItem = () => {
      throw new DOMException("Quota", "QuotaExceededError");
    };
  });
  await page.reload();
  await expect(page.getByRole("status")).toContainText("Saving is unavailable");
  await objective(page);
  await expect(
    page.getByRole("region", { name: "Dr. Maya controls" }),
  ).toContainText("Welcome, Commander!");
});
