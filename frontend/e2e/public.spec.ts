import { expect, Page, test } from "@playwright/test";

const user = { id: "11111111-1111-1111-1111-111111111111", email: "member@example.com", status: "active", is_email_verified: true, is_phone_verified: false, created_at: "2026-08-04T00:00:00Z" };
const profile = { public_id: "22222222-2222-2222-2222-222222222222", display_name: "Mai", age: 27, gender: "female", current_province: { code: "01", name: "Hà Nội" }, hometown_province: { code: "36", name: "Thanh Hóa" }, height_cm: 162, occupation_category: { id: "33333333-3333-3333-3333-333333333333", name: "Công nghệ thông tin" }, occupation_text: "Software Engineer", education_level: "university", income_band: "20_30", relationship_status: "single", relationship_goal: "serious", religion: "", smoking_status: "never", drinking_status: "sometimes", children_status: "none", children_plan: "want", bio: "Mình thích đọc sách, chạy bộ và khám phá những quán cà phê yên tĩnh ở Hà Nội.", looking_for: "Một người chân thành, biết lắng nghe và nghiêm túc trong mối quan hệ.", interests: [{ id: "1", name: "Đọc sách" }, { id: "2", name: "Cà phê" }], photos: [], completion_percent: 100, verification_level: "identity_verified", verified_at: "2026-08-04T00:00:00Z", connection_status: "none" };
const referenceData = { provinces: [{ code: "01", name: "Hà Nội" }, { code: "36", name: "Thanh Hóa" }], occupations: [{ id: "33333333-3333-3333-3333-333333333333", name: "Công nghệ thông tin" }], interests: [{ id: "1", name: "Đọc sách" }, { id: "2", name: "Cà phê" }], choices: { genders: [["male", "Nam"], ["female", "Nữ"]], education: [["university", "Đại học"]], income: [["20_30", "20–30 triệu"]], goals: [["serious", "Tìm hiểu nghiêm túc"]], relationship_status: [["single", "Độc thân"]], habits: [["never", "Không"], ["sometimes", "Thỉnh thoảng"]], children: [["none", "Chưa có"]], children_plan: [["want", "Muốn có"]] } };

async function mockAuthenticatedApi(page: Page) {
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname.replace(/^\/api\/v1/, "");
    if (path === "/auth/me") return route.fulfill({ json: user });
    if (path === "/auth/csrf") return route.fulfill({ json: { csrfToken: "test" } });
    if (path === "/reference-data") return route.fulfill({ json: referenceData });
    if (path === "/discover") return route.fulfill({ json: { results: [profile], next: null } });
    if (path === `/profiles/${profile.public_id}`) return route.fulfill({ json: profile });
    if (path === "/connections/requests" && request.method() === "POST") return route.fulfill({ status: 201, json: { status: "pending" } });
    if (path === `/users/${profile.public_id}/block` && request.method() === "POST") return route.fulfill({ status: 204, body: "" });
    if (path === "/reports" && request.method() === "POST") return route.fulfill({ status: 201, json: { id: "report" } });
    if (path === "/connections/received") return route.fulfill({ json: { results: [{ id: "44444444-4444-4444-4444-444444444444", sender: profile, receiver: profile, other_user: profile, intro_message: "Chào Mai, mình cũng thích đọc sách.", status: "pending", sent_at: "2026-08-04T00:00:00Z", expires_at: "2026-08-18T00:00:00Z" }] } });
    if (path.includes("/connections/") && request.method() === "POST") return route.fulfill({ json: { status: "accepted" } });
    if (path === "/conversations") return route.fulfill({ json: { results: [{ id: "55555555-5555-5555-5555-555555555555", other_user: profile, last_message: { text: "Hẹn bạn cuối tuần nhé" }, last_message_at: "2026-08-04T00:00:00Z", unread_count: 1, created_at: "2026-08-04T00:00:00Z" }] } });
    if (path === "/verification/current") return route.fulfill({ json: null });
    if (path === "/verification/requests" && request.method() === "POST") return route.fulfill({ status: 201, json: { id: "66666666-6666-6666-6666-666666666666", status: "draft", challenge_code: "ABC123", evidence: [] } });
    return route.fulfill({ status: 404, json: { detail: `Unhandled test route: ${path}` } });
  });
}

test("landing and authentication pages render", async ({ page }) => {
  await page.route("**/api/v1/auth/me", route => route.fulfill({ status: 401, json: { detail: "Unauthenticated" } }));
  await page.goto("/");
  await expect(page.getByText("LoveLink").first()).toBeVisible();
  await page.goto("/auth/login");
  await expect(page.getByRole("heading", { name: "Chào mừng trở lại", exact: true })).toBeVisible();
  await page.goto("/auth/register");
  await expect(page.getByRole("heading", { name: "Tạo tài khoản LoveLink", exact: true })).toBeVisible();
  await page.goto("/auth/forgot-password");
  await expect(page.getByRole("heading", { name: "Quên mật khẩu", exact: true })).toBeVisible();
});

