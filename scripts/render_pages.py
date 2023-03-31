# code to make a markdown page of a vulnerability

import os

if __name__ == "__main__":

    INDIR = '../vulnerabilities/2023/'
    OUTDIR = '../../piko/exampleSite/content/database/vulnerabilities/2023/'
    for i in range(1,29):
        filename = 'AVID-2023-V'+str(i).zfill(3)
        os.system('python3 render_single_page.py -i '+INDIR+filename+'.json'+' -o '+OUTDIR+filename+'.md -v True')

    INDIR = '../reports/2023/'
    OUTDIR = '../../piko/exampleSite/content/database/reports/2023/'
    for i in range(1,5):
        filename = 'AVID-2023-R'+str(i).zfill(4)
        os.system('python3 render_single_page.py -i '+INDIR+filename+'.json'+' -o '+OUTDIR+filename+'.md -r True -v True')