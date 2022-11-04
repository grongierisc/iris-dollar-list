# Change Log


## [0.9.5] 04-Nov-2022

### Added

- Added support of __init__ in DollarList
  - Can now create a DollarList from a list, bytes, string, or another DollarList
- Added support of float in DollarList

### Fixed

- Fixed to_string() in DollarList
  - Now returns $lb("") instead of $lb()

## [0.9.4] 03-Nov-2022

### Added

- Dunder methods for DollarList
  - getitem
  - setitem
  - add
  - contains
  - eq
  - ne
  - sizeof
  - hash

### Fixed

- refactored from_string

## [0.9.3] 03-Nov-2022

### Added

- Support of from_string method in DollarList

## [0.9.2] 28-Oct-2022

### Added

- Added CHANGELOG.md
- Support of from_list and to_list methods

## [0.9.1] 27-Oct-2022

### Added

- Support of from_bytes and to_bytes methods for DollarList and DollarItem

## [0.9.0] 23-Oct-2022

### Added

- Initial release