import { test, expect } from "@playwright/test";

test("arrival, world beacons, keyboard conversation, camera and renderer recovery", async ({
  page,
}) => {
  test.setTimeout(180000);
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/?debug");
  await expect(page.locator(".world-loading")).toHaveCount(0, {
    timeout: 60000,
  });
  await page.screenshot({
    path: `docs/review/${test.info().project.name}-arrival.png`,
  });
  await page
    .getByRole("button", { name: "Skip arrival", exact: false })
    .click();
  await expect(page.locator(".world-loading")).toHaveCount(0, {
    timeout: 60000,
  });
  await expect
    .poll(() => page.locator("#render-stats").textContent(), { timeout: 60000 })
    .toMatch(/draws/);
  await page.screenshot({
    path: `docs/review/${test.info().project.name}-guided-base.png`,
  });
  // Walk towards Maya; keyboard E and touch share the same proximity target.
  await page.keyboard.down("w");
  try {
    await expect(page.locator(".near-prompt")).toContainText("Dr. Maya", {
      timeout: 30000,
    });
  } finally {
    await page.keyboard.up("w");
  }
  await page.keyboard.press("e");
  await expect(
    page.getByRole("region", { name: "Dr. Maya controls" }),
  ).toContainText("Welcome, Commander!");
  await page.screenshot({
    path: `docs/review/${test.info().project.name}-crew.png`,
  });
  await page.getByRole("button", { name: "Continue", exact: true }).click();
  await page.getByRole("button", { name: "Find Alex", exact: false }).click();
  await page.getByRole("button", { name: "Talk to Alex", exact: true }).click();
  await page.getByRole("button", { name: "Continue", exact: true }).click();
  await page
    .getByRole("button", { name: "Find power station", exact: false })
    .click();
  await page.waitForTimeout(1600);
  await page.screenshot({
    path: `docs/review/${test.info().project.name}-objective.png`,
  });
  await page
    .getByRole("button", { name: "GO: Power station", exact: false })
    .click();
  await expect(
    page.getByRole("region", { name: "Power station controls" }),
  ).toBeVisible();
  await page.getByRole("button", { name: /^Use stored oxygen/ }).click();
  await page.screenshot({
    path: `docs/review/${test.info().project.name}-allocation.png`,
  });
  await page.getByRole("button", { name: "Close facility" }).click();
  await page.getByRole("button", { name: "Settings", exact: true }).click();
  await page.getByRole("button", { name: "Low · lighter rendering" }).click();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.getByRole("button", { name: "Overview", exact: true }).click();
  await page.waitForTimeout(800);
  await page.screenshot({
    path: `docs/review/${test.info().project.name}-guided-low.png`,
  });
  console.log(
    "render counters",
    test.info().project.name,
    await page.locator("#render-stats").textContent(),
  );
  await page
    .locator("canvas")
    .evaluate((c) =>
      c.dispatchEvent(new Event("webglcontextlost", { cancelable: true })),
    );
  await expect(page.getByLabel("Lightweight mission map")).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Mission guide", exact: true }),
  ).toContainText("Choose where power goes");
  expect(errors).toEqual([]);
});

test("reduced motion bypasses cinematic without spending resources", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(
    page.getByRole("region", { name: "Mission guide", exact: true }),
  ).toContainText("Meet your science lead", { timeout: 60000 });
  const saved = await page.evaluate(() =>
    JSON.parse(localStorage.getItem("marsastro.save.v1")!),
  );
  expect(saved.history).toEqual([]);
  expect(saved.turn).toBe(1);
  expect(saved.energy).toBe(12);
});

test("arrival completes naturally and leaves the first decision unspent", async ({
  page,
}) => {
  test.setTimeout(120000);
  await page.goto("/");
  await expect(page.locator(".world-loading")).toHaveCount(0, {
    timeout: 60000,
  });
  await expect(
    page.getByRole("region", { name: "Mission guide", exact: true }),
  ).toContainText("Meet your science lead", { timeout: 90000 });
  const saved = await page.evaluate(() =>
    JSON.parse(localStorage.getItem("marsastro.save.v1")!),
  );
  expect(saved.history).toHaveLength(0);
  expect(saved.energy).toBe(12);
  expect(saved.oxygen).toBe(48);
  await expect(
    page.getByRole("button", { name: "Walk", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
});

test("missing model offers an explicit playable map fallback", async ({
  page,
}) => {
  test.setTimeout(90000);
  await page.route("**/assets/models/lander.glb", (route) => route.abort());
  await page.goto("/");
  const fallback = page.getByRole("button", {
    name: "Open mission map",
    exact: true,
  });
  await expect(
    fallback.or(page.getByLabel("Lightweight mission map")),
  ).toBeVisible({ timeout: 60000 });
  let acknowledged = false;
  if (await fallback.isVisible()) {
    try {
      await fallback.click({ timeout: 1500 });
      acknowledged = true;
    } catch {
      /* Context disposal can replace the panel with the map first. */
    }
  }
  await expect(page.getByLabel("Lightweight mission map")).toBeVisible();
  if (!acknowledged)
    await expect(page.getByRole("status")).toContainText("3D view stopped");
  await expect(page.getByLabel("Lightweight mission map")).toBeVisible();
  await page
    .getByRole("button", { name: "Skip arrival", exact: false })
    .click();
  await expect(
    page.getByRole("region", { name: "Mission guide", exact: true }),
  ).toContainText("Meet your science lead");
});
