import { expect, Page, test } from "@playwright/test";

const enabled = process.env.FULLSTACK_E2E === "1";
test.skip(!enabled, "Runs only against the Docker Compose full stack.");

async function login(page: Page, email: string, password: string) {
  await page.goto("/auth/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Mật khẩu").fill(password);
  await page.getByRole("button", { name: "Đăng nhập" }).click();
  await expect(page).toHaveURL(/\/discover/);
}

test("real backend supports realtime chat and incoming-call recovery", async ({ browser }) => {
  const firstContext = await browser.newContext();
  const secondContext = await browser.newContext();
  const first = await firstContext.newPage();
  const second = await secondContext.newPage();

  await login(first, "e2e.a@lovelink.local", "E2EPassword123!");
  await login(second, "e2e.b@lovelink.local", "E2EPassword123!");

  await first.goto("/messages");
  await first.getByRole("link", { name: /Bình/ }).click();
  await second.goto("/messages");
  await second.getByRole("link", { name: /An/ }).click();

  const text = `Tin nhắn realtime ${Date.now()}`;
  await first.getByPlaceholder("Nhập tin nhắn…").fill(text);
  await first.locator(".composer button").click();
  await expect(second.getByText(text)).toBeVisible({ timeout: 15_000 });

  await first.getByTitle("Gọi video").click();
  await expect(first).toHaveURL(/\/calls\//);

  await second.reload();
  await expect(second.getByText("đang gọi video cho bạn")).toBeVisible({ timeout: 15_000 });
  await second.getByRole("button", { name: /Từ chối/ }).click();
  await expect(first).toHaveURL(/\/messages/, { timeout: 15_000 });

  await firstContext.close();
  await secondContext.close();
});

test("reviewer and moderator workflows are usable in Django admin", async ({ page }) => {
  await page.goto("http://localhost:8000/admin/login/?next=/admin/");
  await page.locator('input[name="username"]').fill("e2e.admin@lovelink.local");
  await page.locator('input[name="password"]').fill("E2EAdminPassword123!");
  await page.locator('input[type="submit"]').click();

  await page.goto("http://localhost:8000/admin/verification/verificationrequest/");
  await page.getByRole("link", { name: /e2e\.b@lovelink\.local/ }).first().click();
  await expect(page.getByText("Thao tác xét duyệt")).toBeVisible();
  await expect(page.getByText("Bằng chứng riêng tư")).toBeVisible();

  await page.goto("http://localhost:8000/admin/moderation/report/");
  await page.getByRole("link", { name: /e2e\.b@lovelink\.local/ }).first().click();
  await expect(page.getByText("Xử lý báo cáo")).toBeVisible();
  await expect(page.getByText("Nội dung liên quan")).toBeVisible();
});
