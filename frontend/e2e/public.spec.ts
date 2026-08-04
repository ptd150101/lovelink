import { expect, Page, test } from "@playwright/test";

const user = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "member@example.com",
  status: "active",
  is_email_verified: true,
  is_phone_verified: false,
  created_at: "2026-08-04T00:00:00Z",
};

const profile = {
  public_id: "22222222-2222-2222-2222-222222222222",
  display_name: "Mai",
  age: 27,
  gender: "female",
  current_province: { code: "01", name: "Hà Nội" },
  hometown_province: { code: "36", name: "Thanh Hóa" },
  height_cm: 162,
  occupation_category: { id: "33333333-3333-3333-3333-333333333333", name: "Công nghệ thông tin" },
  occupation_text: "Software Engineer",
  education_level: "university",
  income_band: "20_30",
  relationship_status: "single",
  relationship_goal: "serious",
  religion: "",
  smoking_status: "never",
  drinking_status: "sometimes",
  children_status: "none",
  children_plan: "want",
  bio: "Mình thích đọc sách, chạy bộ và khám phá những quán cà phê yên tĩnh ở Hà Nội.",
  looking_for: "Một người chân thành, biết lắng nghe và nghiêm túc trong mối quan hệ.",
  interests: [{ id: "1", name: "Đọc sách" }, { id: "2", name: "Cà phê" }],
  photos: [],
  completion_percent: 100,
  verification_level: "identity_verified",
  verified_at: "2026-08-04T00:00:00Z",
  connection_status: "none",
};

const referenceData = {
  provinces: [{ code: "01", name: "Hà Nội" }, { code: "36", name: "Thanh Hóa" }],
  occupations: [{ id: "33333333-3333-3333-3333-333333333333", name: "Công nghệ thông tin" }],
  interests: [{ id: "1", name: "Đọc sách" }, { id: "2", name: "Cà phê" }],
  choices: {
    genders: [["male", "Nam"], ["female", "Nữ"]],
    education: [["university", "Đại học"]],
    income: [["20_30", "20–30 triệu"]],
    goals: [["serious", "Tìm hiểu nghiêm túc"]],
    relationship_status: [["single", "Độc thân"]],
    habits: [["never", "Không"], ["sometimes", "Thỉnh thoảng"]],
    children: [["none", "Chưa có"]],
    children_plan: [["want", "Muốn có"]],
  },
};

async function mockAuthenticatedApi(page: Page) {
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname.replace(/^\/api\/v1/, "");

    if (path === "/auth/me") return route.fulfill({ json: user });
    if (path === "/auth/csrf") return route.fulfill({ json: { csrfToken: "test" } });
    if (path === "/reference-data") return route.fulfill({ json: referenceData });
    if (path === "/discover") return route.fulfill({ json: { results: [profile], next: null } });
    if (path === `/profiles/${profile.public_id}`) return route.fulfill({ json: profile });
    if (path === "/connections/received") {
      return route.fulfill({ json: { results: [{ id: "44444444-4444-4444-4444-444444444444", sender: profile, receiver: profile, other_user: profile, intro_message: "Chào Mai, mình cũng thích đọc sách.", status: "pending", sent_at: "2026-08-04T00:00:00Z", expires_at: "2026-08-18T00:00:00Z" }] } });
    }
    if (path.includes("/connections/") && request.method() === "POST") return route.fulfill({ json: { status: "accepted" } });
    if (path === "/conversations") {
      return route.fulfill({ json: { results: [{ id: "55555555-5555-5555-5555-555555555555", other_user: profile, last_message: { text: "Hẹn bạn cuối tuần nhé" }, last_message_at: "2026-08-04T00:00:00Z", unread_count: 1, created_at: "2026-08-04T00:00:00Z" }] } });
    }
    if (path === "/verification/current") return route.fulfill({ json: null });
    if (path === "/verification/requests" && request.method() === "POST") {
      return route.fulfill({ status: 201, json: { id: "66666666-6666-6666-6666-666666666666", status: "draft", challenge_code: "ABC123", evidence: [] } });
    }
    return route.fulfill({ status: 404, json: { detail: `Unhandled test route: ${path}` } });
  });
}

test("landing and authentication pages render", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("LoveLink").first()).toBeVisible();
  await page.goto("/auth/login");
  await expect(page.getByRole("heading", { name: /đăng nhập/i })).toBeVisible();
  await page.goto("/auth/register");
  await expect(page.getByRole("heading", { name: /đăng ký/i })).toBeVisible();
  await page.goto("/auth/forgot-password");
  await expect(page.getByRole("heading", { name: /quên mật khẩu/i })).toBeVisible();
});

test("authenticated member can discover and inspect a verified profile", async ({ page }) => {
  await mockAuthenticatedApi(page);
  await page.goto("/discover");
  await expect(page.getByRole("heading", { name: "Tìm người phù hợp" })).toBeVisible();
  await expect(page.getByText("Mai, 27")).toBeVisible();
  await expect(page.getByText("Software Engineer")).toBeVisible();
  await page.getByRole("link", { name: "Xem hồ sơ" }).click();
  await expect(page.getByRole("heading", { name: /Mai, 27/ })).toBeVisible();
  await expect(page.getByText("Danh tính đã xác minh")).toBeVisible();
  await expect(page.getByRole("button", { name: /Gửi lời làm quen/ })).toBeVisible();
});

test("connections, messages and verification entry points are usable", async ({ page }) => {
  await mockAuthenticatedApi(page);
  await page.goto("/connections");
  await expect(page.getByRole("heading", { name: "Lời làm quen" })).toBeVisible();
  await expect(page.getByText("Chào Mai, mình cũng thích đọc sách.")).toBeVisible();
  await page.getByRole("button", { name: "Chấp nhận" }).click();
  await page.goto("/messages");
  await expect(page.getByRole("heading", { name: "Hội thoại" })).toBeVisible();
  await expect(page.getByText("Hẹn bạn cuối tuần nhé")).toBeVisible();
  await page.goto("/verification");
  await expect(page.getByRole("heading", { name: "Xác minh danh tính" })).toBeVisible();
  await page.getByRole("button", { name: "Tạo yêu cầu xác minh" }).click();
  await expect(page.getByText("ABC123")).toBeVisible();
  await expect(page.getByText("Mặt trước giấy tờ")).toBeVisible();
});
