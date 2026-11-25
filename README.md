# MoMo Wallet — Lab 3

A class-based desktop mobile-money wallet simulator made with Python's standard library. This is a learning project and a simulated sandbox: it does **not** connect to a bank, MTN, Telecel, AT, or any real payment gateway, and no real money moves.

## Contents

- [Start the app](#start-the-app)
- [Demo accounts](#demo-accounts)
- [Features and how to try them](#features-and-how-to-try-them)
- [Project files](#project-files)
- [How the app is organized](#how-the-app-is-organized)
- [Learning notes](#learning-notes)
- [Run the tests](#run-the-tests)
- [Troubleshooting](#troubleshooting)
- [Safety and simulation limits](#safety-and-simulation-limits)

## Start the app

Open PowerShell or a terminal in the project folder, then run:

```powershell
python main.py
```

The project needs Python with Tkinter available. It uses Python's standard library, so no third-party packages or `pip install` step are required. On the first launch, the app creates `wallet_data.json` in the current working directory and seeds the two demo accounts below. Later launches load the accounts and transaction history from that JSON file.

## Demo accounts

| Account | Phone | PIN | Starting balance |
| --- | --- | --- | ---: |
| Personal — Ama Mensah | `0240000000` | `1234` | GH₵ 500.00 |
| Merchant — Kojo's Store | `0200000000` | `4321` | GH₵ 1,250.00 |

Use the **Create account** option to register another Personal or Merchant wallet. New wallets start at GH₵ 0.00. Phone numbers must contain 10–15 digits and be unique; a PIN must contain exactly four digits.

## Features and how to try them

### Login and registration

- The app opens at a login/register gate; wallet balances and actions are not displayed before login.
- Log in using a phone number and PIN. A wrong pair produces a friendly error instead of terminating the app.
- Register with a name, phone number, four-digit PIN, and Personal or Merchant account type. Duplicate phone numbers are rejected.
- PINs are stored as SHA-256 hashes rather than readable PIN text. The demo credentials above are intentionally public so the lab can be tried immediately.

### Wallet actions

- **Show balance** reveals the balance; it is masked by default and can be hidden again with the eye control.
- Enter an amount or use the GH₵ 10, GH₵ 50, or GH₵ 100 quick-amount buttons.
- **Deposit** adds a valid positive amount, saves the wallet, and confirms the amount deposited.
- **Cash out** withdraws an amount, applies the account's fee rule, saves the wallet, and reports that the cash-out is allowed in this simulation.
- Amounts must be valid, finite, and greater than zero. An attempted withdrawal or transfer that exceeds available funds is rejected without changing the balance.
- Success and error messages are shown in popups. Amount and transfer-recipient inputs are cleared after successful actions; PINs and other sensitive form values are cleared when leaving a screen.

### Send money and choose a network

- Enter a recipient phone number and choose MTN, Telecel, or AT. The provider selection is stored in the simulated transaction details only; it does not route a real payment.
- If the phone belongs to an account in this app, that account receives the amount and a matching **Transfer received** history entry. The sender's fee, if any, is deducted from the sender only.
- If the phone is not registered in this app, the app still records a simulated send for any valid 10–15 digit phone number. It clearly explains that the recipient's in-app wallet cannot be updated and no real transfer occurred.
- A sender cannot send to their own phone. A successful transfer shows the recipient, amount, provider, and new balance (or says the balance is hidden if privacy mode is on).
- Each transaction has a short reference and a status. Transfers between registered accounts share one reference and timestamp on both sides.

### Dashboard tab

Choose **Wallet dashboard** to view the dashboard separately from **Wallet actions**. The dashboard summarizes the signed-in account's own history for the last 7 days, last 30 days, or all time:

- Money in: deposits and transfers received.
- Money out: withdrawals and transfers sent.
- Fees and transaction count.
- A built-in Tkinter Canvas bar chart comparing money in with money out.

For recent-period reports, transactions with malformed, too-old, or future timestamps are excluded. The all-time view includes the complete stored transaction history.

### History, receipts, and statement export

- Transaction history starts collapsed. Click **Show transaction history** to reveal it and click again to hide it.
- Rows show date/time, transaction type, amount, fee, reference, and details; newest transactions appear first.
- Select a row and click **View receipt**, or double-click the row, to open a receipt popup. The receipt includes the transaction's status and reference.
- Click **Export .txt** to write a readable `statement_<phone>.txt` file in the app's current working directory. It includes the account summary and transactions using the model classes' string representations.

### Lock and switch accounts

Click **Lock / switch account** to return to the login screen, clear the active account from the interface, and clear sensitive PIN, amount, and recipient inputs. Log in again to access another wallet.

### Visual design

The Tkinter interface uses an MTN-inspired yellow-and-dark palette, white content cards, and a visible **SIMULATED SANDBOX** badge. The colors are visual styling only and do not indicate a connection with MTN.

## Project files

| File | Responsibility | Start here when… |
| --- | --- | --- |
| `main.py` | Application entry point; creates `WalletApp` and starts Tkinter's event loop. | The program does not launch. |
| `gui.py` | Login/registration, tabs, styling, wallet actions, dashboard display, history, receipts, exports, and user-facing messages. | A screen, button, popup, or GUI flow is wrong. |
| `models.py` | `InsufficientFundsError`, PIN/amount validation, `Transaction`, `Account`, `MerchantAccount`, balances, transfers, and fees. | A balance, fee, transfer, or transaction record is wrong. |
| `storage.py` | `WalletStore`, JSON load/save, demo account creation, registration, authentication, and text statement export. | Login, registration, saved data, or statement output is wrong. |
| `analytics.py` | Period selection and calculations for dashboard totals. | A dashboard total or date range is wrong. |
| `test_wallet.py` | Standard-library unit tests for analytics, wallet rules, registration, authentication, persistence, and statements. | You want to understand or verify the expected behavior. |
| `wallet_data.json` | Local saved wallet accounts and transaction histories; created on first app launch. | You are inspecting the simulator's saved data. Back it up before manual changes. |
| `statement_<phone>.txt` | Readable mini statement generated when the export button is used. | You are looking for an exported statement. |

### Key methods to explore

| Behavior | Code location | What to notice |
| --- | --- | --- |
| Open the application | `main.py` → `main()` | `WalletApp` is created and Tkinter's event loop starts. |
| Load or create saved wallets | `storage.py` → `WalletStore.load()` | Existing JSON is validated; demo wallets are created only when the file is missing. |
| Log in and create a wallet | `gui.py` → `WalletApp._login()` / `WalletApp._register_account()`; `storage.py` → `WalletStore.authenticate()` / `WalletStore.register()` | The GUI gathers input; the store performs account lookup, validation, and registration. |
| Change a wallet balance | `gui.py` → `WalletApp._perform()`; `models.py` → `Account.deposit()`, `Account.withdraw()`, or `Account.transfer_to()` | The GUI chooses the action, while account methods enforce money rules and record transactions. |
| Apply merchant charges | `models.py` → `MerchantAccount.fee_for()` | The overridden method supplies the 1% fee to the shared withdrawal and transfer behavior. |
| Record a send to an unregistered number | `models.py` → `Account.transfer_to_phone()` | The sender gets a transaction record, but there is no receiver wallet to update. |
| Refresh the dashboard | `gui.py` → `WalletApp._refresh_dashboard()` / `WalletApp._draw_dashboard_chart()`; `analytics.py` → `summarize_transactions()` | Totals are calculated separately from their visual presentation. |
| Show a receipt or export a statement | `gui.py` → `WalletApp._show_receipt()` / `WalletApp._export_statement()`; `storage.py` → `WalletStore.export_statement()` | Receipts use a transaction's string form; export writes the account and transaction history to text. |
| Save account data | `storage.py` → `WalletStore.save()` | Each account and its transaction objects are converted to JSON-compatible dictionaries. |

## How the app is organized

The main flow is:

1. `main.py` creates the `WalletApp` window from `gui.py`.
2. `WalletApp` creates a `WalletStore` and loads saved account data. If there is no data file yet, `WalletStore` creates the demo accounts and saves them.
3. The login/register gate uses `WalletStore.authenticate` or `WalletStore.register`. Once authenticated, the GUI displays the active account's actions, dashboard, and history.
4. The GUI delegates wallet rules to `Account` methods and refreshes the UI after the action. It then asks `WalletStore` to persist the updated data.
5. `analytics.py` reads the active account's transaction objects to calculate dashboard totals; it does not own or modify wallet balances.

Keeping these responsibilities separate makes it easier to find problems: interface behavior is in `gui.py`, money rules are in `models.py`, and file operations are in `storage.py`.

## Learning notes

- **Classes and objects:** each `Account` object holds one wallet's name, phone, PIN hash, balance, and transaction list. Methods such as `deposit`, `withdraw`, and `transfer_to` keep related balance changes and history records together.
- **Inheritance:** `MerchantAccount` inherits from `Account`, including its initializer, and overrides `fee_for` to charge 1% on merchant withdrawals and outgoing transfers. Personal accounts have no fee. Shared account methods call `fee_for`, demonstrating polymorphism without duplicating the transaction logic.
- **Exceptions and validation:** invalid amounts and insufficient funds are reported through `ValueError` and `InsufficientFundsError`; the GUI catches these and shows helpful popups. Failed money actions do not append a transaction or change balances.
- **Transaction objects:** each `Transaction` records its kind, amount, fee, details, timestamp, short reference, and status. `to_dict`/`from_dict` convert it to and from JSON-compatible records; `__str__` supplies readable receipt and statement content.
- **Persistence boundary:** `WalletStore` is responsible for JSON and account lookup. The GUI does not write JSON itself. If saved JSON is unreadable or malformed, the app reports a wallet-data error rather than silently replacing it.
- **Dashboard aggregation:** `summarize_transactions` calculates money in/out, fees, and count separately from Tkinter. Keeping this calculation in `analytics.py` makes it possible to test without opening a window.
- **Standard-library UI:** `ttk.Notebook` provides separate action and dashboard tabs, `ttk.Treeview` displays history, and `tkinter.Canvas` draws the chart.

## Run the tests

From the project folder, run:

```powershell
python -m unittest -v
```

The tests cover 7-day and all-time dashboard summaries, deposits and withdrawals, the merchant fee, insufficient funds, registered and unregistered transfers, invalid amounts, PIN authentication, duplicate registration, JSON save/load, and statement contents. The suite does not require opening the GUI.

To check that the Python files compile, run:

```powershell
python -m py_compile main.py gui.py models.py storage.py analytics.py test_wallet.py
```

## Troubleshooting

- **The app does not open:** run `python main.py` from this project folder and check that your Python installation includes Tkinter. Start at `main.py`, then check import or window errors in `gui.py`.
- **Login is rejected:** use the exact demo phone/PIN pair listed above, or check that you are using the same `wallet_data.json` file as the previous run. Registering a new account creates a different wallet; it does not change the demo PINs.
- **Registration fails:** confirm the name is not empty, the phone is 10–15 digits and not already registered, and the PIN is exactly four digits. Registration and authentication are in `storage.py`; their form and messages are in `gui.py`.
- **A transaction is rejected:** enter a positive numeric amount. Withdrawals and transfers must cover both the amount and any fee. The validation and balance checks are in `models.py`.
- **A recipient does not get an in-app balance update:** only numbers registered in this app have an in-app wallet to update. Sends to other valid numbers are recorded as simulations only; they are not delivered to a person or provider.
- **Saved-data error on startup:** `wallet_data.json` may be unreadable or invalid. Make a backup before inspecting or repairing it; startup intentionally avoids silently overwriting a file that cannot be loaded. JSON loading and validation are in `storage.py`.
- **Statement export fails or you cannot find the file:** check write permissions and look in the directory from which you launched the app. The filename is `statement_<phone>.txt`; the export handler is in `gui.py` and file writing is in `storage.py`.
- **Dashboard numbers look unexpected:** check the selected period, transaction timestamps, and transaction kinds. Start with `analytics.py`; the dashboard controls and chart are in `gui.py`.
- **A change breaks behavior:** run the unit tests above and begin with the test class related to that feature in `test_wallet.py`.

## Safety and simulation limits

This program is an educational demonstration, not a financial product. Network names, references, success statuses, deposits, cash-outs, and transfers are simulated locally. No payment provider is contacted, and no real money is deposited, withdrawn, or sent.

SHA-256 is used here to satisfy the lab's built-in-library learning requirement; it is a fast hash and is not sufficient PIN/password storage for a real service. The wallet JSON file contains balances, account details, transaction histories, and PIN hashes, so treat it as demo data and do not use real credentials or financial information. A production financial application would require professionally reviewed authentication, secure storage, authorization, auditing, and integration with regulated payment services.