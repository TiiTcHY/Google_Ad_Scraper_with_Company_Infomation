import requests
import pandas as pd
import re
from collections import Counter
from datetime import datetime
import glob
import time
import os
import shutil
import json
from tabulate import tabulate
import asyncio
from pyppeteer import launch
from PIL import Image

#gets the current date
current_date = datetime.now().strftime("%d-%m-%Y")
#gets the day (e.g Monday, Tuesday etc)
TodayDay = datetime.today().strftime('%A')
if TodayDay == 'Monday':
    location = 'Manchester,England,United Kingdom'
elif TodayDay == 'Tuesday':
    location = 'Liverpool,England,United Kingdom'
elif TodayDay == 'Wednesday':
    location = 'London,England,United Kingdom'
elif TodayDay == 'Thursday':
    location = 'Wales,United Kingdom'
elif TodayDay == 'Friday':
    location = 'England,United Kingdom'

# create folder to store all output documents in, grouped by dateå
if not os.path.exists(f'Outputs/{current_date}/Short'):
    os.makedirs(f'Outputs/{current_date}/Short')
if not os.path.exists(f'Outputs/{current_date}/Long'):
    os.makedirs(f'Outputs/{current_date}/Long')
if not os.path.exists(f'Outputs/{current_date}/Temp'):
    os.makedirs(f'Outputs/{current_date}/Temp')

#sets the filename for the CSV file
CSVFile = current_date + '_GoogleAd_Results.csv'

#sets the savefilepath varibales
ShortSavePath = #Set you file path to save the HTML which requrires a Short Screenshot
LongSavePath = #Set you file path to save the HTML which requrires a Full  Screenshot
TempSavePath = #Set you file path to temporary save files
FilesSavePath = #Set you file path 

#Insert brands
brands = ['']
#Insert Scaleserp.com API key
scaleserpkey = ''
#Function to convert a string to a list
def Convert(string):
    li = list(string.split(","))
    return li

