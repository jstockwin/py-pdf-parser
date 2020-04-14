# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- `extract_simple_table` now allows extracting tables with gaps, provided there is at least one full row and one full column. This is only the case if you pass `allow_gaps=True`, otherwise the original logic of raising an exception if there a gap remains. You can optionally pass a `reference_element` which must be in both a full row and a full column, this defaults to the first (top-left) element. ([#57](https://github.com/optimor/py-pdf-parser/pull/57))

## [0.1.0] - 2019-04-08
### Added
- Initial version of the product. Note: The version is less than 1, so this product should not yet be considered stable. API changes and other breaking changes are possible, if not likely.
