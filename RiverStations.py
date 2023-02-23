'''Python 3 script, which makes use of the modules: pandas, numpy, datetime, pgeocode, matplotlib.
These modules can be downloaded using pip. Script was tested on python 3.10.10

RiverStations.py has user inputs as it runs to select a measurement station. It then plots graphs for water level, flow rate, wind velocity and temperature if it has the readings.'''

# import modules
import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
# pgeocode adds to postcode and town search - this is the least likely to already be installed
# pip install pgeocode
import pgeocode as pg


def station_search():
    ''' 
    function to find a measurement station based on name/town/postcode
    
    returns
    -------
    [station reference, station label (name)]
    '''
    # This will run until a station has been selected
    station = ''
    while station == '':
        search_method = input('To search by measurement station enter 1, to search by town enter 2, or to search by postcode enter 3\n')
        # based on input this redirects to corresponding function
        if search_method == '1':
            station = name_search()
        elif search_method == '2':
            station = town_search()
        elif search_method == '3':
            station = postcode_search()
        else:
            print('Please enter 1, 2, or 3')
    return station

def name_search():
    ''' 
    function to find a measurement station based on a name
        
    returns
    -------
    [station reference, station label (name)]
    or '' to try the search process again
    '''
    # get the list of stations from the api
    stations = pd.read_csv('http://environment.data.gov.uk/flood-monitoring/id/stations.csv')
    search_name = input('Name a station\n')
    # find matches between user input and the list
    results = [search_name.lower() in i.lower() for i in stations.label]
    
    if sum(results)>0:
        print('Did you mean?')
        # lists options with extra information to help make a choice
        print(stations[['label','riverName','catchmentName','town']][results])
        index = input('Enter the associated number for the monitoring station or n to search again\n')
        if index == 'n':
            station = ''
        else:        
            station = [stations.stationReference[int(index)],stations.label[int(index)]]
    else:
        # if no stations are found
        print('No matching stations found')
        station = ''
    return station

def town_search():
    ''' 
    function to find a measurement station based on a town
        
    returns
    -------
    [station reference, station label (name)]
    or '' to try the search process again
    '''
    # format the town name correctly
    town_name = input('Name a town\n').capitalize()
    try:
        # where the town name is written in the api we can query the data like this
        stations = pd.read_csv('http://environment.data.gov.uk/flood-monitoring/id/stations.csv?town=' + town_name)
        print('Would you like?')
        # options for this town
        print(stations[['label','riverName','catchmentName','town']])
        index = input('Enter the associated number for the monitoring station or n to search again\n')
        if index == 'n':
            station = ''
        else:        
            station = [stations.stationReference[int(index)],stations.label[int(index)]]
    except:
        # where the town name is not in the api we can get latitude and longitude from the pgeocode module
        locations = pg.Nominatim('GB').query_location(town_name)
        if len(locations)>0:
            print('Did you mean?')
            # shows options where multiple towns have the same name
            print(locations[['place_name','county_name','postal_code']].reset_index())
            index = int(input('Enter the associated number for the town\n'))
            lat = locations.latitude.iloc[index]
            lon = locations.longitude.iloc[index]

            try:
                # can query the data with the longitude and latitude - here dist = 5 means we are looking within a 5km radius
                stations = pd.read_csv('http://environment.data.gov.uk/flood-monitoring/id/stations.csv?lat='+str(lat)+'&long='+str(lon)+'&dist=5')
                print('Would you like?')
                # lists options
                print(stations[['label','riverName','catchmentName','town']])
                
                index = input('Enter the associated number for the monitoring station or n to search again\n')
                if index == 'n':
                    station = ''
                else:        
                    station = [stations.stationReference[int(index)],stations.label[int(index)]]
            except:
                # If no stations are found within 5km of town
                print('No station found within 5km from town')
                station = ''
        else:
            # If no town with that name is in the uk
            print('Town not found')
            station = ''
    return station

def postcode_search():
    ''' 
    function to find a measurement station based on a postcode
        
    returns
    -------
    [station reference, station label (name)]
    or '' to try the search process again
    '''
    # Can input just the first half of postcode, or whole postcode with the space.
    postcode = input('Enter a postcode\n')
    location = pg.Nominatim('GB').query_postal_code(postcode)
    # from postcode get a latitude and a longitude
    lat = location.latitude
    lon = location.longitude
    if np.isnan(lat):
        print('invalid postcode')
        station = ''
    else:
        try:
            # can query the data with the longitude and latitude - here dist = 5 means we are looking within a 5km radius
            stations = pd.read_csv('http://environment.data.gov.uk/flood-monitoring/id/stations.csv?lat='+str(lat)+'&long='+str(lon)+'&dist=5')
            print('Would you like?')
            #lists options
            print(stations[['label','riverName','catchmentName','town']])
            index = input('Enter the associated number for the monitoring station or n to search again\n')
            if index == 'n':
                station = ''
            else:        
                station = [stations.stationReference[int(index)],stations.label[int(index)]]
        except:
            print('No station found within 5km from town')
            station = ''
    return station


def get_readings():
    '''
    function to get the readings from the measurement stations
    
    Will display a line graph of the data from the last 24 hours if there is any
    '''
    # selects a station
    station = station_search()
    # works out when yesterday was
    yesterday = dt.datetime.now()-dt.timedelta(1)
    # formats the time correctly for the query
    yesterdaystr = yesterday.strftime('%Y-%m-%dT%XZ')
    #dictionaries for the different readings the stations can measure
    parameters = {'level':'Water Level','flow':'Water Flow Rate','wind':'Wind Velocity','temperature':'Air Temperature'}
    units = {'level':'(m)','flow':'(m/s)','wind':'(m/s)','temperature':'(°C)'}
    
    for p in parameters:
        try:
            # gets the readings for a given station and parameter for the last 24 hours
            readings = pd.read_csv('https://environment.data.gov.uk/flood-monitoring/id/stations/'+str(station[0])+'/readings.csv?since='+yesterdaystr+'&parameter='+p,parse_dates=[0])
            # plots the data
            readings.plot('dateTime','value',rot=60,xlabel = 'Date and Time',ylabel = parameters[p]+' ' + units[p],legend = False,title = parameters[p]+' for '+station[1]+' in the last 24 hours')
            plt.show()
        except:
            # if no readings for parameter in the last 24 hours
            print('No readings for '+parameters[p]+' in last 24 hours')
            
# runs the function            
get_readings()