# Changelog

<< [Home](../README.md) | [Installation Guide](INSTALL.md) | [Troubleshooting](TROUBLESHOOTING.md) | [Status Monitor](MBVIEWER.md) | [Robustness](ROBUSTNESS.md) | [Updating](UPDATING.md) | **Changelog** | [Code of Conduct](CODE_OF_CONDUCT.md)

---

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - (Unreleased)

### Changed

- Refactored GPIO control to exclusively use `libgpiod` for simplicity and to remove the `pigpio` dependency. LED control is now simple on/off, not PWM.

### Added

- Initial project structure.
- Core UDP Bridge and MQTT Gateway functionality.
- Status LED support via `pigpio`.
- `systemd` service file for headless operation.
- Comprehensive unit test suite and modular documentation.
- Automated, cross-platform packaging script.
- Versioning support via `--version` argument and in package name.

[Unreleased]: https://github.com/your-username/your-repo/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/your-username/your-repo/releases/tag/v1.0.0