test("authenticated member can discover and inspect a verified profile", async ({ page }) => {
  await mockAuthenticatedApi(page);
  await page.goto("/discover");
  await expect(page.getByRole("heading", { name: "Tìm người phù hợp" })).toBeVisible();
  await expect(page.getByText("1 hồ sơ")).toBeVisible();
  const mobileFilter = page.locator(".mobile-filter");
  if (await mobileFilter.isVisible()) await mobileFilter.click();
  const filterScope = page.locator(".filter-panel").last();
  await expect(filterScope.getByText("Thêm tiêu chí")).toBeVisible();
  await expect(filterScope.getByText("Mục tiêu")).toBeVisible();
  await expect(filterScope.getByText("Nghề nghiệp")).toBeHidden();
  await filterScope.getByRole("button", { name: "Thêm tiêu chí" }).click();
  await expect(filterScope.getByText("Nghề nghiệp")).toBeVisible();
  if (await mobileFilter.isVisible()) await filterScope.getByRole("button", { name: "Đóng" }).click();
  await expect(page.getByText("Mai, 27")).toBeVisible();
  await expect(page.getByText("Software Engineer")).toBeVisible();
  await page.getByRole("link", { name: "Xem hồ sơ" }).click();
  await expect(page.getByRole("heading", { name: /Mai, 27/ })).toBeVisible();
  await expect(page.getByText("Danh tính đã xác minh")).toBeVisible();
  await expect(page.getByRole("button", { name: /Gửi lời làm quen/ })).toBeVisible();
});

test("dialogs trap focus, close with Escape and restore the trigger", async ({ page }) => {
  await mockAuthenticatedApi(page);
  await page.goto(`/profiles/${profile.public_id}`);

  const trigger = page.getByRole("button", { name: /Gửi lời làm quen/ });
  await trigger.focus();
  await trigger.click();

  const dialog = page.getByRole("dialog", {
    name: `Gửi lời làm quen tới ${profile.display_name}`,
  });
  await expect(dialog).toHaveAttribute("aria-modal", "true");
  await expect(page.getByLabel("Lời nhắn")).toBeFocused();
  await expect(page.locator("body")).toHaveCSS("overflow", "hidden");

  await page.keyboard.press("Shift+Tab");
  await expect(dialog.getByRole("button", { name: "Hủy" })).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(page.getByLabel("Lời nhắn")).toBeFocused();

  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(trigger).toBeFocused();
  await expect(page.locator("body")).not.toHaveCSS("overflow", "hidden");
});

test("field errors are described and feedback uses live regions", async ({ page }) => {
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({ status: 401, json: { detail: "Unauthenticated" } }),
  );
  await page.route("**/api/v1/auth/csrf", (route) =>
    route.fulfill({ json: { csrfToken: "test" } }),
  );
  await page.route("**/api/v1/auth/register", (route) =>
    route.fulfill({
      status: 400,
      json: { detail: "Dữ liệu chưa hợp lệ.", email: ["Email đã tồn tại."] },
    }),
  );
  await page.goto("/auth/register");
  const email = page.getByLabel("Email");
  await email.fill("member@example.com");
  await page.getByLabel("Ngày sinh").fill("1995-01-01");
  await page.locator('input[type="password"]').nth(0).fill("Password123!");
  await page.getByLabel("Nhập lại mật khẩu").fill("Password123!");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Tạo tài khoản" }).click();

  await expect(
    page.getByRole("alert").filter({ hasText: "Dữ liệu chưa hợp lệ." }),
  ).toBeVisible();
  const describedBy = await email.getAttribute("aria-describedby");
  expect(describedBy).toBeTruthy();
  await expect(email).toHaveAttribute("aria-invalid", "true");
  await expect(page.locator(`#${describedBy!.split(" ").at(-1)}`)).toHaveText(
    "Email đã tồn tại.",
  );
});

test("connections, messages and verification entry points are usable", async ({ page }) => {
  await mockAuthenticatedApi(page);
  await page.goto("/connections");
  await expect(page.getByRole("heading", { name: "Lời làm quen" })).toBeVisible();
  await expect(page.getByText("Chào Mai, mình cũng thích đọc sách.")).toBeVisible();
  await page.getByRole("button", { name: "Chấp nhận" }).click();
  await page.goto("/messages");
  await expect(page.getByRole("heading", { name: "Hội thoại", exact: true })).toBeVisible();
  await expect(page.getByText("Hẹn bạn cuối tuần nhé")).toBeVisible();
  await page.goto("/verification");
  await expect(page.getByRole("heading", { name: "Xác minh danh tính" })).toBeVisible();
  await page.getByRole("button", { name: "Tạo yêu cầu xác minh" }).click();
  await expect(page.getByText("ABC123").first()).toBeVisible();
  await expect(page.getByText("Mặt trước giấy tờ")).toBeVisible();
});