#Import the list of domains you have already identified 
FoundList = ['']
#Add square brackets to the start and end of the string
FoundList = '[' + FoundList + ']'
#Covert the string into a list
AlreadyFoundDomains = json.loads(FoundList)
#List containing the search results
SearchResultsList = []
#Import the list of search terms
SearchTermsList = ['']
#Covert the string into a list
SearchTerms = Convert(SearchTermsList)
#Convert the list into a pandas DataFrame
SearchDataFrame = pd.DataFrame(SearchTerms,columns=['Keyword'])
#Import the list of domains you want excluded from the results
ExcludeList = ['']
#Covert the string into a list
ExcludeDomains = Convert(ExcludeList)
#blank lists to use later
branddomain = []
PartialSearchResult = []
NonDuplicateList = []
newresultlist = []
df_list = []
dfexcludelist = []
#for statement to go through each brand in the list
for brand in brands:
    #we will pull all the terms from the 'Keyword' column inside the dataframe
    terms = SearchDataFrame.loc[:, 'Keyword']
    #everytime there is a string(brand) this will be replaced the the brand name
    terms = [str(term).replace('brand', f'{brand}') for term in terms]
    contains_brand = []
    domains_in_matched_brand_ads = []

    #function which allows us to submit each term through the scaleserp API
    def submit_term(term):
        params = {
            f'api_key': {scaleserpkey},
            f'q': {term},
            f'location': {location},
            'device': 'mobile',
            'output': 'json',
            'include_html': 'true',
            'include_advertiser_info': 'true',
            'gl': 'uk',
            'hl': 'en',
            'google_domain': 'google.co.uk'
        }

        # make the http GET request to Scale SERP
        try:
            api_result = requests.get('https://api.scaleserp.com/search', params)
        except:
            time.sleep(30)
            api_result = requests.get('https://api.scaleserp.com/search', params, headers={'Connection':'close'})

        # print the JSON response from Scale SERP
        result = api_result.json()
        return result

    #Function to go from the results from the ScaleSerp API and identify if there are any ADS that contain our brands.
    def check_for_brand_string(serp_result):
        try:
            yeslist = []
            search_result = []
            search = "is_phone_ad"
            bottom = "block_position"
            #looks through each of the ads
            for serp in serp_result['ads']:
                #pulls the keys from the dict
                for key in serp.keys():
                    #looking to see if "phone_ad" is in the Key
                    if search in key:
                        #ammend the search result with the reuslt
                        search_result.append(search)
                    #looking through the ADS to identify if any of the domians contain our brands but not one of the brands from the exclusion list.
                    if type(serp[key]) is str and re.search(brand, serp[key], re.IGNORECASE) and serp[key] not in ExcludeDomains:
                        #if its a phone ad:
                        if search in search_result:
                            domains_in_matched_brand_ads.append(serp['domain'])
                            yeslist.append('yes')
                            matcheddomain = serp['domain']
                            matchedterm = serp[key]
                            searchbrand = brand
                            trackinglink = serp['tracking_link']
                            merged = matcheddomain + "|" + searchbrand
                            branddomain.append(merged)
                            try:
                                companyInfo = serp['advertiser_info']['company_name']
                            except:
                                companyInfo = "No Company Attached"
                            FullResult = matcheddomain + "|" + searchbrand + "  " + matchedterm + "  " + "Yes" + "  " + trackinglink + "  " + companyInfo
                            #we create a string format which will then get ammended to a list
                            newresultlist.append(FullResult)
                            if serp['block_position'] == 'bottom':
                                write_full_html_from_results(res, matcheddomain)
                            else:
                                write_short_html_from_results(res, matcheddomain)


                        #if it doesn't contain a phone ad then:
                        else:
                            domains_in_matched_brand_ads.append(serp['domain'])
                            yeslist.append('yes')
                            matcheddomain = serp['domain']
                            matchedterm = serp[key]
                            searchbrand = brand
                            trackinglink = serp['tracking_link']
                            merged = matcheddomain + "|" + searchbrand
                            branddomain.append(merged)
                            try:
                                companyInfo = serp['advertiser_info']['company_name']
                            except:
                                companyInfo = "No Company Attached"
                            FullResult = matcheddomain + "|" + searchbrand + "  " + matchedterm + "  " + "No" + "  " + trackinglink + "  " + companyInfo
                            #we create a string format which will then get ammended to a list
                            newresultlist.append(FullResult)
                            if serp['block_position'] == 'bottom':
                                write_full_html_from_results(res, matcheddomain)
                            else:
                                write_short_html_from_results(res, matcheddomain)


            if yeslist:
                contains_brand.append('yes')
            else:
                contains_brand.append('no')
        except:
            contains_brand.append('no')

    #function to get the HTML for the matched domain
    def write_full_html_from_results(serp_result, matcheddomain):
        try:
            # get html from json (requires request to scaleserp to include it)
            html = serp_result['html']
            if matcheddomain in ExcludeDomains:
                pass
            else:
                # write to file
                f = open(f"Outputs/{current_date}/Long/{brand}_HTML_{current_date}_for_domain_{matcheddomain}.html", "w")
                f.write(html)
                f.close()
        except:
            print("Error getting HTML results: none found!")

    #function to get the HTML for the matched domain
    def write_short_html_from_results(serp_result, matcheddomain):
        try:
            # get html from json (requires request to scaleserp to include it)
            html = serp_result['html']
            if matcheddomain in ExcludeDomains:
                pass
            else:
                # write to file
                f = open(f"Outputs/{current_date}/Short/{brand}_HTML_{current_date}_for_domain_{matcheddomain}.html", "w")
                f.write(html)
                f.close()
        except:
            print("Error getting HTML results: none found!")

    #function to open the HTML file and take a FULL screenshot of the file.
    async def generate_Full_png():
        for image_path in os.listdir(LongSavePath):
            input_path = os.path.join(LongSavePath, image_path)
            sourcepath = 'file://' + input_path
            browser = await launch(options={'args': ['--no-sandbox'],'headless':True})
            page = await browser.newPage()
            x = image_path.replace(".html", "")
            _OUTFILE = TempSavePath + str(x) + '.png'
            await page.goto(sourcepath)
            await page.screenshot({'path': _OUTFILE, 'fullPage': True})
            await browser.close()

    #function to open the HTML file and take a SHORT screenshot of the file.
    async def generate_Short_png():
        for image_path in os.listdir(ShortSavePath):
            input_path = os.path.join(ShortSavePath, image_path)
            sourcepath = 'file://' + input_path
            browser = await launch(options={'args': ['--no-sandbox'],'headless':True})
            page = await browser.newPage()
            x = image_path.replace(".html", "")
            _OUTFILE = FilesSavePath + str(x) + '.png'
            await page.goto(sourcepath)
            await page.setViewport({'width': 800, 'height':1000})
            await page.screenshot({'path': _OUTFILE, 'fullPage': False})
            await browser.close()

    def snip_full_screenshot():
        for image_path in os.listdir(TempSavePath):
            defaultheight = 1500
            _OUTFILE = FilesSavePath + str(image_path)
            input_path = os.path.join(TempSavePath, image_path)
            image = Image.open(input_path)
            imgwidth, imgheight = image.size
            NewHeight = imgheight - defaultheight
            halfedheight = imgheight/2
            x = 0
            y = NewHeight
            w = 800
            h = halfedheight + 1500
            image = image.crop((x,y,w,h))
            image.save(_OUTFILE)

    #ammend the newly created list into a dict
    output = {'Domain':newresultlist}
    #for statement for each of the search terms
    for term in terms:
        #if a term exsits
        if term:
            #call the submit term function
            res = submit_term(term)
            #call the check for brand function
            check_for_brand_string(res)
    #create a dataframe from the output dict.
    Outputdf = pd.DataFrame.from_dict(output, orient='index')
    Outputdf = Outputdf.transpose()
    if Outputdf.empty:
        pass
    else:
        #split the DataFrame based on a double space
        Outputdf[['Domains','MatchedTerm','CTC', 'Tracking_Link', 'Advertiser_Company']] = Outputdf.Domain.str.split("  ",expand=True)
        #delete the original column
        Outputdf = Outputdf.drop(['Domain'], axis = 1)
        #Count the occurance of the domains/brands
        OccuranceDataFrame = Outputdf.groupby('Domains').size()
        #remove duplicates from the original DataFrame
        NonDupsDataFrame = Outputdf.drop_duplicates(subset=['Domains']).reset_index()
        FinalDataFrame = OccuranceDataFrame.to_frame().reset_index()
        #sets the column names
        FinalDataFrame.columns = ['Domains','Occurance']
        #merge the two dataframe together
        FinalDataFrame = NonDupsDataFrame.merge(FinalDataFrame[['Domains','Occurance']], on='Domains', how='left')
        #split the domain column based on the | into two columns
        FinalDataFrame[['Domains','Brand']] = FinalDataFrame.Domains.str.split("|",expand=True)
        #re-order the columns
        FinalDataFrame = FinalDataFrame.reindex(columns=['Brand', 'Domains', 'Occurance', 'CTC','Advertiser_Company', 'MatchedTerm',  'Tracking_Link'])

        ExcludeDF = FinalDataFrame[(FinalDataFrame['MatchedTerm'].str.contains('|'.join(ExcludeDomains))) & (FinalDataFrame['Domains'].str.contains('|'.join(ExcludeDomains)))]
        FinalDataFrame = FinalDataFrame[~FinalDataFrame['Domains'].str.contains('|'.join(ExcludeDomains))]
        FinalDataFrame = FinalDataFrame[~FinalDataFrame['MatchedTerm'].str.contains('|'.join(ExcludeDomains))]
        if ExcludeDF.empty:
            pass
        else:
            ExcludeDF = ExcludeDF.drop(['Brand','CTC', 'MatchedTerm', 'Tracking_Link','Occurance','Advertiser_Company'],axis=1)
            dfexcludelist = ExcludeDF.values.tolist()

        MarketingDataFrame = FinalDataFrame.copy()
        FinalDataFrame = FinalDataFrame.drop(['Tracking_Link'], axis = 1)
        #convert the rows into a list.
        dfexcludelist = ExcludeDF.values.tolist()
        df_list = FinalDataFrame.values.tolist()
        MarketingDataFrame.to_csv(CSVFile, index=0)

    flatlist = [item for elem in dfexcludelist for item in elem]
    CombinedExcludeList =  flatlist + ExcludeDomains
    #counts the occurance of the domains
    founddomains = [x for x in domains_in_matched_brand_ads if x not in CombinedExcludeList]
    count_domains_in_matched_brand_ads = Counter(founddomains)

    #for statement to go through the doamins and counter
    for dom, cnt in count_domains_in_matched_brand_ads.most_common():
        #sets the brand
        BrandResult = (f'{brand}')
        DomainCounter = (" " + dom, " " +str(cnt))
        #joins the domains the counters together
        NewDomainCounter = ''.join(DomainCounter)
        #sets the string
        FullResult = BrandResult + NewDomainCounter
        #ammended it to a list.
        PartialSearchResult.append(FullResult.split())

