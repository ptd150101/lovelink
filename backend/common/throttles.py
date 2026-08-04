from rest_framework.throttling import ScopedRateThrottle


class AuthRateThrottle(ScopedRateThrottle):
    scope = "auth"


class IntroRateThrottle(ScopedRateThrottle):
    scope = "intro"


class MessageRateThrottle(ScopedRateThrottle):
    scope = "message"


class PhoneOtpSendRateThrottle(ScopedRateThrottle):
    scope = "phone_otp_send"


class PhoneOtpVerifyRateThrottle(ScopedRateThrottle):
    scope = "phone_otp_verify"
