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

test("real backend supports realtime chat, receipts and a LiveKit call", async ({ browser }) => {
  const firstContext = await browser.newContext({
    permissions: ["camera", "microphone"],
  });
  const secondContext = await browser.newContext({
    permissions: ["camera", "microphone"],
  });
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
  await expect(first.getByText("Đã xem").last()).toBeVisible({ timeout: 15_000 });

  await first.getByTitle("Gọi video").click();
  await expect(first).toHaveURL(/\/calls\//);

  // Reloading the callee proves the pending call is recovered through REST.
  await second.reload();
  await expect(second.getByText("đang gọi video cho bạn")).toBeVisible({
    timeout: 15_000,
  });
  await second.getByRole("button", { name: /Trả lời/ }).click();
  await expect(second).toHaveURL(/\/calls\//);
  await expect(first.locator(".video-stage")).toBeVisible({ timeout: 20_000 });
  await expect(second.locator(".video-stage")).toBeVisible({ timeout: 20_000 });
  await expect(first.getByText(/Kết nối|Đang đo chất lượng/)).toBeVisible();

  await first.getByRole("button", { name: /Kết thúc/ }).click();
  await expect(first).toHaveURL(/\/messages/);
  await expect(second).toHaveURL(/\/messages/, { timeout: 15_000 });

  await firstContext.close();
  await secondContext.close();
});

test("member can verify a private phone number through OTP", async ({ page }) => {
  await login(page, "e2e.a@lovelink.local", "E2EPassword123!");
  await page.goto("/settings/security");
  await page.getByLabel("Số điện thoại").fill("0901234567");
  await page.getByRole("button", { name: /Gửi mã OTP/ }).click();
  await expect(page.getByText(/Mã OTP đã được gửi/)).toBeVisible();
  await page.getByLabel("Mã OTP 6 chữ số").fill("123456");
  await page.getByRole("button", { name: "Xác minh", exact: true }).click();
  await expect(page.getByText("Xác minh số điện thoại thành công.")).toBeVisible();
  await expect(page.getByText("Đã xác minh", { exact: true })).toBeVisible();
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
