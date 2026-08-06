---
name: LoveLink
description: Hệ thống web sáng, tin cậy và thân thiện cho kết nối có đồng thuận.
colors:
  trust-blue: "#2563eb"
  trust-blue-deep: "#1d4ed8"
  heartbeat-pink: "#f43f72"
  verified-green: "#059669"
  caution-amber: "#d97706"
  safety-red: "#dc2626"
  ink: "#172033"
  slate: "#64748b"
  line: "#e2e8f0"
  surface: "#ffffff"
  canvas: "#f7f9fc"
typography:
  display:
    fontFamily: "Inter, Be Vietnam Pro, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "clamp(2.5rem, 6vw, 5.3rem)"
    fontWeight: 850
    lineHeight: 1.02
    letterSpacing: "-0.06em"
  headline:
    fontFamily: "Inter, Be Vietnam Pro, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "2rem"
    fontWeight: 850
    lineHeight: 1.2
    letterSpacing: "-0.03em"
  title:
    fontFamily: "Inter, Be Vietnam Pro, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1.15rem"
    fontWeight: 750
    lineHeight: 1.3
  body:
    fontFamily: "Inter, Be Vietnam Pro, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Inter, Be Vietnam Pro, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "0.14em"
rounded:
  control: "11px"
  button: "12px"
  surface: "16px"
  prominent: "24px"
  pill: "999px"
spacing:
  xs: "7px"
  sm: "12px"
  md: "18px"
  lg: "24px"
  xl: "34px"
components:
  button-primary:
    backgroundColor: "{colors.trust-blue}"
    textColor: "{colors.surface}"
    rounded: "{rounded.button}"
    padding: "11px 18px"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.trust-blue-deep}"
    textColor: "{colors.surface}"
  button-secondary:
    backgroundColor: "#eef4ff"
    textColor: "{colors.trust-blue}"
    rounded: "{rounded.button}"
    padding: "11px 18px"
    height: "44px"
  button-danger:
    backgroundColor: "{colors.safety-red}"
    textColor: "{colors.surface}"
    rounded: "{rounded.button}"
    padding: "11px 18px"
    height: "44px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "11px 13px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.surface}"
    padding: "24px"
  badge:
    backgroundColor: "#f1f5f9"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "5px 9px"
---

# Design System: LoveLink

## Overview

**Creative North Star: "Nơi gặp gỡ đáng tin"**

LoveLink hiện dùng một hệ thống sáng, tin cậy và thân thiện: nền trắng hoặc xanh xám rất nhạt, cấu trúc rõ ràng, sắc xanh làm trục chức năng và sắc hồng chỉ tạo tín hiệu hẹn hò mềm. Hệ thống ưu tiên thao tác dễ hiểu hơn biểu đạt cao; icon nét đơn, nhãn trạng thái và khoảng trắng vừa phải giúp người dùng đọc nhanh luồng hồ sơ, xác minh, kết nối và trò chuyện.

Ngôn ngữ hình thức mềm mại nhưng không mong manh. Card bo vừa-lớn, nút có vùng chạm tối thiểu rõ, input có focus ring xanh và trạng thái an toàn dùng màu ngữ nghĩa nhất quán. Brand hiện được thể hiện bằng wordmark chữ LoveLink, chưa có logo hình ảnh riêng.

**Key Characteristics:**
- Nền sáng, xanh chức năng, hồng điểm xuyết.
- Bề mặt bo mềm với viền mảnh và shadow ambient nhẹ.
- Trạng thái xác minh, thành công, cảnh báo và nguy hiểm được mã hóa bằng màu.
- Layout utility-first, responsive từ desktop grid sang mobile stack hoặc bottom navigation.
- Một sans-serif thống nhất; hierarchy đến từ scale, weight và tracking.

## Colors

Bảng màu lấy xanh rõ, lạnh làm trục tin cậy; các màu ngữ nghĩa giữ vai trò cụ thể, còn hồng tạo nét hẹn hò nhưng không điều khiển tác vụ.

### Primary
- **Xanh Tin Cậy:** hành động chính, active navigation, focus, progress và tín hiệu tương tác đáng tin.
- **Xanh Tin Cậy Sâu:** trạng thái hover của hành động chính.

### Secondary
- **Hồng Rung Động:** điểm nhấn cảm xúc trên landing và gradient ảnh mẫu; dùng hiếm để không cạnh tranh với xanh chức năng.

### Tertiary
- **Xanh Xác Minh:** thành công, số điện thoại hoặc bằng chứng đã xác minh.
- **Hổ Phách Thận Trọng:** cảnh báo và trạng thái cần chú ý.
- **Đỏ An Toàn:** lỗi, từ chối và hành động nguy hiểm.