#calls the function to get the screenshots from the HTML files.
asyncio.get_event_loop().run_until_complete(generate_Full_png())
asyncio.get_event_loop().run_until_complete(generate_Short_png())
snip_full_screenshot()

#creats two lists NewDomains + SeenDomains based on a comparision of the brand and domain with the new list and exclsion lists.
PartialNewDomainList = ([ x for x in PartialSearchResult if x[0:2] not in [ l[0:2] for l in AlreadyFoundDomains]])
PartialSeenDomainList = ([ x for x in PartialSearchResult if x[0:2] in [ l[0:2] for l in AlreadyFoundDomains]])
#creats two lists NewDomains + SeenDomains based on a comparision of the brand and domain with the new list and exclsion lists.
NewDomainsList = ([ x for x in df_list if x[0:2] not in [ l[0:2] for l in AlreadyFoundDomains]])
SeenDomainsList = ([ x for x in df_list if x[0:2] in [ l[0:2] for l in AlreadyFoundDomains]])

#if newDomainsLists is empty then:
if not NewDomainsList:
    #sets the HTML to nothing found
    NewBrands = "<p><b>No New Domains Identified</b></p>"
else:
    #creates a HTML table of the results
    NewBrands = (tabulate(NewDomainsList, headers=["Brand Name", "Domain", "Count", "Contains CTC", "Advertiser_Company", "Matched Term"],tablefmt='html'))

