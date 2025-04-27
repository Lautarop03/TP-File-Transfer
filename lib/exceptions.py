# Custom exceptions for the Stop and Wait protocol
class MaxSendAttemptsExceeded(Exception):
    pass


class PacketDuplicateOrCorrupted(Exception):
    pass