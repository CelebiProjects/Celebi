"""
Created by Mingrui Zhao @ 2017
define some classes and functions used throughout the project

Note: This module now re-exports color functions from color_utils.
"""
# Load module
from .color_utils import colorize, color_print

# Re-export the functions
__all__ = ['colorize', 'color_print']
