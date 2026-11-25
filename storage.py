"""JSON persistence and statement export for the MoMo wallet."""

import json

from models import Account, MerchantAccount, Transaction, hash_pin, validate_pin


DATA_FILE = "wallet_data.json"


class WalletDataError(Exception):
    """Raised when saved wallet data cannot safely be read."""


class WalletStore:
    """Load, register, find, and save the app's wallet accounts."""

    def __init__(self, filename=DATA_FILE):
        self.filename = filename
        self.accounts = []

    def load(self):
        """Load accounts, creating demo accounts only on first launch."""
        try:
            with open(self.filename, "r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            self.accounts = self._demo_accounts()
            self.save()
            return
        except (OSError, json.JSONDecodeError) as error:
            raise WalletDataError(f"Could not read {self.filename}: {error}")

        try:
            if not isinstance(data, dict) or not isinstance(data.get("accounts"), list):
                raise ValueError("The file must contain an accounts list.")
            accounts = []
            seen_phones = set()
            for record in data["accounts"]:
                if not isinstance(record, dict):
                    raise ValueError("An account record is not an object.")
                account_type = record["account_type"]
                account_class = MerchantAccount if account_type == "Merchant" else Account
                if account_type not in ("Personal", "Merchant"):
                    raise ValueError("An account has an unknown account type.")
                transactions = [Transaction.from_dict(item) for item in record["transactions"]]
                account = account_class(
                    record["name"], record["phone"], record["pin_hash"],
                    record["balance"], transactions,
                )
                if account.phone in seen_phones:
                    raise ValueError("The file contains duplicate phone numbers.")
                seen_phones.add(account.phone)
                accounts.append(account)
            self.accounts = accounts
        except (KeyError, TypeError, ValueError) as error:
            raise WalletDataError(f"Saved wallet data is incomplete or invalid: {error}")

    def save(self):
        """Persist all accounts and transaction histories as readable JSON."""
        data = {"accounts": [account.to_dict() for account in self.accounts]}
        try:
            with open(self.filename, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
        except OSError as error:
            raise WalletDataError(f"Could not save {self.filename}: {error}")

    def register(self, name, phone, pin, account_type):
        """Create a zero-balance account after validating its unique identity."""
        name = name.strip()
        phone = phone.strip()
        if not name:
            raise ValueError("Enter the account holder's name.")
        if not phone.isdigit() or not 10 <= len(phone) <= 15:
            raise ValueError("Enter a phone number containing 10 to 15 digits.")
        if self.get_account(phone) is not None:
            raise ValueError("An account with that phone number already exists.")
        validate_pin(pin)
        account_classes = {"Personal": Account, "Merchant": MerchantAccount}
        if account_type not in account_classes:
            raise ValueError("Choose Personal or Merchant account type.")
        account = account_classes[account_type](name, phone, hash_pin(phone, pin))
        self.accounts.append(account)
        return account

    def get_account(self, phone):
        """Find an account by phone number, or return None."""
        for account in self.accounts:
            if account.phone == phone:
                return account
        return None

    def authenticate(self, phone, pin):
        """Return the matching account only when its PIN hash is correct."""
        account = self.get_account(phone.strip())
        if account is not None and account.pin_hash == hash_pin(account.phone, pin):
            return account
        return None

    def export_statement(self, account):
        """Write a readable text statement beside the app's launch directory."""
        filename = f"statement_{account.phone}.txt"
        lines = [
            "MOMO WALLET — MINI STATEMENT",
            "Simulated Sandbox (not real money)",
            str(account),
            "",
            "TRANSACTIONS",
            "------------",
        ]
        if account.transactions:
            for transaction in account.transactions:
                lines.extend((str(transaction), ""))
        else:
            lines.append("No transactions yet.")
        try:
            with open(filename, "w", encoding="utf-8") as file:
                file.write("\n".join(lines).rstrip() + "\n")
        except OSError as error:
            raise WalletDataError(f"Could not write {filename}: {error}")
        return filename

    @staticmethod
    def _demo_accounts():
        """Build the two first-run demo accounts with documented PINs."""
        return [
            Account("Ama Mensah", "0240000000", hash_pin("0240000000", "1234"), 500.00),
            MerchantAccount("Kojo's Store", "0200000000", hash_pin("0200000000", "4321"), 1250.00),
        ]