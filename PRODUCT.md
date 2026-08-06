# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

LoveLink phục vụ trước tiên người trưởng thành độc thân tại Việt Nam đang tìm một mối quan hệ nghiêm túc. Họ cần đánh giá hồ sơ theo tiêu chí rõ ràng, giảm rủi ro khi tiếp xúc với người lạ và chỉ trò chuyện hoặc gọi điện sau khi cả hai bên đồng ý kết nối.

Nhân sự vận hành gồm reviewer xử lý xác minh danh tính và moderator xử lý an toàn cộng đồng.

## Product Purpose

LoveLink là nền tảng hẹn hò giúp người dùng tạo hồ sơ đáng tin cậy, khám phá người phù hợp theo tiêu chí cụ thể, xin kết nối có đồng thuận, nhắn tin riêng tư và gọi video 1–1.

Thành công nghĩa là người dùng có thể đi từ hồ sơ đã hoàn thiện đến một cuộc trò chuyện hoặc cuộc gọi được cả hai bên chấp thuận, với các biện pháp xác minh, riêng tư và xử lý lạm dụng xuyên suốt hành trình.

## Positioning

LoveLink đặt niềm tin và sự đồng thuận làm cơ chế cốt lõi: hồ sơ có thể được xác minh thủ công; trò chuyện và gọi video chỉ mở sau kết nối hai chiều; quyền riêng tư, chặn, báo cáo, moderation và audit là một phần của luồng sản phẩm thay vì lớp bổ sung.

## Operating Context

Luồng thành viên gồm đăng ký và xác minh liên hệ, onboarding hồ sơ, tải và sắp xếp ảnh, thiết lập quyền riêng tư, khám phá bằng bộ lọc, xem hồ sơ, gửi hoặc xử lý lời làm quen, nhắn tin realtime, gọi video 1–1, nhận thông báo và quản lý tài khoản.

Reviewer dùng hàng đợi xác minh và bằng chứng riêng tư có liên kết truy cập tạm thời. Moderator dùng Django Admin để xử lý báo cáo, cảnh báo, ẩn nội dung, đình chỉ hoặc cấm tài khoản. Hệ thống vận hành trên web; giao diện và nội dung hiện tại dùng tiếng Việt.

## Capabilities and Constraints

- MVP bao gồm hồ sơ, quyền riêng tư theo trường dữ liệu, ảnh 4:5, khám phá đa tiêu chí, xác minh số điện thoại và danh tính, kết nối hai chiều, chat realtime 1–1, video call LiveKit tự host, thông báo, chặn, báo cáo, moderation và quản lý tài khoản.
- Hồ sơ chỉ hiển thị cho thành viên đã đăng nhập và đang hoạt động. Presence ở mức thô, chỉ dành cho kết nối và tôn trọng lựa chọn chia sẻ trạng thái.
- Bằng chứng xác minh nằm trong vùng lưu trữ riêng tư; truy cập dùng URL ký ngắn hạn và được audit. Token LiveKit phải ngắn hạn, theo phòng; secret chỉ ở server.
- Production phải dùng HTTPS, SMTP/SMS thật, secret mạnh, log có cấu trúc, monitoring, backup mã hóa, lifecycle cho object storage, MFA bắt buộc cho staff và chính sách pháp lý/quyền riêng tư đã được rà soát.
- Phạm vi MVP đóng: không có social feed, bình luận công khai, stories, livestream, group chat/call, tiền ảo, boost/payment, AI matching, recording, file/voice message, social login hoặc native mobile app.

## Brand Commitments

Tên sản phẩm là LoveLink. Ngôn ngữ sản phẩm hiện tại là tiếng Việt. Cam kết không thể thỏa hiệp: an toàn và đồng thuận, gồm xác minh, moderation, audit, privacy controls và consent gates.

Các tuyên bố hiện có cần được bảo toàn về mặt sự thật: “Hẹn hò an toàn · Kết nối có đồng thuận”, “hồ sơ đáng tin cậy” và “Kết nối chân thành”.

## Evidence on Hand

- Phạm vi, kiến trúc, yêu cầu bảo mật và production: [README.md](README.md).
- Luồng API và state machine: [docs/API.md](docs/API.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- Copy sản phẩm hiện hữu: [frontend/app/page.tsx](frontend/app/page.tsx), [frontend/app/layout.tsx](frontend/app/layout.tsx).
- Browser tests và full-stack flow: [frontend/e2e/public.spec.ts](frontend/e2e/public.spec.ts), [frontend/e2e/fullstack.spec.ts](frontend/e2e/fullstack.spec.ts).
- Chưa có logo hình ảnh, testimonial, số liệu kết quả, khách hàng, press proof hoặc benchmark được xác nhận; công việc tương lai không được tự tạo các bằng chứng này.
- Chính sách quyền riêng tư hiện chỉ là bản mẫu cần rà soát pháp lý trước production; chưa có bằng chứng về bộ điều khoản pháp lý hoàn chỉnh đã được phê duyệt.

## Product Principles

1. Mọi tương tác riêng tư bắt đầu bằng sự đồng thuận rõ ràng của cả hai bên.
2. Niềm tin phải đến từ cơ chế có thể kiểm chứng, phân quyền và audit, không chỉ từ copy marketing.
3. Quyền riêng tư là mặc định; chỉ thu thập, hiển thị và lưu giữ dữ liệu trong phạm vi cần thiết.
4. Khám phá phải minh bạch bằng tiêu chí người dùng hiểu và kiểm soát được.
5. Giữ phạm vi MVP tập trung; không thêm cơ chế gây nghiện hoặc kiếm tiền khi chưa có quyết định sản phẩm mới.

## Accessibility & Inclusion

Chưa cam kết một tiêu chuẩn accessibility cụ thể. Trong thời gian quyết định còn mở, mọi surface web phải giữ semantic HTML, khả năng sử dụng bằng bàn phím, nhãn truy cập được và nội dung dễ đọc; không được tuyên bố tuân thủ WCAG khi chưa được kiểm chứng.