#if SeenDomainsList is empty then:
if not SeenDomainsList:
    #sets the HTML to nothing found
    SeenBrands = "<p><b>No already seen domains identified</b></p>"
else:
    #creates a HTML table of the results
    SeenBrands = (tabulate(SeenDomainsList, headers=["Brand Name", "Domain", "Count", "Contains CTC", "Advertiser_Company", "Matched Term"],tablefmt='html'))

#try to delete the short folder and the HTML files inside of it
try:
    shutil.rmtree(ShortSavePath)
    print("The Files has been removed")
except OSError as e:
    print("Error: %s : %s" % (path, e.strerror))

#try to delete the long folder and the HTML files inside of it
try:
    shutil.rmtree(LongSavePath)
    print("The Files has been removed")
except OSError as e:
    print("Error: %s : %s" % (path, e.strerror))

#try to delete the temp folder and the HTML files inside of it
try:
    shutil.rmtree(TempSavePath)
    print("The Files has been removed")
except OSError as e:
    print("Error: %s : %s" % (path, e.strerror))
try:
    for root, subdirs, files in os.walk(FilesSavePath):
        for filename in files:
            for domain in CombinedExcludeList:
                if domain in filename:
                    filestoremove = os.path.join(FilesSavePath, filename)
                    os.remove(filestoremove)
                    print(filestoremove)
                    print("Files removed - List 1")
except:
    print("Cannot remove files - list1")

#try to create a ZIP file of the outputs for the image files
try:
    for dirpath, dirnames, files in os.walk(FilesSavePath):
        if files:
            shutil.make_archive(current_date + '_Output', 'zip', FilesSavePath)
        if not files:
            pass
except:
    print("Cannot make ZIP")

#try to remove the remaing files to clean up
try:
    shutil.rmtree('Outputs/')
    print("The Files has been removed")
except OSError as e:
    print("Error: %s : %s" % (path, e.strerror))