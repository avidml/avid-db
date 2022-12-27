# code to make a markdown page of a vulnerability
# Example usage:
# python3 render_single_page.py -i AVID-2022-V001.py -o AVID-2022-V001.md -v True

import json
import argparse
import logging
import ast
import sys

# add location of rendering functions and load them
sys.path.append('../connectors')
from render_page import *

if __name__ == "__main__":

    # set logging config
    logging.basicConfig(level=logging.INFO)

    # parse inputs
    parser = argparse.ArgumentParser(description='Render vuln information into a markdown page.')
    parser.add_argument('-i', type=str, help='input json file')
    parser.add_argument('-o', type=str, help='output md file')
    parser.add_argument('-r', type=str, help='is this a report (default=on)', default='False')
    parser.add_argument('-v', type=str, help='logging on/off (default=on)', default='True')
    args = parser.parse_args()

    # load input json file
    if ast.literal_eval(args.v):
        logging.info("Rendering "+args.i+" into "+args.o)
    j = json.load(open(args.i))

    # render components
    is_report = ast.literal_eval(args.r)
    Header = renderHeader(j, is_report=is_report)
    Desc = renderDesc(j)
    References = renderReferences(j)
    Taxonomy = renderTaxonomy(j)
    Affected = renderAffected(j)
    Info = renderInfo(j, is_report=is_report)
    if is_report:
        Final = ''.join(Header+Desc+References+Taxonomy+Affected+Info)
    else:
        Report = renderReports(j)
        Final = ''.join(Header+Desc+Report+References+Taxonomy+Affected+Info)

    # put together everything and save
    out = open(args.o, "w")
    out.write(Final)
    out.close()