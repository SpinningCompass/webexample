#======================================================================#
# File Name: skyscraper.py
# Author: Megan Yancy megan.c.yancy@gmail.com
# Date Created: 20161112
# Description: This program goes to the NOAA site, allows the user
#              to download storm information by year and name, and
#              imports to a specified geodatabase. Requires user
#              interaction.
# Requirements:
#       BeautifulSoup - https://www.crummy.com/software/BeautifulSoup/
#                       bs4/doc/
#       requests - http://docs.python-requests.org/en/master/
#======================================================================#

import requests
import arcpy
from arcpy import env
import os
import StringIO
import zipfile
from BeautifulSoup import BeautifulSoup

url = 'http://www.nhc.noaa.gov/gis/archive_forecast.php'

# convert shapefiles to feature classes
def convertShapefiles():
    env.workspace = 'hurricane_data'
    env.overwriteOutput = True
    fcList = arcpy.ListFeatureClasses()
    print("shapefiles: {0}".format(fcList))
    stormsGDB = 'storms.gdb'
    if not arcpy.Exists(stormsGDB):
        arcpy.CreateFileGDB_management(env.workspace, stormsGDB)
    arcpy.FeatureClassToGeodatabase_conversion(fcList, stormsGDB)

    #delete downloaded data
    for fc in fcList:
        arcpy.Delete_management(fc)
        
    
# download zipfiles to folder
def getZipfiles(zipUrls):
    
    response =  requests.get(zipUrls)
    html = response.content
    soup = BeautifulSoup(html)
    extractionDir = 'hurricane_data'

    zipUrlList = []
    for pageUrl in soup.findAll('a'):
        findZip = str(pageUrl.get('href'))
        try:
            if findZip[-4:] == '.zip':
                zipUrlList.append(findZip)
                fileUrl = 'http://www.nhc.noaa.gov/gis/'
                fileUrl += findZip
                getFile = requests.get(fileUrl, stream=True)
                if getFile.ok == True:
                    zipRef = zipfile.ZipFile(StringIO.StringIO(getFile.content))
                    zipRef.extractall(extractionDir)
                    zipRef.close()
                print("Extracting {0} to {1}".format(findZip[17:], extractionDir))
        except Exception:
            pass

    
# create a menu based off the years available   
def printMenu():
    
    response = requests.get(url)
    html = response.content
    soup = BeautifulSoup(html)

    #access form  to select a year
    getForm = soup.find('form', attrs={'name':'yearselect'})
    getYears = []

    for row in getForm.findAll('option'):
        try:
            getYears.append(int(row.text))
        except ValueError:
            pass
    print("Choose a year:\n")
    for option in getYears:
        print("{0}".format(option))
        
    print("Quit")

    return getYears

# make the storms table readable to a human
def processStorms(stormsList):

    for storm in stormsList:
        print("{0}: {1}".format(storm[0], storm[1]))
    zipList = raw_input("Choose a storm Id Number:\t")

    for storm in stormsList:
        if zipList == storm[0]:
            getZipfiles('http://www.nhc.noaa.gov{0}'.format(storm[2]))

            
# main program
def main():
    userContinue = True
    failLoop = 0
    while userContinue == True and failLoop < 5:
        getYears = printMenu()
        userYear = raw_input("\nChoose a year to download from: ")
        try:
            userYear = int(userYear)
            if userYear in getYears:
                form = {'year':'{0}'.format(userYear)}
                response = requests.post(url, data=form)
                html = response.content
                soup = BeautifulSoup(html)

                table = soup.find('tbody')
                Atlantic = []
                Pacific = []

                for row in table.findAll('tr'):
                    rowlist = []
                    for stormComponent in row.findAll('td'):
                        rowlist.append(stormComponent.text)
                    if rowlist[0][:2] == 'al' or rowlist[0][:2] == 'ep':    
                        parsedURL = u'/gis/archive_forecast_results.php?'
                        parsedURL +='id={0}&year={1}&name={2}'.format(rowlist[0],
                                                                      userYear,
                                                                      rowlist[1])
                        rowlist.append(parsedURL)

                        if rowlist[0][:2] == 'al':
                            Atlantic.append(rowlist)
                        if rowlist[0][:2] == 'ep':
                            Pacific.append(rowlist)
                validOcean = False
                incorrectInput = 0
                while validOcean == False and incorrectInput < 2: 
                    try:
                        ocean = input("Atlantic or Pacific Storms?\t")
                        processStorms(ocean)
                        validOcean = True
                    except Exception:
                        print('Choose Atlantic or Pacific.')
                        print('{0} more tries'.format(2 - incorrectInput))
                        incorrectInput +=1
        except ValueError:
            if userYear.upper().strip()  == "QUIT":
                print("Quitting Program")
                userContinue = False
                exit()
            else:
                failLoop += 1
                print("Not a valid selection. Please try again.")
        convertShapefiles()

if __name__ == "__main__":
    main()
