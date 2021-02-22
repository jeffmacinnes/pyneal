# Change Log

## [v1.0.1] - 2021-02-19

### Added

### Changed

- all instances of 'scannerBaseDir' have been changed to 'scannerSessionDir', and users must specify the path to this directory in the scannerConfig.yaml file. This makes the paths on pyneal scanner simpler and more consistent across all 3 scanner manufacturers, whereas before GE had been automatically trying to assign the session dir by finding the most recently updated the p###/e### directories.

### Fixed

- updated deprecated `yaml.load(input)` to `yaml.load(input, Loader=yaml.FullLoader)` throughout
