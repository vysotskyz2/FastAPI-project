class DomainException(Exception):
    status_code: int
    detail: str

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class UserAlreadyExistsError(DomainException):
    status_code = 409


class UserNotFoundError(DomainException):
    status_code = 404


class UserAlreadyBlockedError(DomainException):
    status_code = 400


class UserAlreadyActiveError(DomainException):
    status_code = 400


class UserBlockedError(DomainException):
    status_code = 400


class NegativeBalanceError(DomainException):
    status_code = 400


class BalanceNotFoundError(DomainException):
    status_code = 400


class TransactionNotFoundError(DomainException):
    status_code = 400


class TransactionNotBelongToUserError(DomainException):
    status_code = 400


class TransactionAlreadyRollbackedError(DomainException):
    status_code = 400
