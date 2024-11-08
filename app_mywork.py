# Import the dependencies.

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

import numpy as np

from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta

from flask import Flask, jsonify


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
# print(Base.classes.keys())

# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#to check
# print(session.query(measurement).first().__dict__)
# print(session.query(station).first().__dict__)


#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Welcome to the hawaii meteo API! <br/>"
        f"  <br/>"
        f"Available Routes:<br/>"
        f"  <br/>"
        f"precipitation full data : /api/v0.1/all_precipitation <br/>"
        f"precipitation of the last year : /api/v0.1/precipitation_1Y <br/>"
        f"All the stations : /api/v0.1/station <br/>"
        f"Temperatures of the last year for the most active station : /api/v0.1/tobs <br/>"
        f"/api/v0.1/start <br/>"
        f"/api/v0.1/start_end <br/>"
        )

@app.route("/api/v0.1/all_precipitation")
def precipitation():

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # query for precipitation
    results = session.query(measurement.date, \
                            measurement.prcp).all()

           
    
    precipitation_res = list(np.ravel(results))

    return jsonify(precipitation_res)


@app.route("/api/v0.1/precipitation_1y")
def precipitation_1y():

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # query for precipitation

    date_most_recent = session.query(measurement.date).order_by(measurement.date.desc()).first()
    date_most_recent = date_most_recent.date 
    date_most_recent = datetime.strptime(date_most_recent, '%Y-%m-%d')
    date_1y_ago = date_most_recent - relativedelta(years=1)
    date_1y_ago = date_1y_ago.strftime('%Y-%m-%d')
    
    result_1y = session.query(measurement.date, measurement.prcp)\
    .filter(measurement.date >= date_1y_ago)\
    .order_by(measurement.date).all()
         
    
    precipitation_res_1y = list(np.ravel(result_1y))

    return jsonify(precipitation_res_1y)


@app.route("/api/v0.1/station")
def station_list():

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # query for precipitation
    results = session.query(station.station, \
                            station.name).all()

           
    
    station_result = list(np.ravel(results))

    return jsonify(station_result)



@app.route("/api/v0.1/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # query for temperatures

    date_most_recent = session.query(measurement.date).order_by(measurement.date.desc()).first()
    date_most_recent = date_most_recent.date 
    date_most_recent = datetime.strptime(date_most_recent, '%Y-%m-%d')
    date_1y_ago = date_most_recent - relativedelta(years=1)
    date_1y_ago = date_1y_ago.strftime('%Y-%m-%d')
    station_active = session.query(measurement.station, \
                func.count(measurement.station)).\
                group_by(measurement.station).\
                order_by(func.count(measurement.station).desc())\
                .all()
    most_active_station = station_active[0][0]
    result_1y = session.query(measurement.date, measurement.tobs)\
            .filter(measurement.date >= date_1y_ago)\
            .filter(measurement.station == most_active_station) \
            .group_by(measurement.date)\
            .order_by(measurement.date).all()
    
    temperature_1y = list(np.ravel(result_1y))

    return jsonify(temperature_1y)


# @app.route("/")
# def start():

# @app.route("/")
# def start_end():

if __name__ == "__main__":
    app.run(debug=True)