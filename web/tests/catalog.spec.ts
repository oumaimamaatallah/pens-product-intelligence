import { test, expect } from "@playwright/test"

test("inspect captured quantity tiers and refine the catalog", async ({ page }) => {
  await page.goto("/")
  await expect(page.locator(".catalog-product")).toHaveCount(12)
  await page.locator(".catalog-product").filter({ hasText: "LNS" }).click()
  const sheet = page.getByRole("dialog")
  await expect(sheet.getByRole("heading", { level: 2 })).toContainText("Alpha Soft Touch")
  await expect(sheet.locator(".quote-result")).toContainText("$1.32")
  await sheet.getByRole("slider", { name: "Order quantity", exact: true }).press("End")
  await expect(sheet.locator(".quote-result")).toContainText("$0.90")
  await expect(sheet.locator(".quote-result")).toContainText("$4,500.00")
  await sheet.getByRole("button", { name: "Close", exact: true }).click()
  await page
    .getByRole("textbox", { name: "Search products", exact: true })
    .fill("thereisnosuchproduct")
  await expect(
    page.getByRole("heading", { name: "Nothing on this shelf.", exact: true }),
  ).toBeVisible()
  await page.getByRole("button", { name: "Reset catalog", exact: true }).click()
  const download = page.waitForEvent("download")
  await page.getByRole("link", { name: "Power BI report", exact: true }).click()
  expect((await download).suggestedFilename()).toBe("PensProductNotebook.zip")
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= screen.width)).toBe(true)
})
