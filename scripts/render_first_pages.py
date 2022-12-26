# code to make a markdown page of a vulnerability

import os

if __name__ == "__main__":

    INDIR = '../vulnerabilities/2022/'
    OUTDIR = '../../piko/exampleSite/content/database/vulnerabilities/2022/'
    for i in range(1,14):
        filename = 'AVID-2022-V'+str(i).zfill(3)
        os.system('python3 render_single_page.py -i '+INDIR+filename+'.json'+' -o '+OUTDIR+filename+'.md -v True')

    INDIR = '../reports/2022/'
    OUTDIR = '../../piko/exampleSite/content/database/reports/2022/'
    for i in range(1,6):
        filename = 'AVID-2022-R'+str(i).zfill(4)
        os.system('python3 render_single_page.py -i '+INDIR+filename+'.json'+' -o '+OUTDIR+filename+'.md -r True -v True')