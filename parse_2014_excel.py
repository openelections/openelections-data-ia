import xlrd
import requests
import unicodecsv

results = []

def download_file():
    url = "https://sos.iowa.gov/elections/results/xls/2014/general/statewide.xlsx"
    r = requests.get(url, stream=True)
    with open("statewide.xlsx", 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)

def parse_results():
    book = xlrd.open_workbook("statewide.xlsx")
    sh = book.sheet_by_index(0)
    headers = sh.row(0)
    precincts = headers[3:sh.ncols]
    for rx in range(1, sh.nrows):
        row = sh.row(rx)
        office = row[0].value.strip()
        if "Dist." in office:
            office, district = office.split(' Dist. ')
        else:
            district = None
        candidate = row[1].value.strip()
        party = row[2].value.strip()
        vote_cells = row[3:sh.ncols]
        for idx, vote_cell in enumerate(vote_cells):
            if vote_cell.value == ' ':
                continue
            if '-' in precincts[idx].value:
                county, precinct = precincts[idx].value.split('-', 1)
                if 'Absentee' in precinct:
                    vote_type = 'Absentee'
                    precinct = precinct.replace(' Absentee','')
                elif 'Polling' in precinct:
                    vote_type = 'Polling'
                    precinct = precinct.replace(' Polling','')
                elif ' Total' in precinct:
                    vote_type = 'Total'
                    precinct = precinct.replace(' Total','')
            else:
                county = precincts[idx].value.replace(' Total','')
                precinct = None
                vote_type = 'Total'
            r = [x for x in results if x['county'] == county and x['precinct'] == precinct and x['office'] == office and x['district'] == district and x['party'] == party and x['candidate'] == candidate]
            if r:
                r[0][vote_type.lower()] = vote_cell.value
            else:
                results.append({ 'county': county, 'precinct': precinct, 'office': office, 'district': district, 'party': party, 'candidate': candidate, vote_type.lower(): vote_cell.value})
    return results

def write_csv(results):
    with open('20141104__ia__general__precinct.csv', 'wb') as csvfile:
         w = unicodecsv.writer(csvfile, encoding='utf-8')
         w.writerow(['county', 'precinct', 'office', 'district', 'party', 'candidate', 'absentee', 'polling', 'votes'])
         for row in results:
             if row['precinct']:
                 w.writerow([row['county'].strip(), row['precinct'], row['office'], row['district'], row['party'], row['candidate'], row['absentee'], row['polling'], row['total']])
             else:
                 w.writerow([row['county'].strip(), row['precinct'], row['office'], row['district'], row['party'], row['candidate'], None, None, row['total']])
