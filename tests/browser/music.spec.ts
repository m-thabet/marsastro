import { test, expect } from "@playwright/test";

test("real soundtrack starts on interaction, loops, and retains audio preferences", async ({
  page,
}) => {
  await page.goto("/?view=map");
  const audio = page.locator("#background-music");
  await expect
    .poll(() => audio.evaluate((a: HTMLAudioElement) => a.paused))
    .toBe(true);
  await page
    .getByRole("button", { name: "Play background music", exact: true })
    .click();
  await page.getByRole("button", { name: "Settings", exact: true }).click();
  await expect
    .poll(() => audio.evaluate((a: HTMLAudioElement) => a.currentTime), {
      timeout: 20000,
    })
    .toBeGreaterThan(0.1);
  expect(await audio.evaluate((a: HTMLAudioElement) => a.volume)).toBeCloseTo(
    0.24,
  );
  expect(await audio.evaluate((a: HTMLAudioElement) => a.loop)).toBe(true);
  await expect(
    page.getByRole("link", {
      name: "Adrift Among Infinite Stars",
      exact: true,
    }),
  ).toHaveAttribute("href", /scottbuckley/);
  const volume = page.getByRole("slider", { name: "Music volume" });
  await volume.press("Home");
  for (let i = 0; i < 37; i++) await volume.press("ArrowRight");
  await expect
    .poll(() => audio.evaluate((a: HTMLAudioElement) => a.volume))
    .toBeCloseTo(0.37);
  await page.getByRole("checkbox", { name: "Music enabled" }).uncheck();
  await expect
    .poll(() => audio.evaluate((a: HTMLAudioElement) => a.paused))
    .toBe(true);
  await page.reload();
  await page.getByRole("button", { name: "Settings", exact: true }).click();
  await expect(
    page.getByRole("checkbox", { name: "Music enabled" }),
  ).not.toBeChecked();
  await expect(page.getByRole("slider", { name: "Music volume" })).toHaveValue(
    "37",
  );
  expect(await audio.evaluate((a: HTMLAudioElement) => a.paused)).toBe(true);
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page
    .getByRole("button", { name: "Play background music", exact: true })
    .click();
  await expect
    .poll(() => audio.evaluate((a: HTMLAudioElement) => a.currentTime), {
      timeout: 20000,
    })
    .toBeGreaterThan(0.1);
  // Exercise the browser's real MP3 duration, range loading and loop boundary.
  await audio.evaluate((a: HTMLAudioElement) => {
    a.currentTime = a.duration - 0.25;
  });
  await expect
    .poll(() => audio.evaluate((a: HTMLAudioElement) => a.currentTime), {
      timeout: 15000,
    })
    .toBeLessThan(3);
  await page
    .getByRole("button", { name: "Mute background music", exact: true })
    .click();
  await expect
    .poll(() => audio.evaluate((a: HTMLAudioElement) => a.paused))
    .toBe(true);
});

test("hidden tabs pause music and missing audio cannot block the mission", async ({
  page,
}) => {
  await page.goto("/?view=map");
  await page.getByRole("button", { name: /Skip arrival/ }).click();
  const audio = page.locator("#background-music");
  await expect
    .poll(() => audio.evaluate((a: HTMLAudioElement) => a.currentTime), {
      timeout: 20000,
    })
    .toBeGreaterThan(0.1);
  await page.evaluate(() => {
    Object.defineProperty(document, "hidden", {
      configurable: true,
      value: true,
    });
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await expect
    .poll(() => audio.evaluate((a: HTMLAudioElement) => a.paused))
    .toBe(true);
  await page.evaluate(() => {
    Object.defineProperty(document, "hidden", {
      configurable: true,
      value: false,
    });
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await expect
    .poll(() => audio.evaluate((a: HTMLAudioElement) => a.paused))
    .toBe(false);
  await page.route("**/assets/audio/*.mp3", (route) => route.abort());
  await page.reload();
  await page.getByRole("button", { name: "Settings", exact: true }).click();
  await expect(
    page.getByText("Music could not load.", { exact: false }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page
    .getByRole("button", { name: "Find Dr. Maya", exact: false })
    .click();
  await expect(
    page.getByRole("region", { name: "Dr. Maya controls" }),
  ).toBeVisible();
});
