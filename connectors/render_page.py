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
    header = ['## Reports \n\n', '| ID | Class | Name |\n']
    divider = ['| --- | --- | --- | \n']
    content = [
        '| '+rep['report_id']+' | '+rep['class']+' | '+rep['name']+' |\n'
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
        '- **SEP view:** '+(', '.join([sep['id']+': '+sep['name'] for sep in taxo['sep_view']]))+'\n',
        '- **Lifecycle view:** '+(', '.join([lc['id']+': '+lc['stage'] for lc in taxo['lifecycle_view']]))+'\n'
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
    for art in aff['artifact']:
        content.append('| '+art['type']+' | '+art['name']+' |\n')
        
    return header+content+['\n']

def renderInfo(vuln, is_report=False):
    header = ['## Other information\n\n']

    if is_report:
        content = [
            '- **Report Type:** '+vuln['problemtype']['type']+'\n',
            '- **Credits:** '+('; '.join([cred['value'] for cred in vuln['credit']]))+'\n',
            '- **Date Reported:** '+vuln['reported_date']+'\n',
            '- **Version:** '+vuln['data_version']+'\n'
        ]        
    else:
        content = [
            '- **Vulnerability Class:** '+vuln['problemtype']['class']+'\n',
            '- **Credits:** '+('; '.join([cred['value'] for cred in vuln['credit']]))+'\n',
            '- **Date Published:** '+vuln['published_date']+'\n',
            '- **Date Last Modified:** '+vuln['last_modified_date']+'\n',
            '- **Version:** '+vuln['data_version']+'\n'
        ]
    return header+content+['\n']