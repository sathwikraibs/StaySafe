# Contributing to TrustLight

Thank you for helping make TrustLight better. Every report helps protect someone from a scam.

## Ways to help

- **A wrong result.** TrustLight called a scam safe, or a real message risky. [Open an issue](https://github.com/sathwikraibs/StaySafe/issues) with the link or message (remove any personal details first: names, phone numbers, account numbers, OTPs).
- **A translation that reads wrong.** Hindi, Kannada and Tulu corrections from native speakers are very welcome. Open an issue with the page, the current text and your better wording.
- **A bug.** Open an issue: what you did, what you expected, what happened, and your phone or browser.
- **A security problem.** Please do **not** open a public issue. Follow [SECURITY.md](SECURITY.md).

## Changing the code

1. Fork the repository and make a branch.
2. Make your change. Keep the words on screen simple, short and friendly: many users are new to the internet.
3. Add or update a test for your change in `staysafe-full/backend/tests/`.
4. Run the tests:

       cd staysafe-full/backend
       python tests/run_all.py

5. If you changed any text the backend sends, add the same text with its Hindi, Kannada and Tulu translations to `staysafe-full/frontend/src/i18n/content-*.ts`.
6. Open a pull request explaining what you changed and why. The tests and a full website build run automatically on every pull request and must pass.

## Rules for the code

- Never put API keys, passwords or tokens in the code. They live only in the server's settings.
- Personal details in messages (phone numbers, account numbers, OTPs, email addresses) must never be sent to outside services; use `mask_personal` in `translator.py`.
- The verdict must stay explainable: every point added to a risk score needs a plain-language reason.

## Code of conduct

Be kind and respectful. Harassment of any kind is not accepted.
