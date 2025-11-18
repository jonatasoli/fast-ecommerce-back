# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This project uses [*towncrier*](https://towncrier.readthedocs.io/) and the changes for the upcoming release can be found in <https://github.com/twisted/my-project/tree/main/changelog.d/>.

<!-- towncrier release notes start -->

## [0.4.0](https://github.com/twisted/my-project/tree/0.4.0) - 2025-11-18

### Added

- Create cielo client skeleton ([#1178](https://github.com/twisted/my-project/issues/1178))
- Criar uma task para atualizar pagamentos perdidos. ([#1180](https://github.com/twisted/my-project/issues/1180))
- Add changelog
- Criar uma task para atualizar os pedidos.

### Changed

- Remove deprecated lifespan in app initialization

### Fixed

- Ajuste no fluxo de pagamento do stripe
- Fix integration test use postgres 17
- Fixed error to show commissions

### Build

- Update dependencies in api project. ([#1177](https://github.com/twisted/my-project/issues/1177))
- Ajustada a configuração do docker para rodar no mono repo
