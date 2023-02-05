# import all case studies from MITRE ATLAS

import logging
from avidtools.connectors.atlas import *

SAVE_LOCATION = '../reports/review/'

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)
    logging.info('Saving reports to '+SAVE_LOCATION)
    
    for i in range(16):
        cs_id = 'AML.CS'+str(i).zfill(4)
        logging.info('Processing case study '+cs_id)
        cs = import_case_study(cs_id)
        report = convert_case_study(cs)

        report.save(SAVE_LOCATION+cs_id+'.json')