### Neutral
- **Mực Đêm:** nội dung chính và toast tối.
- **Xám Slate:** nội dung phụ, icon và navigation chưa active.
- **Đường Viền Mây:** divider, border card và ranh giới control.
- **Bề Mặt Trắng:** card, input, top bar, modal.
- **Nền Sương:** canvas ứng dụng và vùng section phụ.

### Named Rules

**The Trust Leads Rule.** Xanh Tin Cậy mang hành động và trạng thái điều hướng; Hồng Rung Động không thay thế nó trên luồng vận hành.

**The Semantic State Rule.** Xanh lá, hổ phách và đỏ chỉ dùng khi chúng truyền đạt trạng thái thật; không dùng như trang trí.

## Typography

**Display Font:** Inter với Be Vietnam Pro và system sans-serif dự phòng.
**Body Font:** Inter với Be Vietnam Pro và system sans-serif dự phòng.

**Character:** Một sans-serif hiện đại, trực tiếp, hỗ trợ tiếng Việt. Hệ thống không dùng cặp font; khác biệt đến từ độ đậm cao, tracking âm ở tiêu đề và tracking rộng ở eyebrow.

### Hierarchy
- **Display:** tiêu đề landing rất lớn, đậm, sát dòng và tracking âm; chỉ dành cho tuyên bố đầu trang.
- **Headline:** tiêu đề trang ứng dụng, gọn hơn display nhưng vẫn đậm và hơi nén chữ.
- **Title:** tên hồ sơ, tiêu đề card và nhóm nội dung.
- **Body:** copy chức năng và mô tả, line-height rộng hơn khi đọc đoạn dài.
- **Label:** eyebrow uppercase nhỏ, đậm, tracking rộng; dùng để định hướng section, không dùng cho đoạn văn.

### Named Rules

**The One Sans Rule.** Giữ một sans-serif xuyên suốt; hierarchy bằng scale, weight và spacing, không thêm font trang trí khi chưa thay thế identity.

## Layout

Canvas dùng container trung tâm tối đa 1180px; biến thể rộng đạt 1360px, biến thể hẹp đạt 850px. Nhịp section chủ yếu theo 12–24px bên trong component, 28–34px giữa nhóm trang và khoảng lớn hơn trên landing. Desktop ưu tiên grid: landing hai cột, discovery sidebar 280px cộng nội dung, hồ sơ ba cột, form hai cột.

Ở 980px, navigation desktop thu gọn nhãn, profile grid còn hai cột và landing chuyển một cột. Ở 700px, top bar giảm chiều cao, navigation chính chuyển thành bottom navigation cố định, page gutter còn 14px, form và content stack một cột. Profile grid giữ hai cột đến 430px rồi chuyển một cột. Các luồng chat và call dùng chiều cao viewport; media giữ tỷ lệ 4:5 cho hồ sơ và 3:4 cho self-view.

**The Task Before Flourish Rule.** Trong app, giữ hành động chính và trạng thái trong vùng quét đầu tiên; biểu đạt thương hiệu nằm ở chi tiết, không phá grid tác vụ.

## Elevation & Depth

Hệ thống dùng phân lớp nhẹ. Viền mảnh giữ cấu trúc thường trực; shadow ambient tách card, auth surface, modal, toast và phần tử media nổi khỏi canvas. Shadow mạnh hơn chỉ xuất hiện ở landing mockup hoặc overlay cần ưu tiên. Tonal backgrounds xanh nhạt, hồng nhạt và xanh lá nhạt bổ sung chiều sâu mà không tạo cảm giác nặng.

### Shadow Vocabulary
- **Ambient Surface:** `0 4px 18px rgba(15,23,42,.04)` cho card nội dung thông thường.
- **Raised Surface:** `0 12px 35px rgba(15,23,42,.08)` cho auth card, modal, toast và phần tử nổi.
- **Floating Control:** `0 3px 10px rgba(15,23,42,.18)` cho action nhỏ nằm trên ảnh.
- **Hero Lift:** `0 32px 80px rgba(37,99,235,.18)` chỉ cho mock profile trên landing.

### Named Rules

**The Border First Rule.** Dùng border để định cấu trúc; chỉ thêm shadow khi bề mặt thật sự nằm trên một lớp khác.

## Shapes

