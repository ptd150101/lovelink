import { expect, Page, test } from "@playwright/test";

const user = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "member@example.com",
  status: "active",
  is_email_verified: true,
  is_phone_verified: false,
  created_at: "2026-08-04T00:00:00Z",
};

function photoDataUrl(index: number) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="1000"><rect width="100%" height="100%" fill="#dbeafe"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-size="80">${index}</text></svg>`;
  return `data:image/svg+xml,${encodeURIComponent(svg)}`;
}

function makeProfile(photoCount: number) {
  const suffix = String(photoCount).padStart(2, "0");
  return {
    public_id: `22222222-2222-2222-2222-2222222222${suffix}`,
    display_name: "Mai",
    age: 27,
    gender: "female",
    current_province: { code: "01", name: "Hà Nội" },
    hometown_province: { code: "35", name: "Ninh Bình" },
    height_cm: 162,
    occupation_category: {
      id: "33333333-3333-3333-3333-333333333333",
      name: "Công nghệ thông tin",
    },
    occupation_text: "Software Engineer",
    education_level: "postgraduate",
    income_band: "private",
    relationship_status: "widowed",
    relationship_goal: "long_term",
    religion: "buddhism",
    smoking_status: "often",
    drinking_status: "often",
    children_status: "private",
    children_plan: "unsure",
    bio: "Yêu công việc, thích chạy bộ và khám phá những quán ăn mới.",
    looking_for: "Một mối quan hệ ổn định, tôn trọng không gian riêng của nhau.",
    interests: [{ id: "1", name: "Chạy bộ" }],
    photos: Array.from({ length: photoCount }, (_, index) => ({
      id: `photo-${photoCount}-${index}`,
      public_url: photoDataUrl(index + 1),
      thumbnail_url: photoDataUrl(index + 1),
      position: index,
      is_primary: index === Math.min(1, Math.max(photoCount - 1, 0)),
    })),
    completion_percent: 100,
    verification_level: "none",
    is_phone_verified: false,
    connection_status: "none",
  };
}

const profiles = new Map(
  [0, 1, 2, 5, 6, 20].map((count) => {
    const profile = makeProfile(count);
    return [profile.public_id, profile] as const;
  }),
);

async function mockProfileApi(page: Page) {
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname.replace(/^\/api\/v1/, "");
    if (path === "/auth/me") return route.fulfill({ json: user });
    if (path === "/auth/csrf") {
      return route.fulfill({ json: { csrfToken: "test" } });
    }
    if (path.startsWith("/profiles/")) {
      const publicId = path.slice("/profiles/".length);
      const profile = profiles.get(publicId);
      if (profile) return route.fulfill({ json: profile });
    }
    return route.fulfill({
      status: 404,
      json: { detail: `Unhandled test route: ${path}` },
    });
  });
}

test("profile gallery handles 0, 1, 2, 5, 6 and 20 photos", async ({ page }) => {
  await mockProfileApi(page);

  for (const photoCount of [0, 1, 2, 5, 6, 20]) {
    const profile = makeProfile(photoCount);
    await page.goto(`/profiles/${profile.public_id}`);
    await expect(page.getByRole("heading", { name: /Mai, 27/ })).toBeVisible();

    if (photoCount === 0) {
      await expect(page.getByTestId("profile-photo-placeholder")).toBeVisible();
      await expect(page.getByText("Chưa có ảnh")).toBeVisible();
      continue;
    }

    await expect(page.getByTestId("profile-main-photo")).toHaveCSS(
      "aspect-ratio",
      "1 / 1",
    );
    const expectedThumbnailSlots = Math.min(Math.max(photoCount - 1, 0), 4);
    await expect(page.getByTestId("profile-thumbnail")).toHaveCount(
      expectedThumbnailSlots,
    );

    if (photoCount > 5) {
      await expect(page.getByTestId("profile-more-photos")).toHaveText(
        `+${photoCount - 4}`,
      );
    } else {
      await expect(page.getByTestId("profile-more-photos")).toHaveCount(0);
    }
  }
});

test("profile enums are fully localized to Vietnamese", async ({ page }) => {
  await mockProfileApi(page);
  const profile = makeProfile(1);
  await page.goto(`/profiles/${profile.public_id}`);

  await expect(page.getByText("Sau đại học")).toBeVisible();
  await expect(page.getByText("Không muốn công khai")).toBeVisible();
  await expect(page.getByText("Hẹn hò lâu dài")).toBeVisible();
  await expect(page.getByText("Góa")).toBeVisible();
  await expect(page.getByText("Thường xuyên")).toHaveCount(2);
  await expect(page.getByText("Không muốn chia sẻ")).toBeVisible();
  await expect(page.getByText("Chưa chắc chắn")).toBeVisible();
  await expect(page.getByText("Phật giáo")).toBeVisible();

  const text = await page.locator("body").innerText();
  expect(text).not.toMatch(/\b(widowed|often|private|unsure|long_term|postgraduate)\b/i);
});

test("photo viewer opens the selected photo and supports keyboard controls", async ({
  page,
}) => {
  await mockProfileApi(page);
  const profile = makeProfile(6);
  await page.goto(`/profiles/${profile.public_id}`);

  const mainPhoto = page.getByTestId("profile-main-photo");
  await mainPhoto.focus();
  await mainPhoto.click();

  const viewer = page.getByRole("dialog", { name: "Xem ảnh của Mai" });
  await expect(viewer).toBeVisible();
  await expect(viewer).toHaveAttribute("aria-modal", "true");
  await expect(viewer.getByText("1 / 6")).toBeVisible();
  await expect(page.getByTestId("photo-viewer-image")).toHaveCSS(
    "object-fit",
    "contain",
  );
  await expect(page.locator("body")).toHaveCSS("overflow", "hidden");

  await page.keyboard.press("ArrowRight");
  await expect(viewer.getByText("2 / 6")).toBeVisible();
  await page.keyboard.press("ArrowLeft");
  await expect(viewer.getByText("1 / 6")).toBeVisible();

  await page.keyboard.press("Escape");
  await expect(viewer).toBeHidden();
  await expect(mainPhoto).toBeFocused();
  await expect(page.locator("body")).not.toHaveCSS("overflow", "hidden");
});

test("profile detail collapses to one column on mobile", async ({ page }) => {
  await page.setViewportSize({ width: 600, height: 900 });
  await mockProfileApi(page);
  const profile = makeProfile(2);
  await page.goto(`/profiles/${profile.public_id}`);

  const columnCount = await page
    .getByTestId("profile-detail-hero")
    .evaluate((element) =>
      getComputedStyle(element).gridTemplateColumns.trim().split(/\s+/).length,
    );
  expect(columnCount).toBe(1);
});
