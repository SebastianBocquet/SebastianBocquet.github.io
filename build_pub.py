import sys
import requests
from scholarly import scholarly

top_tier_bibcodes = ['2021MNRAS.504.1253G', '2020MNRAS.498..771G', '2019MNRAS.488.2041G',
                     '2018MNRAS.478.3072C', '2018MNRAS.474.2635S', '2016MNRAS.455..258C',]

ads_prefix = "https://ui.adsabs.harvard.edu/abs/"
ads_suffix = "/abstract"
doi_prefix = "https://doi.org/"

def main(ads_token):
    overview_content = []

    # ADS
    who = "author%3A\"bocquet%2Cs\"%20database%3Aastronomy"
    fl = "fl=author,bibcode,bibstem,citation_count,date,doi,identifier,page,title,volume,year"
    sort = "sort=date%20desc%2C%20bibcode%20desc"
    req = "https://api.adsabs.harvard.edu/v1/search/query?q=%s&&%s&%s&rows=1000"%(who, sort, fl)
    r = requests.get(req,
                 headers={'Authorization': 'Bearer '+ads_token})
    ads_papers = r.json()['response']['docs']
    # Somehow strangely, some papers don't have the citation_count key
    for paper in ads_papers:
        if 'citation_count' not in paper.keys():
            paper['citation_count'] = 0
    # Metrics
    sorted_citation_count = sorted([paper['citation_count'] for paper in ads_papers])[::-1]
    citations = sum(sorted_citation_count)
    hindex = 0
    while sorted_citation_count[hindex]>=hindex:
        hindex+= 1
    hindex-= 1
    refereed = 0
    peer_rev_j = ['AJ', 'ApJ', 'ApJS', 'A&A', 'JOSS', 'MNRAS', 'PhRvD', 'PhRvL']
    for paper in ads_papers:
        if paper['bibstem'][0] in peer_rev_j:
            refereed+= 1

    # Publication list
    top_tier_list, other_pub_list = [], []
    for p,paper in enumerate(ads_papers):
        # Skip proposals, zenodo, VizieR
        if paper['bibstem'][0] in ['ascl', 'hst', 'MPEC', 'sptz', 'yCat', 'zndo']:
            continue
        # First-author
        if 'Bocquet' in paper['author'][0]:
            if len(paper['author'])==2:
                a = ' & '.join([paper['author'][i].split(',')[0] for i in range(2)])
            else:
                a = ', '.join([paper['author'][i].split(',')[0] for i in range(3)])+' et al.'
            top_tier = True
        # Top-tier
        elif ('Bocquet' in paper['author'][1])|('Bocquet' in paper['author'][2])|(paper['bibcode'] in top_tier_bibcodes):
            for aa,a in enumerate(paper['author'][:5]):
                if 'Bocquet' in a:
                    # Want minimum of three authors listed
                    if aa==1:
                        a = ', '.join([paper['author'][i].split(',')[0] for i in range(aa+2)])+' et al.'
                    else:
                        a = ', '.join([paper['author'][i].split(',')[0] for i in range(aa+1)])+' et al.'
                    top_tier = True
                    break
        # Other
        else:
            if paper['bibcode']=='2021arXiv210104984G':
                continue
            a = paper['author'][0].split(',')[0]+' et al.'
            top_tier = False

        author_year_title = "<li>%s (%s), <em>%s</em>, "%(a, paper['year'], paper['title'][0])
        if 'volume' in paper.keys():
            ref = "%s, %s, %s"%(paper['bibstem'][0], paper['volume'], paper['page'][0])
        else:
            ref = "%s"%paper['bibstem'][0]
        if 'doi' in paper.keys():
            doi = ", DOI:<a href='%s%s'>%s</a> "%(doi_prefix, paper['doi'][0], paper['doi'][0])
        else:
            doi = " "
        ads_link = "(<a href='%s%s%s'>ADS abstract</a>)"%(ads_prefix, paper['bibcode'], ads_suffix)
        this = author_year_title+ref+doi+ads_link+"</li>\n"

        if top_tier==True:
            top_tier_list.append(this)
        else:
            other_pub_list.append(this)


    # Google scholar
    search_query = scholarly.search_author('Sebastian Bocquet')
    author = scholarly.fill(next(search_query), sections=['indices',])


    with open('pub_blank.html', 'r') as f:
        lines = f.readlines()
    out_lines = []
    for line in lines:
        if 'overview_content' in line:
            out_lines.append("%d refereed publications<br>\n"%refereed)
            out_lines.append("<a href=\"https://ui.adsabs.harvard.edu/search/p_=0&q=author:&quot;bocquet,s&quot; database:astronomy\">Publications on ADS</a>: %d citations, h-index %d<br>\n"%(citations, hindex))
            out_lines.append("<a href=\"https://scholar.google.com/citations?hl=en&user=K9dkRiQAAAAJ\">Profile on Google Scholar</a>: %d citations, h-index %d<br>\n"%(author['citedby'], author['hindex']))
        elif 'top_tier_content' in line:
            out_lines.append('<ol>\n')
            for p in top_tier_list:
                out_lines.append(p)
            out_lines.append('</ol>\n')
        elif 'other_pub_content' in line:
            out_lines.append('<ol>\n')
            for p in other_pub_list:
                out_lines.append(p)
            out_lines.append('</ol>\n')
        else:
            out_lines.append(line)

    with open('pub.html', 'w') as f:
        for line in out_lines:
            f.write(line)



if __name__=="__main__":
    main(sys.argv[1])
