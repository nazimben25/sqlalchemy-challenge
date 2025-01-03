# Import the dependencies.

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

import numpy as np

from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta

from flask import Flask, jsonify

    
from collections import defaultdict  # to generate dictionary 'precipitation

################################################
# Database Setup
################################################
engine = create_engine("sqlite:///SurfsUp/Resources/hawaii.sqlite")


# reflect an existing database into a new model
Base = automap_base()
Base.prepare(autoload_with=engine)

# # reflect the tables
Base.classes.keys()

#to check
print(Base.classes.keys())

# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#to check
print(session.query(measurement).first().__dict__)
print(session.query(station).first().__dict__)

# retrieve the last date (recent) + conversion from measurment table

date_most_recent = session.query(measurement.date).order_by(measurement.date.desc()).first()
date_most_recent = date_most_recent.date 
    
    
# retrieve the most active station from measurment table

station_active = session.query(measurement.station, \
                func.count(measurement.station)).\
                group_by(measurement.station).\
                order_by(func.count(measurement.station).desc())\
                .all()
most_active_station = station_active[0][0]

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

## welcome route presentation of the 6 routes available

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Welcome to the hawaii meteo API! <br/>"
        f"  <br/>"
        f"Available Routes:<br/>"
        f"  <br/>"
        f"Precipitation of the last year     : /api/v0.1/precipitation <br/>"
        f"Lists of all the stations       : /api/v0.1/station <br/>"
        f"Temperature of the last year for the most active station    : /api/v0.1/tobs <br/>"
        f"Returns TMIN, TAVG, TMAX from date to specify (yyyy-mm-dd)      : /api/v0.1/date_start <br/>"
        f"Returns TMIN, TAVG, TMAX between 2 dates  (yyyy-mm-dd) \
                : /api/v0.1/date_start/date_end <br/>"
        )


# route precipitation : returns the precipitation data for the last year before th max date

@app.route("/api/v0.1/precipitation")
def precipitation():

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # query measurment table for the last date in the DB

    precipitation_1y = session.query(measurement.date, measurement.prcp)\
              .filter(measurement.date >= \
                   (datetime.strptime(date_most_recent, "%Y-%m-%d")- timedelta(days=366) )\
                   )\
              .order_by(measurement.date) \
              .all()       
    
    #create a list to be jsonified, by looping through the result above
    prcp_by_date = []

    for date_x, prcp_x in precipitation_1y :
        prcp_dict = {}
        prcp_dict['Date'] = date_x
        prcp_dict['prcp'] = prcp_x

        prcp_by_date.append(prcp_dict)

    # close the session     
    session.close()

    ## cnvert t dictionary with key as date and prcp as values
    date_values = defaultdict(list)

    # Populate the dictionary
    for entry in prcp_by_date:
        date = entry["Date"]
        prcp = entry["prcp"]
        date_values[date].append(prcp)

    # Convert defaultdict to a regular dict if desired
    date_values = dict(date_values)

    return jsonify(date_values)



## returns all the stations with their name

@app.route("/api/v0.1/station")
def station_list():

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # query 'station' table
    results = session.query(station.station \
                            ,station.name \
                            ,station.longitude  \
                            ,station.latitude \
                            ,station.elevation  \
                            ).all()
         
    # close the session               
    session.close()

    stations_list = []
    for id, name, lon, lat, elev   in results:
            station_dict = {}
            station_dict['station_id'] = id
            station_dict['name'] = name
            station_dict['longitude'] = lon
            station_dict['latitude'] = lat
            station_dict['elevation'] = elev

            stations_list.append(station_dict)


    return jsonify(stations_list)

## returns temparature statistics (TMIN, TAVG, TMAX) between a date to specify and the last date available

@app.route("/api/v0.1/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # collect data related to the last year for the most active station from measurment table

    tobs_1y = session.query(measurement.station, measurement.date, measurement.tobs)\
        .filter(measurement.date >= \
                (datetime.strptime(date_most_recent, "%Y-%m-%d")- timedelta(days=366) )\
                )\
        .filter(measurement.station == most_active_station) \
        .group_by(measurement.date)\
        .order_by(measurement.date).all()
    
    
    #create a list to be jsonified, by looping through the result above
    temp_by_date = []

    for station_x, date_x, tobs_x in tobs_1y :
        temp_dict = {}
        temp_dict['station'] = station_x
        temp_dict['Date'] = date_x
        temp_dict['tobs'] = tobs_x

        temp_by_date.append(temp_dict)
           
    session.close()

    return jsonify(temp_by_date)

## returns temparature statistics (TMIN, TAVG, TMAX) between a date to specify and the last date available


@app.route("/api/v0.1/<date_start>")
def start(date_start):

    # from measurment, calculate TMIN, TAVG, TMAX for date greater than the one specified 
    result = session.query(func.min(measurement.tobs)\
                    ,func.avg(measurement.tobs)\
                    ,func.max(measurement.tobs))\
                    .filter(measurement.date >= date_start)\
                    .all()
    
    # close the session
    session.close()

    # extract the item to generate the needed dictionary to be jsonified

    tmin, tavg, tmax = result[0]
    return jsonify({'TMIN': tmin,
                   'TAVG': tavg,
                   'TMAX' : tmax
                   })

## returns temparature statistics (TMIN, TAVG, TMAX) between 2 dates to be specified in the API address (start_date and )

@app.route("/api/v0.1/<date_start>/<date_end>")
def start_end(date_start, date_end):

    # set a condition to be sure that dates are consistant

    if date_end > date_start :

        # grop by table measurment, and calculate TMIN, TAVG, TMAX) for each date after filter of dates              
        result = session.query(measurement.date, func.min(measurement.tobs)\
                        ,func.avg(measurement.tobs)\
                        ,func.max(measurement.tobs))\
                        .filter(measurement.date >= date_start)\
                        .filter(measurement.date <= date_end)\
                        .group_by(measurement.date)\
                        .all()

        # close session
        session.close()        
        
        #create a list to be jsonified, by loopong through the result above
 
        stats_by_date = []
        for date_x, tmin, tavg, tmax in result:
            stats_dict = {}
            stats_dict['DATE'] = date_x
            stats_dict['TMIN'] = tmin
            stats_dict['TAVG'] = tavg
            stats_dict['TMAX'] = tmax

            stats_by_date.append(stats_dict)

        return jsonify(stats_by_date)
    
    else : 
        # error message if dates are not consistant
        return 'NEIN!!! DAS IST NICH GUT !!! <br/> \
            <br/> \
            Date_end must be later than start_date. <br/> \
            In other words, you must enter a "date_end" that is after a "date_start". <br/> \
            <br/> \
            Respect the format yyyy-mm-dd'
    

if __name__ == '__main__':
    app.run(debug=True)