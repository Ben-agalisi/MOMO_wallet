"""Wallet domain classes: accounts, transactions, and business rules."""

import datetime
import hashlib
import uuid


class InsufficientFundsError(Exception):
    """Raised when an account cannot cover an amount and its fee."""


def hash_pin(phone, pin):
    """Return a deterministic SHA-256 hash without storing a PIN in plain text."""
    return hashlib.sha256((phone + ":" + pin).encode("utf-8")).hexdigest()


def validate_pin(pin):
    """Ensure a PIN contains exactly four ASCII digits."""
    if len(pin) != 4 or any(character < "0" or character > "9" for character in pin):
        raise ValueError("Your PIN must contain exactly four digits.")


def validate_amount(amount):
    """Reject non-positive, NaN, and infinite amounts and return two decimals."""
    try:
        value = float(amount)
    except (TypeError, ValueError):
        raise ValueError("Enter a valid amount.")
    if value != value or value <= 0 or value >= float("inf"):
        raise ValueError("Amount must be greater than zero.")
    return round(value, 2)


class Transaction:
    """One recorded wallet event, suitable for a history row or receipt."""

    def __init__(self, kind, amount, fee=0.0, details="", reference=None,
                 status="SUCCESS", timestamp=None):
        self.kind = kind
        self.amount = round(float(amount), 2)
        self.fee = round(float(fee), 2)
        self.details = details
        self.reference = reference or uuid.uuid4().hex[:8].upper()
        self.status = status
        self.timestamp = timestamp or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        """Convert the transaction to JSON-compatible data."""
        return {
            "kind": self.kind,
            "amount": self.amount,
            "fee": self.fee,
            "details": self.details,
            "reference": self.reference,
            "status": self.status,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data):
        """Restore a transaction previously written as JSON."""
        return cls(
            kind=data["kind"],
            amount=data["amount"],
            fee=data.get("fee", 0.0),
            details=data.get("details", ""),
            reference=data["reference"],
            status=data.get("status", "SUCCESS"),
            timestamp=data["timestamp"],
        )

    def __str__(self):
        return (
            f"{self.timestamp} | {self.kind} | GH₵ {self.amount:.2f} | "
            f"Fee: GH₵ {self.fee:.2f} | {self.status} | Ref: {self.reference}\n"
            f"Details: {self.details}"
        )


class Account:
    """A personal mobile-money wallet and its transaction history."""

    account_type = "Personal"

    def __init__(self, name, phone, pin_hash_value, balance=0.0, transactions=None):
        self.name = name
        self.phone = phone
        self.pin_hash = pin_hash_value
        self.balance = round(float(balance), 2)
        self.transactions = list(transactions or [])

    def fee_for(self, amount):
        """Personal accounts do not pay a transaction fee."""
        return 0.0

    def deposit(self, amount):
        """Add funds and record a successful cash-in transaction."""
        amount = validate_amount(amount)
        self.balance = round(self.balance + amount, 2)
        transaction = Transaction("Deposit", amount, details="Funds added to wallet")
        self.transactions.append(transaction)
        return transaction

    def withdraw(self, amount):
        """Withdraw funds, including any account-specific transaction fee."""
        amount = validate_amount(amount)
        fee = round(self.fee_for(amount), 2)
        total = round(amount + fee, 2)
        if total > self.balance:
            raise InsufficientFundsError(
                f"This transaction needs GH₵ {total:.2f}, but your balance is "
                f"GH₵ {self.balance:.2f}."
            )
        self.balance = round(self.balance - total, 2)
        transaction = Transaction("Withdrawal", amount, fee, "Cash withdrawal")
        self.transactions.append(transaction)
        return transaction

    def transfer_to(self, recipient, amount, network_provider="MTN"):
        """Send money to another account, applying the sender's fee policy."""
        return self._send_transfer(recipient.phone, amount, network_provider, recipient)

    def transfer_to_phone(self, phone, amount, network_provider="MTN"):
        """Simulate sending to any valid phone, even without an app wallet."""
        phone = str(phone).strip()
        if not phone.isdigit() or not 10 <= len(phone) <= 15:
            raise ValueError("Enter a recipient phone number containing 10 to 15 digits.")
        return self._send_transfer(phone, amount, network_provider)

    def _send_transfer(self, phone, amount, network_provider, recipient=None):
        amount = validate_amount(amount)
        if self.phone == phone:
            raise ValueError("Choose a different phone number to send money to.")
        fee = round(self.fee_for(amount), 2)
        total = round(amount + fee, 2)
        if total > self.balance:
            raise InsufficientFundsError(
                f"This transfer needs GH₵ {total:.2f} including its fee, but your "
                f"balance is GH₵ {self.balance:.2f}."
            )

        reference = uuid.uuid4().hex[:8].upper()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        destination = f"{recipient.name} ({phone})" if recipient is not None else phone
        details = f"To {destination} via {network_provider}"
        if recipient is None:
            details += " (recipient is not registered in this app; simulated only)"
        sent = Transaction(
            "Transfer sent", amount, fee, details, reference, timestamp=timestamp,
        )

        self.balance = round(self.balance - total, 2)
        self.transactions.append(sent)
        if recipient is not None:
            received = Transaction(
                "Transfer received", amount, 0.0,
                f"From {self.name} ({self.phone}) via {network_provider}",
                reference, timestamp=timestamp,
            )
            recipient.balance = round(recipient.balance + amount, 2)
            recipient.transactions.append(received)
        return sent

    def to_dict(self):
        """Convert the account and its history to JSON-compatible data."""
        return {
            "account_type": self.account_type,
            "name": self.name,
            "phone": self.phone,
            "pin_hash": self.pin_hash,
            "balance": self.balance,
            "transactions": [item.to_dict() for item in self.transactions],
        }

    def __str__(self):
        return f"{self.account_type} account — {self.name} ({self.phone}), balance GH₵ {self.balance:.2f}"


class MerchantAccount(Account):
    """A merchant wallet that pays a 1% fee on withdrawals and transfers."""

    account_type = "Merchant"

    def fee_for(self, amount):
        """Charge merchants one percent of each outgoing transaction."""
        return round(float(amount) * 0.01, 2)