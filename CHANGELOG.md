# Change Log
## [v1.0.4] - 2021-04-26

### Added

### Changed

- updated `requirements.txt` and `pyneal_scanner/requirements.txt` to match the latest development environment

### Fixed


## [v1.0.3] - 2021-04-18

### Added

### Changed

- changed `yaml.load(input, Loader=yaml.FullLoader)` to `yaml.safe_load(input)` throughout. This was done to keep up with Yaml's ever changing recommendations for avoiding security issues with `load` (https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input)-Deprecation)

### Fixed

## [v1.0.2] - 2021-02-22

### Added

### Changed

### Fixed

- removed obsolete `receivedImg.nii.gz` from `pyneal_scanner/simulations/`

## [v1.0.1] - 2021-02-19

### Added

### Changed

- all instances of 'scannerBaseDir' have been changed to 'scannerSessionDir', and users must specify the path to this directory in the scannerConfig.yaml file. This makes the paths on pyneal scanner simpler and more consistent across all 3 scanner manufacturers, whereas before GE had been automatically trying to assign the session dir by finding the most recently updated the p###/e### directories.

### Fixed

- updated deprecated `yaml.load(input)` to `yaml.load(input, Loader=yaml.FullLoader)` throughout
