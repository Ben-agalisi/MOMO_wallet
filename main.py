"""Start the class-based MoMo wallet desktop app."""

from gui import WalletApp


def main():
    """Create the application window and run Tkinter's event loop."""
    app = WalletApp()
    app.mainloop()


if __name__ == "__main__":
    main()
