import {test,expect} from "@playwright/test";
test("landing and auth pages render", async({page})=>{
  await page.goto("/"); await expect(page.getByText("LoveLink").first()).toBeVisible();
  await page.goto("/auth/login"); await expect(page.getByRole("heading",{name:/đăng nhập/i})).toBeVisible();
  await page.goto("/auth/register"); await expect(page.getByRole("heading",{name:/đăng ký/i})).toBeVisible();
});
