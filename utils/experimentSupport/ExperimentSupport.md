# Experiment Support

The tools in this directory offer ways of communicating with Pyneal to obtain results during a real-time scan. 

They can be used as is, or -- more likely -- modified to fit your particular experiemental needs. 



## Matlab

* `getFromPyneal.m` : Matlab tool to request results from the Pyneal Results Server during a real-time scan. Requires `jsonlab` library added to Matlab path in order to parse results and return a structure. 