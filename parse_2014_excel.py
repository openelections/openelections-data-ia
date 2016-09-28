import xlrd
import requests
import unicodecsv

COUNTIES = ['Adair','Adams','Allamakee','Appanoose','Audubon','Benton','Black Hawk','Boone','Bremer','Buchanan','Buena Vista','Butler','Calhoun','Carroll','Cass','Cedar','Cerro Gordo','Cherokee','Chickasaw','Clarke','Clay','Clayton','Clinton','Crawford','Dallas','Davis','Decatur','Delaware','Des Moines','Dickinson','Dubuque','Emmet','Fayette','Floyd','Franklin','Fremont','Greene','Grundy','Guthrie','Hamilton','Hancock','Hardin','Harrison','Henry','Howard','Humboldt','Ida','Iowa','Jackson','Jasper','Jefferson','Johnson','Jones','Keokuk','Kossuth','Lee','Linn','Louisa','Lucas','Lyon','Madison','Mahaska','Marion','Marshall','Mills','Mitchell','Monona','Monroe','Montgomery','Muscatine',"O'brien",'Osceola','Page','Palo Alto','Plymouth','Pocahontas','Polk','Pottawattamie','Poweshiek','Ringgold','Sac','Scott','Shelby','Sioux','Story','Tama','Taylor','Union', 'Van Buren','Wapello','Warren','Washington','Wayne','Webster','Winnebago','Winneshiek','Woodbury','Worth','Wright']

def download_file():
    url = "https://sos.iowa.gov/elections/results/xls/2014/general/statewide.xlsx"
    r = requests.get(url, stream=True)
    with open("statewide.xlsx", 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)

def download_county_files():
    for county in COUNTIES:
        url = "https://sos.iowa.gov/elections/results/xls/2016/primary/%s.xlsx" % county
        r = requests.get(url, stream=True)
        filename = county+'.xlsx'
        with open(filename, 'wb') as f:
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

def parse_primary(county):
    print county
    results = []
    filename = county+'.xlsx'
    book = xlrd.open_workbook(filename)
    sh = book.sheet_by_index(0)
    precincts = [x.value for x in sh.row(0)[3:]]
    for rx in range(1, sh.nrows):
        vote_cols = [x.value for x in sh.row(rx)[3:]]
        row = sh.row(rx)
        if row[0].value.strip() == '':
            continue
        office, party = row[0].value.split(' - ')
        candidate = row[1].value.strip()
        if 'Dist' in office:
            office, district = office.split(' Dist. ')
        else:
            district = None
        for idx, precinct in enumerate(precincts):
            if '-' in precinct:
                precinct = precinct.split('-', 1)[1].strip()
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
                county = precinct.replace(' Total','')
                precinct = None
                vote_type = 'Total'
            r = next((x for x in results if x['county'] == county and x['precinct'] == precinct and x['office'] == office and x['district'] == district and x['party'] == party and x['candidate'] == candidate), None)
            if r:
                r[vote_type.lower()] = vote_cols[idx]
            else:
                results.append({ 'county': county, 'precinct': precinct, 'office': office, 'district': district, 'party': party, 'candidate': candidate, vote_type.lower(): vote_cols[idx]})
    return results

def write_csv(results, county):
    filename = '20160607__ia__primary__%s__precinct.csv' % county.lower().replace(' ','_')
    with open(filename, 'wb') as csvfile:
         w = unicodecsv.writer(csvfile, encoding='utf-8')
         w.writerow(['county', 'precinct', 'office', 'district', 'party', 'candidate', 'absentee', 'polling', 'votes'])
         for row in results:
             try:
                 w.writerow([row['county'].strip(), row['precinct'], row['office'], row['district'], row['party'], row['candidate'], row['absentee'], row['polling'], row['total']])
             except:
                 if row.get('polling') is not None:
                     w.writerow([row['county'].strip(), row['precinct'], row['office'], row['district'], row['party'], row['candidate'], None, None, row['polling']])
                 elif row.get('absentee') is not None:
                    w.writerow([row['county'].strip(), row['precinct'], row['office'], row['district'], row['party'], row['candidate'], None, None, row['absentee']])
                 else:
                    w.writerow([row['county'].strip(), row['precinct'], row['office'], row['district'], row['party'], row['candidate'], None, None, row['total']])
