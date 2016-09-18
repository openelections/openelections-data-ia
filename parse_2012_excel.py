import xlrd
import requests
import unicodecsv

# need to parse O'Brien County file

COUNTIES = ['Adair','Adams','Allamakee','Appanoose','Audubon','Benton','Black Hawk','Boone','Bremer','Buchanan','Buena Vista','Butler','Calhoun','Carroll','Cass','Cedar','Cerro Gordo','Cherokee','Chickasaw','Clarke','Clay','Clayton','Clinton','Crawford','Dallas','Davis','Decatur','Delaware','Des Moines','Dickinson','Dubuque','Emmet','Fayette','Floyd','Franklin','Fremont','Greene','Grundy','Guthrie','Hamilton','Hancock','Hardin','Harrison','Henry','Howard','Humboldt','Ida','Iowa','Jackson','Jasper','Jefferson','Johnson','Jones','Keokuk','Kossuth','Lee','Linn','Louisa','Lucas','Lyon','Madison','Mahaska','Marion','Marshall','Mills','Mitchell','Monona','Monroe','Montgomery','Muscatine','Obrien','Osceola','Page','Palo Alto','Plymouth','Pocahontas','Polk','Pottawattamie','Poweshiek','Ringgold','Sac','Scott','Shelby','Sioux','Story','Tama','Taylor','Union','Van Buren','Wapello','Warren','Washington','Wayne','Webster','Winnebago','Winneshiek','Woodbury','Worth','Wright']
OFFICES = ['President/Vice President', 'U.S. House of Representatives', 'State Senator', 'State Representative', 'Co. Supervisor']
PARTIES = ['Republican', 'Democratic', 'Constitution', 'Iowa Green Party', 'Libertarian', 'Party for Socialism and Liberation', 'Socialist Workers Party', 'Nominated by Petition']

def download_county_files():
    for county in COUNTIES:
        url = "https://sos.iowa.gov/elections/results/xls/2012/general/%s.xls" % county
        r = requests.get(url, stream=True)
        filename = county+'.xls'
        with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk)

def parse_file(county):
    print county
    results = []
    filename = county+'.xls'
    book = xlrd.open_workbook(filename)
    sh = book.sheet_by_index(0)
    for rx in range(sh.nrows):
        if not isinstance(sh.row(rx)[5].value, float) and [x.value for x in sh.row(rx)[0:4]] == ['','','',''] and sh.row(rx)[5].value.strip() != '':
            office = sh.row(rx)[5].value.replace('\n','')
            if "District" in office and 'District Court' not in office and 'Board of Supervisors' not in office:
                office, district = office.split(' District ')
            else:
                district = None
        elif sh.row(rx)[0].value == 'Precinct':
            candidates = []
            raw_candidates = [x.value.replace('\n',' ').strip() for x in sh.row(rx)[2:-1] if x.value != '']
            for rc in raw_candidates:
                try:
                    party = [p for p in PARTIES if p in rc][0]
                    candidate = rc.replace(party, '').strip()
                except:
                    party = None
                    candidate = rc
                candidates.append({ 'candidate': candidate, 'party': party})
        elif sh.row(rx)[2].value.strip() == 'Election Day':
            precinct = sh.row(rx)[0].value
            for idx, vote_cell in enumerate(sh.row(rx)[5:len(candidates)+5]):
                cand = candidates[idx]
                results.append({ 'county': county, 'precinct': precinct, 'office': office, 'district': district, 'party': cand['party'], 'candidate': cand['candidate'], 'election_day': vote_cell.value})
        elif sh.row(rx)[2].value.strip() == 'Absentee':
            for idx, vote_cell in enumerate(sh.row(rx)[5:len(candidates)+5]):
                cand = candidates[idx]
                r = [x for x in results if x['county'] == county and x['precinct'] == precinct and x['office'] == office and x['district'] == district and x['party'] == cand['party'] and x['candidate'] == cand['candidate']]
                if r:
                    r[0]['absentee'] = vote_cell.value
        elif sh.row(rx)[2].value.strip() == 'Total':
            for idx, vote_cell in enumerate(sh.row(rx)[5:len(candidates)+5]):
                cand = candidates[idx]
                r = [x for x in results if x['county'] == county and x['precinct'] == precinct and x['office'] == office and x['district'] == district and x['party'] == cand['party'] and x['candidate'] == cand['candidate']]
                if r:
                    r[0]['votes'] = vote_cell.value
        else:
            continue
    return results

def write_csv(results, county):
    filename = '20121106__ia__general__%s__precinct.csv' % county.lower().replace(' ','_')
    with open(filename, 'wb') as csvfile:
         w = unicodecsv.writer(csvfile, encoding='utf-8')
         w.writerow(['county', 'precinct', 'office', 'district', 'party', 'candidate', 'absentee', 'election_date', 'votes'])
         for row in results:
             if 'precinct' in row and 'absentee' in row:
                 w.writerow([row['county'].strip(), row['precinct'], row['office'], row['district'], row['party'], row['candidate'], row['absentee'], row['election_day'], row['votes']])
             elif 'votes' in row:
                 w.writerow([row['county'].strip(), row['precinct'], row['office'], row['district'], row['party'], row['candidate'], None, None, row['votes']])
