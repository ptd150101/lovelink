from rest_framework.throttling import ScopedRateThrottle
class AuthRateThrottle(ScopedRateThrottle): scope = "auth"
class IntroRateThrottle(ScopedRateThrottle): scope = "intro"
class MessageRateThrottle(ScopedRateThrottle): scope = "message"
