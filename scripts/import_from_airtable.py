import pyairtable
import os
from dotenv import load_dotenv
import json
import logging
import sys

# add location of rendering functions and load them
sys.path.append('../connectors')
from airtable import *

# load environment and config
load_dotenv()
config = json.load(open('../config.json'))

if __name__ == "__main__":
    
    # set logging config
    logging.basicConfig(level=logging.INFO)
    
    # fetch data from airtable
    logging.info('Fetching data from Airtable')
    all_records = pyairtable.Table(
        os.getenv('AIRTABLE_API_KEY'), 
        config['airtable']['base_id'], 
        config['airtable']['table_name']
    ).all()

    for record in all_records:
        logging.info('Converting and saving record '+record['id'])
        
        # fill essential empty entries
        record_keys = list(record['fields'].keys())
        strings = ['Submitter Organization'] + ['Relevant '+s+' subcategories' for s in ['Security','Ethics','Performance']]
        for st in strings:
            if record_keys.count(st)==0:
                record['fields'][st] = ''
        
        save_as_report(
            record = record,
            save_location = '../reports/dev/'
        )
    