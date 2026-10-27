import { test, expect } from "@playwright/test"
import AxeBuilder from "@axe-core/playwright"
test("the first view has no WCAG A or AA violations", async ({ page }) => {
  await page.goto("/")
  await page.waitForLoadState("networkidle")
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze()
  expect(
    results.violations.map((item) => ({
      id: item.id,
      description: item.description,
      nodes: item.nodes.map((node) => ({ target: node.target, summary: node.failureSummary })),
    })),
  ).toEqual([])
})
