import xlrd
import requests
import unicodecsv

COUNTIES = ['Adair','Adams','Allamakee','Appanoose','Audubon','Benton','Black Hawk','Boone','Bremer','Buchanan','Buena Vista','Butler','Calhoun','Carroll','Cass','Cedar','Cerro Gordo','Cherokee','Chickasaw','Clarke','Clay','Clayton','Clinton','Crawford','Dallas','Davis','Decatur','Delaware','Des Moines','Dickinson','Dubuque','Emmet','Fayette','Floyd','Franklin','Fremont','Greene','Grundy','Guthrie','Hamilton','Hancock','Hardin','Harrison','Henry','Howard','Humboldt','Ida','Iowa','Jackson','Jasper','Jefferson','Johnson','Jones','Keokuk','Kossuth','Lee','Linn','Louisa','Lucas','Lyon','Madison','Mahaska','Marion','Marshall','Mills','Mitchell','Monona','Monroe','Montgomery','Muscatine','Obrien','Osceola','Page','Palo Alto','Plymouth','Pocahontas','Polk','Pottawattamie','Poweshiek','Ringgold','Sac','Scott','Shelby','Sioux','Story','Tama','Taylor','Union','Van Buren','Wapello','Warren','Washington','Wayne','Webster','Winnebago','Winneshiek','Woodbury','Worth','Wright']


def download_county_files():
    for county in COUNTIES:
        url = "https://sos.iowa.gov/elections/results/xls/2012/general/%s.xls" % county
        r = requests.get(url, stream=True)
        filename = county+'.xls'
        with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk)
