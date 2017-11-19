**Custom Analysis:**
Build your own custom analysis routines that will be executed on every volume throughout a real-time scan. 

Use custom_template.py as a template for building your own analyses algorithms. Scripts must be written in python and should expect as input a single 3D array representing the 3D volume for a single TR. Set the output to return a single value. 

Store custom analysis scripts in <pyneal dir>/utils/custom_analysis/analysis_scripts

