import json

# converts airtable record to report and saves
def save_as_report(record, save_location):
    
    report = {}
    report['data_type'] = 'AVID'
    report['version'] = ''
    report['metadata'] = {
        'report_id' : ''
    }
    report['affects'] = {
        'developer': record['fields']['Developer of Artifact'],
        'deployer': record['fields']['Deployer of Artifact'],
        'artifact': [
            {
                'type': record['fields']['Artifact Type'],
                'name': record['fields']['Artifact Name']
            }
        ]
    }
    report['problemtype'] = {
        'class': '',
        'type': record['fields']['Report Type'].split(':')[0],
        'description': {
            'lang': 'eng',
            'value': record['fields']['Title']
        }
    }
    report['metrics'] = []
    report['references'] = record['fields']['References']
    report['description'] = {
        'lang': 'eng',
        'value': record['fields']['Description']
    }
    report['impact'] = {
        'avid': {
            'vuln_id': '',
            'risk_domain': record['fields']['Relevant SEP risk domains'],
            'sep_view': record['fields']['Relevant Ethics subcategories'],
            'lifecycle_view': record['fields']['Relevant stages of the AI lifecycle']
        }
    }
    report['credits'] = [
        {
            'lang': 'eng',
            'value': record['fields']['Submitter Name'] + ', ' + record['fields']['Submitter Organization']
        }
    ]
    report['reported_date'] = record['createdTime'].split('T')[0]
    
    # save report
    output = open(save_location+record['id']+'.json', 'w')
    json.dump(report, output, indent=4)
    output.close()