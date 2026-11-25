"""Small standard-library tests for wallet rules and persistence."""

import os
import tempfile
import unittest
import datetime

from analytics import summarize_transactions
from models import Account, InsufficientFundsError, MerchantAccount, hash_pin
from models import Transaction
from storage import WalletStore


class AnalyticsTests(unittest.TestCase):
    def test_dashboard_summarizes_transactions_within_selected_period(self):
        now = datetime.datetime(2025, 1, 10, 12, 0, 0)
        transactions = [
            Transaction("Deposit", 100, timestamp="2025-01-10 09:00:00"),
            Transaction("Withdrawal", 20, fee=1, timestamp="2025-01-03 12:00:00"),
            Transaction("Transfer received", 5, timestamp="2025-01-07 11:00:00"),
            Transaction("Transfer sent", 10, timestamp="2025-01-02 12:00:00"),
        ]

        totals = summarize_transactions(transactions, period_days=7, now=now)

        self.assertEqual(totals, {
            "money_in": 105.0,
            "money_out": 20.0,
            "fees": 1.0,
            "transaction_count": 3,
        })

    def test_dashboard_all_time_includes_the_full_history(self):
        transactions = [
            Transaction("Deposit", 100, timestamp="2025-01-10 09:00:00"),
            Transaction("Withdrawal", 20, fee=1, timestamp="2025-01-03 12:00:00"),
            Transaction("Transfer received", 5, timestamp="2025-01-07 11:00:00"),
            Transaction("Transfer sent", 10, timestamp="2025-01-02 12:00:00"),
        ]

        totals = summarize_transactions(transactions)

        self.assertEqual(totals, {
            "money_in": 105.0,
            "money_out": 30.0,
            "fees": 1.0,
            "transaction_count": 4,
        })


class AccountTests(unittest.TestCase):
    def test_deposit_and_personal_withdrawal(self):
        account = Account("Ama", "0240000000", hash_pin("0240000000", "1234"), 20)
        account.deposit(10)
        transaction = account.withdraw(5)
        self.assertEqual(account.balance, 25.0)
        self.assertEqual(transaction.fee, 0.0)
        self.assertEqual(len(account.transactions), 2)

    def test_merchant_fee_is_one_percent(self):
        account = MerchantAccount("Shop", "0200000000", "hash", 100)
        transaction = account.withdraw(50)
        self.assertEqual(transaction.fee, 0.5)
        self.assertEqual(account.balance, 49.5)

    def test_insufficient_funds_does_not_change_account(self):
        account = Account("Ama", "0240000000", "hash", 10)
        with self.assertRaises(InsufficientFundsError):
            account.withdraw(11)
        self.assertEqual(account.balance, 10.0)
        self.assertEqual(account.transactions, [])

    def test_transfer_records_both_sides_with_shared_reference(self):
        sender = MerchantAccount("Shop", "0200000000", "hash", 100)
        recipient = Account("Ama", "0240000000", "hash", 5)
        sent = sender.transfer_to(recipient, 10, "MTN")
        received = recipient.transactions[0]
        self.assertEqual(sender.balance, 89.9)
        self.assertEqual(recipient.balance, 15.0)
        self.assertEqual(sent.reference, received.reference)
        self.assertEqual(sent.fee, 0.1)
        self.assertIn("via MTN", sent.details)
        self.assertIn("via MTN", received.details)

    def test_transfer_to_unregistered_phone_records_simulated_send(self):
        sender = Account("Demo User", "0240000000", "hash", 100)
        transaction = sender.transfer_to_phone("0551234567", 10, "Telecel")

        self.assertEqual(sender.balance, 90.0)
        self.assertEqual(len(sender.transactions), 1)
        self.assertEqual(transaction.kind, "Transfer sent")
        self.assertIn("0551234567", transaction.details)
        self.assertIn("via Telecel", transaction.details)
        self.assertIn("not registered", transaction.details)

    def test_invalid_amount_is_rejected(self):
        account = Account("Ama", "0240000000", "hash", 10)
        for amount in (0, -1, float("nan"), float("inf")):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    account.deposit(amount)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_directory = os.getcwd()
        os.chdir(self.temp_dir.name)
        self.store = WalletStore("test_wallet.json")

    def tearDown(self):
        os.chdir(self.original_directory)
        self.temp_dir.cleanup()

    def test_register_authenticate_and_reject_duplicate_phone(self):
        account = self.store.register("Ama", "0241234567", "0123", "Personal")
        self.assertIs(self.store.authenticate("0241234567", "0123"), account)
        self.assertIsNone(self.store.authenticate("0241234567", "9999"))
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.store.register("Another", "0241234567", "1234", "Merchant")

    def test_json_round_trip_and_statement_export(self):
        account = self.store.register("Ama", "0241234567", "0123", "Personal")
        account.deposit(25)
        self.store.save()
        restored = WalletStore("test_wallet.json")
        restored.load()
        loaded_account = restored.get_account("0241234567")
        self.assertEqual(loaded_account.balance, 25.0)
        filename = restored.export_statement(loaded_account)
        with open(filename, "r", encoding="utf-8") as file:
            statement = file.read()
        self.assertIn("Deposit", statement)
        self.assertIn("GH₵ 25.00", statement)


if __name__ == "__main__":
    unittest.main()