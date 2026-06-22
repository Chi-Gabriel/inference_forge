class PlatformError(Exception):
    code = "platform_error"


class ResidencyTransitionError(PlatformError):
    code = "residency_transition_failed"
