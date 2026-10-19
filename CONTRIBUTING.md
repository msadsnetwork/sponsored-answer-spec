# Contributing
Thanks for helping shape this draft.

- **Discuss first:** open an Issue for field changes. Use the labels `spec`, `schema`, `privacy`, `disclosure` or `compat`.
- **Pull requests:** if you change the spec, also update `schema/` and the examples, and add or adjust a test in `tests/test_spec.py`. `python3 tests/test_spec.py` must pass.
- **Compatibility:** changes within 0.x should be additive where possible. Breaking changes need an entry in CHANGELOG.md under "Breaking".
- **Privacy:** never add fields that carry raw chat text, device IP/IFA, precise location or user identifiers.
- **Claims:** examples must use fictional brands and no unverifiable superlatives.
- **Licensing:** by contributing you agree that spec text is licensed under CC BY 4.0 and code under Apache-2.0.
- **Code of conduct:** be respectful. Maintainers may moderate.
