class PaymentError(Exception):
    pass


class TransactionDeclined(PaymentError):
    pass


class GatewayError(PaymentError):
    pass


class UnableToTakePayment(PaymentError):
    pass
