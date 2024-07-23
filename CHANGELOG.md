# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.13.0] - 2024-07-23

### Added
- Added extra filtering methods for ElementList
- Make sure tests and docs are not included in binary distribution wheels (PyPi) and source distribution (sdist).

## [0.12.0] - 2023-11-10

### Added
- Added support for opening password protected files ([#350](https://github.com/jstockwin/py-pdf-parser/pull/350))

## [0.11.0] - 2023-08-07

### Changed
- Various dependency updates
- PyPI releases now use Trusted Publishers

### Fixed
- Fixed typo in docs ([#361](https://github.com/jstockwin/py-pdf-parser/pull/361))

## [0.10.2] - 2022-11-07

### Changed
- Various dependency updates
- Removed unused PyYAML dependency ([#262](https://github.com/jstockwin/py-pdf-parser/pull/262))

## [0.10.1] - 2021-10-12
### Fixed
- The `visualise` function properly uses the _elements_ parameter in order to filter visualised elements. ([#256](https://github.com/jstockwin/py-pdf-parser/pull/256))

### Changed
- Various dependency updates

## [0.10.0] - 2021-07-01
- [BREAKING] Changes from using pyqt5 to using tkinter for the visualise tool. This
  means we don't need the python3-dev as a requirement, and seems to solve endless
  issues with pyqt5 not finding the correct qt bindings. This is a potential breaking
  change, although the visualise tool is only in the development version. No code
  changes are needed, but you will need tkinter installed for visualise to still work.
- Changed python version from 3.6 to 3.8 in `.readthedocs.yml`.

## [0.9.0] - 2021-06-09
### Changed
- Various dependency updates (matplotlib, pyqt5)
- Removed all but the tests dockerfile for simplicity. Use Docker BuildKit. We will no longer be pushing images to DockerHub on release. ([#203](https://github.com/jstockwin/py-pdf-parser/pull/203))

## [0.8.0] - 2021-05-12
### Changed
- Various dependency updates
- Updated CI to avoid login issue ([#182](https://github.com/jstockwin/py-pdf-parser/pull/182))

## [0.7.0] - 2021-01-15
### Changed
- Ensure we only accept LTTextBoxes at the top level (not LTTextLines) ([#155](https://github.com/jstockwin/py-pdf-parser/pull/155))
## [0.6.0] - 2020-12-11
### Added
- Enabled dependabot which should help to keep packages up to date ([#124](https://github.com/jstockwin/py-pdf-parser/pull/124))

### Changed
- Various dependency updates

### Fixed
- Fixed a typo in simple memo example in the documentation. ([#121](https://github.com/jstockwin/py-pdf-parser/pull/121))

## [0.5.0] - 2020-07-05
### Added
- New functions on `ElementList`, `move_forwards_from` and `move_backwards_from`, to allow moving forwards and backwards from a certain element in the list easily. ([#113](https://github.com/jstockwin/py-pdf-parser/pull/113))

### Changed
- When the layout parameter all_texts is True, the text inside figures is now also returned as elements in the document. ([#99](https://github.com/jstockwin/py-pdf-parser/pull/99))

### Fixed
- Passing a tolerance less than the width/height of an element no longer causes an error. The tolerance is now capped at half the width/height of the element. ([#103](https://github.com/jstockwin/py-pdf-parser/pull/103))

## [0.4.0] - 2020-06-22
### Added
- Added `__len__` and `__repr__` functions to the Section class. ([#90](https://github.com/jstockwin/py-pdf-parser/pull/90))
- Added flag to `extract_simple_table` and `extract_table` functions to remove duplicate header rows. ([#89](https://github.com/jstockwin/py-pdf-parser/pull/89))
- You can now specify `element_ordering` when instantiating a PDFDocument. This defaults to the old behaviour or left to right, top to bottom. ([#95](https://github.com/jstockwin/py-pdf-parser/pull/95))

### Changed
- Advanced layout analysis is now disabled by default. ([#88](https://github.com/jstockwin/py-pdf-parser/pull/88))

## [0.3.0] - 2020-05-14
### Added
- Published to PyPI as py-pdf-parser.
- Documentation is now hosted [here](https://py-pdf-parser.readthedocs.io/en/latest/). ([#71](https://github.com/jstockwin/py-pdf-parser/pull/71))
- Added new examples to the documentation. ([#74](https://github.com/jstockwin/py-pdf-parser/pull/74))
- Font filtering now caches the elements by font. ([#73](https://github.com/jstockwin/py-pdf-parser/pull/73)) (updated in [#78](https://github.com/jstockwin/py-pdf-parser/pull/78))
- Font filtering now caches the elements by font. ([#73](https://github.com/jstockwin/py-pdf-parser/pull/73))
- The visualise tool now draws an outline around each section on the page. ([#69](https://github.com/jstockwin/py-pdf-parser/pull/69)) (updated in [#80](https://github.com/jstockwin/py-pdf-parser/pull/80))


### Changed
- This product is now complete enough for the needs of Optimor Ltd, however `jstockwin` is going to continue development as a personal project. The repository has been moved from `optimor/py-pdf-parser` to `jstockwin/py-pdf-parser`.

## [0.2.0] - 2020-04-17
### Added
- It is now possible to specify `font_size_precision` when instantiating a PDFDocument. This is the number of decimal places the font size will be rounded to. ([#60](https://github.com/jstockwin/py-pdf-parser/pull/60))
- `extract_simple_table` now allows extracting tables with gaps, provided there is at least one full row and one full column. This is only the case if you pass `allow_gaps=True`, otherwise the original logic of raising an exception if there a gap remains. You can optionally pass a `reference_element` which must be in both a full row and a full column, this defaults to the first (top-left) element. ([#57](https://github.com/jstockwin/py-pdf-parser/pull/57))

### Changed
- Font sizes are now `float` not `int`. The `font_size_precision` in the additions defaults to 1, and as such all fonts will change to have a single decimal place. To keep the old behaviour, you can pass `font_size_precision=0` when instantiating your PDFDocument.

### Fixed
- Improved performance of `extract_simple_table`, which is now much faster. ([#65](https://github.com/jstockwin/py-pdf-parser/pull/65))

## [0.1.0] - 2020-04-08
### Added
- Initial version of the product. Note: The version is less than 1, so this product should not yet be considered stable. API changes and other breaking changes are possible, if not likely.
