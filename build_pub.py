import sys
import requests
from scholarly import ProxyGenerator, scholarly

top_tier_bibcodes = ['2021MNRAS.504.1253G', '2020MNRAS.498..771G', '2019MNRAS.488.2041G',
                     '2018MNRAS.478.3072C', '2018MNRAS.474.2635S', '2016MNRAS.455..258C',]
DES_coauthor_bibcodes = ['2021MNRAS.507.5758S', 'arXiv:2105.13541', 'arXiv:2202.07440', '2022MNRAS.515.4471W',
                         'arXiv:2310.00059', 'arXiv:2310.13207', 'arXiv:2311.07512',]
DES_builder_bibcodes = ['2023arXiv230900671Z',
                        '2023arXiv230906593A',
                        '2023MNRAS.521..836S',
                        '2023AJ....165..222L',
                        '2023MNRAS.522.1951D',
                        '2023MNRAS.522.3163S',
                        'arXiv:2304.13570',
                        '2023MNRAS.522.4132Y',
                        'arXiv:2305.17173',
                        ]
white_paper_bibcodes = ['2019BAAS...51c.279M', '2022arXiv220306795B', '2022arXiv220308024A']

ads_prefix = "https://ui.adsabs.harvard.edu/abs/"
ads_suffix = "/abstract"
doi_prefix = "https://doi.org/"

def main(ads_token):
    overview_content = []

    # ADS
    r = requests.get("https://api.adsabs.harvard.edu/v1/search/query",
                     headers={'Authorization': 'Bearer '+ads_token},
                     params={'q': 'author:"bocquet,s" database:astronomy',
                             'fl': 'author,bibcode,bibstem,citation_count,date,doi,identifier,page,title,volume,year',
                             'sort': 'date desc,bibcode desc',
                             'rows': 1000},
                     timeout=6.1)
    ads_papers = r.json()['response']['docs']
    # Somehow strangely, some papers don't have the citation_count key
    for paper in ads_papers:
        if 'citation_count' not in paper.keys():
            paper['citation_count'] = 0
    # Metrics
    sorted_citation_count = sorted([paper['citation_count'] for paper in ads_papers])[::-1]
    citations = sum(sorted_citation_count)
    hindex = 0
    while sorted_citation_count[hindex]>=(hindex+1):
        hindex+= 1
    refereed = 0
    peer_rev_j = ['AJ', 'ApJ', 'ApJS', 'A&A', 'JOSS', 'MNRAS', 'PhRvD', 'PhRvL']
    for paper in ads_papers:
        if paper['bibstem'][0] in peer_rev_j:
            refereed+= 1

    # List of DES papers
    ref = "https://dbweb8.fnal.gov:8443/DESPub/app/PB/pub/pbpublished"
    f = requests.get(ref, timeout=6.1)
    DES_paper_list = f.text

    # Publication list
    top_tier_list, co_pub_list, DES_pub_list, white_paper_list, other_pub_list = [], [], [], [], []
    for p,paper in enumerate(ads_papers):
        # Skip proposals, zenodo, VizieR
        if paper['bibstem'][0] in ['ascl', 'hst', 'MPEC', 'sptz', 'trec', 'yCat', 'zndo']:
            continue
        # PhD thesis
        if paper['bibstem'][0]=='PhDT':
            a = 'Sebastian Bocquet'
            pub_type = 'other'
        else:
            # First-author
            if 'Bocquet' in paper['author'][0]:
                if len(paper['author'])==2:
                    a = ' & '.join([paper['author'][i].split(',')[0] for i in range(2)])
                else:
                    a = ', '.join([paper['author'][i].split(',')[0] for i in range(3)])+' et al.'
                pub_type = 'top'
            # Top-tier
            elif ('Bocquet' in paper['author'][1])|('Bocquet' in paper['author'][2])|(paper['bibcode'] in top_tier_bibcodes):
                for aa,a in enumerate(paper['author'][:5]):
                    if 'Bocquet' in a:
                        # Want minimum of three authors listed
                        if aa==1:
                            a = ', '.join([paper['author'][i].split(',')[0] for i in range(aa+2)])+' et al.'
                        else:
                            a = ', '.join([paper['author'][i].split(',')[0] for i in range(aa+1)])+' et al.'
                        pub_type = 'top'
                        break
            # Other
            else:
                pub_type = 'coauthor'
                # Is it a DES builder paper?
                if not any(x in paper['identifier'] for x in DES_coauthor_bibcodes):
                    for bibcode in paper['identifier']:
                        if bibcode in DES_builder_bibcodes:
                            pub_type = 'DES'
                        elif bibcode[4:9]=='arXiv':
                            code = '.'.join((bibcode[9:13],bibcode[13:18]))
                            if (float(code[:2])>=21) and (code in DES_paper_list):
                                pub_type = 'DES'
                # White papers
                for bibcode in paper['identifier']:
                    if bibcode in white_paper_bibcodes:
                        pub_type = 'white_paper'
                # Is it the ATel?
                if paper['bibstem'][0]=='ATel':
                    pub_type = 'other'
                a = paper['author'][0].split(',')[0]+' et al.'

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

        if pub_type=='top':
            top_tier_list.append(this)
        elif pub_type=='coauthor':
            co_pub_list.append(this)
        elif pub_type=='DES':
            DES_pub_list.append(this)
        elif pub_type=='white_paper':
            white_paper_list.append(this)
        else:
            other_pub_list.append(this)


    # Google scholar (fails more often than not)
    try:
        pg = ProxyGenerator()
        pg.FreeProxies()
        scholarly.use_proxy(pg)
        author = scholarly.search_author_id('K9dkRiQAAAAJ')
        scholarly_info = scholarly.fill(author, sections=['indices',])
    except:
        scholarly_info = None


    with open('pub_blank.html', 'r') as f:
        lines = f.readlines()
    out_lines = []
    for line in lines:
        if 'overview_content' in line:
            out_lines.append("%d refereed publications<br>\n"%refereed)
            out_lines.append("<a href=\"https://ui.adsabs.harvard.edu/search/p_=0&q=author:&quot;bocquet,s&quot; database:astronomy\">Publications on ADS</a>: %d citations, h-index %d<br>\n"%(citations, hindex))
            if scholarly_info is not None:
                out_lines.append("<a href=\"https://scholar.google.com/citations?hl=en&user=K9dkRiQAAAAJ\">Profile on Google Scholar</a>: %d citations, h-index %d<br>\n"%(scholarly_info['citedby'], scholarly_info['hindex']))
            out_lines.append("ORCID: <a href=\"https://orcid.org/0000-0002-4900-805X\">https://orcid.org/0000-0002-4900-805X</a>")
            # out_lines.append("%d first-author or top-tier publications, %d co-authored publications, %d publications as DES builder\n"%(len(top_tier_list), len(co_pub_list), len(DES_pub_list)))
        elif 'top_tier_content' in line:
            out_lines.append('<ol>\n')
            for p in top_tier_list:
                out_lines.append(p)
            out_lines.append('</ol>\n')
        elif 'co_pub_content' in line:
            out_lines.append('<ol>\n')
            for p in co_pub_list:
                out_lines.append(p)
            out_lines.append('</ol>\n')
        elif 'DES_pub_content' in line:
            out_lines.append('<ol>\n')
            for p in DES_pub_list:
                out_lines.append(p)
            out_lines.append('</ol>\n')
        elif 'white_paper_content' in line:
            out_lines.append('<ol>\n')
            for p in white_paper_list:
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
