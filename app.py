#################################################
# Import dependencies
#################################################
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

import datetime as dt
import numpy as np
import pandas as pd

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Measurements=Base.classes.measurement
Stations=Base.classes.station


#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def home():
    """List all available api routes."""   
    return (
        f"Available Routes:<br/>"
        f"<br/>"
        f"* List rain totals for the previous year<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"<br/>"
        f"* List all stations<br/>"
        f"/api/v1.0/stations<br/>"
        f"<br/>"
        f"* List all temperature observations (TOBS) for the previous year<br/>"
        f"/api/v1.0/tobs<br/>"
        f"<br/>"
        f"* List of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range.<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end><br/>"
        f"Note: Please put the dates in 'YYYY-MM-DD' format :) "
    )


@app.route("/api/v1.0/precipitation")
def prcps():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    """Convert the query results to a dictionary using date as the key and prcp as the value.
        Return the JSON representation of your dictionary."""
    # Calculate the date 1 year ago from the last data point in the database
    last_date = session.query(func.max(Measurements.date)).scalar()
    year_ago = dt.datetime.strptime(last_date, '%Y-%m-%d').date() - dt.timedelta(days=365)
    
    # Query date and precipitation
    result = session.query(Measurements.date, Measurements.prcp).\
                        filter(Measurements.date > year_ago).\
                        order_by(Measurements.date).all()
    
    session.close()
    
    # Create a dictionary from the row data and append to a list of all_passengers
    rainfall_dict={}
    for date, prcp in result:
        rainfall_dict[date] = prcp

    return jsonify(rainfall_dict)


@app.route("/api/v1.0/stations")
def station():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    """Return a list of all stations"""
    # Query all passengers
    station_list = session.query(Stations.station).all()
    session.close()
    
    # Convert list of tuples into normal list
    all_stations = list(np.ravel(station_list))

    return jsonify(all_stations)



@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    """Query the dates and temperature observations of the most active station for the last year of data.
        Return a JSON list of temperature observations (TOBS) for the previous year."""
    # Retreive the latest date present in the database
    last_date = session.query(func.max(Measurements.date)).scalar()
    year_ago = dt.datetime.strptime(last_date, '%Y-%m-%d').date() - dt.timedelta(days=365)
    
    # Query the most active station
    sel = [Measurements.station,
           func.count(Measurements.station)]
    
    stations = session.query(*sel).\
                    group_by(Measurements.station).\
                    order_by(func.count(Measurements.station).desc()).all()
    
    most_active_station = stations[0][0]
    
    # Query the dates and temperature observations of the most active station for the last year of data.
    tobs = session.query(Measurements.date, Measurements.tobs).\
                    filter(Measurements.station == most_active_station).\
                    filter(Measurements.date > year_ago).\
                    order_by(Measurements.date.desc()).all()
    
    session.close()
    
    # Create a dictionary from the row data and append to a list
    temp_list=[]
    temp_dict={}
    for temp in tobs:
        temp_dict = {"date": temp[0], "tobs": temp[1]}
        temp_list.append(temp_dict)
    
    return jsonify(temp_list)



@app.route('/api/v1.0/<start>')
@app.route('/api/v1.0/<start>/<end>')
def dates(start = None, end = None):
    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    """Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range.
    When given the start only, calculate TMIN, TAVG, and TMAX for all dates greater than and equal to the start date.
    When given the start and the end date, calculate the TMIN, TAVG, and TMAX for dates between the start and end date inclusive."""
    
    # Query minimum temperature, the average temperature, and the max temperature
    sel=[func.min(Measurements.tobs), func.avg(Measurements.tobs), func.max(Measurements.tobs)]
    
    # if the end date exists
    if end != None:
        temperature = session.query(*sel).filter(Measurements.date >= start).filter(Measurements.date <= end).all()
    # if the end date does not exist
    else:
        temperature = session.query(*sel).filter(Measurements.date >= start).all()

    session.close()
    
    # Create a dictionary from the row min, avg and max temperature
    for temps in temperature:
        temp_dict = {"Min Temp" : temps[0], "Avg Temp" : temps[1], "Max Temp" : temps[2]}
        
    return jsonify(temp_dict)
    

if __name__ == '__main__':
    app.run(debug=True)



