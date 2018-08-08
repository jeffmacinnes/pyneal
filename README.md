[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


![Pyneal Logo](src/images/logo.jpg)

# Pyneal -- real-time fMRI Analysis Software

**Pyneal** is an open source software package to support real-time functional magnetic resonance imaging (fMRI). It is entirely Python-based and depends exclusively on free, open source neuroimaging libraries.

It allows users to:

* access functional MRI data in real-time
* compute on-going analyses throughout a scan
* monitor data quality
* share analysis results with remote devices (e.g. send results to an experimental task presenting neurofeedback to participants)

![](src/images/overview.png)

It currently supports data formats used across 3 major MRI manufacturers: **GE**, **Siemens**, **Philips**.

In addition to allowing users to compute basic, ROI-based analyses during a scan, **Pyneal** also provides a simple framework for designing and writing customized analyses that can be computed across the whole brain volume at each timepoint.


## Documentation

Please see [**Pyneal Docs**](https://jeffmacinnes.github.io/pyneal-docs/) for full documentation of this package, including:

* Overview
* Installation/Setup
* Usage
* Customizing analyses
* Simulating fMRI environments for testing
* Troubleshooting


## License
Pyneal is licensed under an MIT license. See the [LICENSE](LICENSE.txt) file for additional details.


## Contributors
Please note that this project is released with a [Contributor Code of Conduct](CONDUCT.md). By contributing to this project you agree to abide by its terms.


## Acknowledgments
#### Made possible through funding support by:

* **W.M. Keck Foundation**; *awarded to Andrea Stocco, PhD, Chantel Prat, PhD, & Rajesh Rao, PhD*

* **NIMH R01 MH094743**, **Alfred P. Sloan Fellowship**, **Klingenstein Fellowship Award in the Neurosciences**,
**Dana Foundation Brain and Immuno-Imaging Program**; *awarded to R. Alison Adcock, MD, PhD*