Ngôn ngữ hình thức dùng góc cong liên tục: control 11–12px, card chuẩn 16–18px, auth hoặc profile hero 24px, avatar tròn và badge pill 999px. Ảnh hồ sơ giữ crop 4:5; thumbnail và action nhỏ dùng bán kính nhỏ hơn. Border chủ yếu 1px; vùng upload và evidence dùng 2px dashed để báo affordance.

**The Soft Not Cute Rule.** Bo góc tạo cảm giác an toàn và dễ tiếp cận; không biến mọi container thành pill hoặc dùng hình trang trí khiến app giống trò chơi.

## Components

### Buttons
- **Shape:** chữ nhật bo mềm, bán kính 12px; vùng chạm tối thiểu 44px.
- **Primary:** nền Xanh Tin Cậy, chữ trắng, padding 11px × 18px, weight cao.
- **Hover / Focus:** hover tối màu và nhấc 1px; disabled giảm opacity, bỏ transform. Nút cần focus-visible rõ dù incumbent CSS hiện chưa chuẩn hóa riêng.
- **Secondary:** nền xanh rất nhạt, chữ xanh, viền xanh nhạt.
- **Ghost:** nền trong suốt, chữ slate.
- **Danger:** nền đỏ, chữ trắng; chỉ dành cho hành động phá hủy hoặc từ chối.

### Chips
- **Style:** pill nhỏ, nền slate rất nhạt, chữ đậm vừa; verified/success chuyển nền xanh lá nhạt và chữ xanh lá đậm, warning dùng cam nhạt.
- **State:** checkbox filters có cùng silhouette pill; selected state cần giữ tín hiệu native checkbox hoặc màu trạng thái rõ.

### Cards / Containers
- **Corner Style:** 16px mặc định; profile card 18px; auth và prominent profile card 24px.
- **Background:** trắng trên canvas Nền Sương.
- **Shadow Strategy:** ambient rất nhẹ; prominent surfaces dùng Raised Surface.
- **Border:** 1px Đường Viền Mây.
- **Internal Padding:** thường 18–24px; auth card 32px.

### Inputs / Fields
- **Style:** nền trắng, viền xám 1px, bán kính 11px, padding 11px × 13px; label đậm vừa và hint slate.
- **Focus:** border xanh cùng focus ring xanh nhạt 3px.
- **Error / Disabled:** lỗi dùng đỏ; disabled phải giữ opacity và cursor rõ. Textarea cho phép resize dọc.

### Navigation
- Desktop dùng top bar trắng 70px, wordmark xanh, nav trung tâm với icon 18px; item active hoặc hover có nền xanh rất nhạt, chữ xanh và bán kính 10px.
- Mobile dùng bottom navigation cao 64px; icon trên nhãn nhỏ, active chuyển xanh. Settings navigation là hàng tab cuộn ngang với active fill xanh nhạt.

### Profile Card

Ảnh 4:5 dẫn đầu, nội dung nằm trong bề mặt trắng có viền và shadow nhẹ. Tên, tuổi và verified badges tạo hierarchy; metadata dùng icon nhỏ và slate; interests dùng chip; CTA primary chiếm toàn chiều rộng. Placeholder dùng gradient xanh-hồng mềm thay cho ảnh giả chi tiết.

### Messaging

Tin nhắn nhận dùng nền slate nhạt; tin nhắn gửi dùng Xanh Tin Cậy với chữ trắng. Bubble bo 14px, giới hạn khoảng 72% chiều rộng; composer tách bằng border và giữ input tối thiểu 44px.

## Do's and Don'ts

### Do:
- **Do** dùng Xanh Tin Cậy cho CTA, focus và trạng thái active quan trọng.
- **Do** giữ card trắng trên canvas xanh xám nhạt, với border mảnh trước khi thêm shadow.
- **Do** giữ ảnh hồ sơ 4:5, avatar tròn và badge trạng thái dễ phân biệt.
- **Do** giữ control tương tác chính cao tối thiểu 44px và layout chuyển stack ở mobile.
- **Do** dùng màu semantic đúng nghĩa cho xác minh, cảnh báo, lỗi và nguy hiểm.

### Don't:
- **Don't** dùng Hồng Rung Động làm màu CTA vận hành hoặc phủ diện tích lớn trong app.
- **Don't** thêm shadow mạnh cho card thông thường; Hero Lift chỉ thuộc landing mockup.
- **Don't** pha thêm font trang trí, glassmorphism hoặc gradient mới khi chưa có quyết định thay identity.
- **Don't** bẻ tỷ lệ ảnh hồ sơ, che verified badges hoặc đặt hành động riêng tư ngoài consent state.
- **Don't** dùng màu trạng thái như trang trí hoặc dựa vào màu đơn độc để truyền đạt thông tin.
