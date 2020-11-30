# leanix-integration-importer
Script to import data from Excel via Integration-API

##Requirements 
You need to install the following python packages: 
import click

import json

import datetime

import requests

import sys

import pandas

##Execute 
You need to add a valid API-TOKEN in the access.json file. 

You can execute the script with the following command:

python3 leanix.py <filename>

After that you need to enter the name of the source system and hit Enter. 

The default value of the name of the source system is set to 'Archer'. 

##Configure
If a new source system is needed you need to add configuration at the following places: 

1. Add a new <source>Processor.json which holds the logic how to import data. 
2. Extend the dataMapping.json with the data of the new source system. 
3. Extend the createRun function in the leanix.py script for the new source. 
