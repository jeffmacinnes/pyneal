![Pyneal Logo](resources/images/pyneal_logo.jpg)

# Pyneal -- real-time fMRI Analysis Software

*NOTE:* **Currently On Development Branch** Currently undergoing major overhaul to the codebase to make it more generalizable across different scanning environments. If you want to download the latest stable version of Pyneal (built for the scanning environment at Duke University), switch to the **master** branch (or click [here](https://github.com/jeffmacinnes/pyneal/tree/master))

## Structure
There are two main components to this software:

* **pyneal_scanner**: This contains all of the code and tools for accessing data from the scanner and *sending* individual slice data to the real-time analysis stage. All of the relevant code for this component is to be found in the `pyneal_scanner` directory.

* **pyneal**: This is component that *receives* incoming slice data from **pyneal_scanner**, builds a 4D dataset overtime, runs whatever analysis you have specified, and makes the results available to a presentation machine. This component can be launched from the root directory by calling `pyneal.py`. The relevant code for this component in found in the `src` directory.



#### Made possible through funding support by:

* **W.M. Keck Foundation**; *awarded to Andrea Stocco, PhD, Chantel Prat, PhD, & Rajesh Rao, PhD*

* **NIMH R01 MH094743**, **Alfred P. Sloan Fellowship**, **Klingenstein Fellowship Award in the Neurosciences**, 
**Dana Foundation Brain and Immuno-Imaging Program**; *awarded to R. Alison Adcock, MD, PhD*
