# code to make a markdown page of a vulnerability

# Functions to render different parts of the page
def renderHeader(vuln, is_report=False):

    if is_report:
        id = vuln['metadata']['report_id']
    else:
        id = vuln['metadata']['vuln_id']
    return [
        '---\n',
        'title: '+id+'\n',
        'layout: page\n',
        'url: /database/'+id+'\n',
        '---\n\n'
    ]

def renderDesc(vuln):
    return [
        "## Description\n\n",
        vuln['problemtype']['description']['value']+'\n\n',
        "## Details\n\n",
        vuln['description']['value']+'\n\n'
    ]

def renderReports(vuln):
    reports = vuln['reports']
    header = ['## Reports \n\n', '| ID | Type | Name |\n']
    divider = ['| --- | --- | --- | \n']
    # for rep in reports:
    #     print(rep['report_id'])
    content = [
        '| ['+rep['report_id']+'](../'+rep['report_id']+') | '+rep['type']+' | '+rep['name']+' |\n'
        for rep in reports
    ]
    return header+divider+content+['\n']

def renderReferences(vuln):
    refs = vuln['references']
    header = ['## References\n\n']
    content = [
        '- ['+ref['label']+']('+ref['url']+')\n'
        for ref in refs
    ]
    return header+content+['\n']

def renderTaxonomy(vuln):
    taxo = vuln['impact']['avid']
    header = ['## AVID Taxonomy Categorization\n\n']
    content = [
        '- **Risk domains:** '+(', '.join(taxo['risk_domain']))+'\n',
        '- **SEP subcategories:** '+('; '.join(taxo['sep_view']))+'\n',
        '- **Lifecycle stages:** '+(', '.join(taxo['lifecycle_view']))+'\n'
    ]
    return header+content+['\n']

def renderAffected(vuln):
    aff = vuln['affects']
    header = ['## Affected or Relevant Artifacts\n\n']
    content = [
        '- **Developer:** '+(', '.join(aff['developer']))+'\n',
        '- **Deployer:** '+(', '.join(aff['deployer']))+'\n',
        '- **Artifact Details:**\n'+
        '| Type | Name |\n'+
        '| --- | --- | \n'
    ]
    for art in aff['artifacts']:
        content.append('| '+art['type']+' | '+art['name']+' |\n')
        
    return header+content+['\n']

def renderInfo(vuln, is_report=False):
    if is_report:
        id = vuln['metadata']['report_id']
    else:
        id = vuln['metadata']['vuln_id']
    yr = id.split('-')[1]
        
    header = ['## Other information\n\n']
    if is_report:
        content = [
            '- **Report Type:** '+vuln['problemtype']['type']+'\n',
            '- **Credits:** '+('; '.join([cred['value'] for cred in vuln['credit']]))+'\n',
            '- **Date Reported:** '+vuln['reported_date']+'\n',
            '- **Version:** '+vuln['data_version']+'\n',
            '- [AVID Entry](https://github.com/avidml/avid-db/tree/main/reports/'+yr+'/'+id+'.json)\n'
        ]        
    else:
        content = [
            '- **Vulnerability Class:** '+vuln['problemtype']['classof']+'\n'
        ]
        if vuln['credit'] is not None:
            content += ['- **Credits:** '+('; '.join([cred['value'] for cred in vuln['credit']]))+'\n']
        content += [
            '- **Date Published:** '+vuln['published_date']+'\n',
            '- **Date Last Modified:** '+vuln['last_modified_date']+'\n',
            '- **Version:** '+vuln['data_version']+'\n',
            '- [AVID Entry](https://github.com/avidml/avid-db/tree/main/vulnerabilities/'+yr+'/'+id+'.json)\n'
        ]
    return header+content+['\n']