#!/usr/bin/env python

# Main file of devkit for the stereo task of the Robust Vision Challenge 2018.

from benchmark import *
from benchmark_cityscapes import *
from benchmark_kitti2015 import *
from benchmark_wilddash import *
from dataset_format import *
from dataset_format_kitti2015 import *
from devkit import *


if __name__ == '__main__':
    # Define the list of benchmarks supported by this script (in the order in
    # which they are listed on http://www.robustvision.net/index.php).
    benchmarks = [KITTI2015(), WildDash(), Cityscapes()]
    
    # Define the list of dataset formats which are supported.
    dataset_formats = [KITTI2015Format()]
    
    # Call the generic devkit main function.
    DevkitMain('instance', benchmarks, dataset_formats)
