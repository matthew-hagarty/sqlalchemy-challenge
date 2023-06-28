from flask import Flask, jsonify
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect
import pandas as pd
import datetime as dt


#################################################
# Database Setup
#################################################

# reflect an existing database into a new model

    # create engine to hawaii.sqlite
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
    # use automap_base()
Base = automap_base()
Base.prepare(autoload_with=engine)

# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    return(
        f"Welcome to the Surf's Up API! <br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation (Returns a json of the last 12 months of precipitation data)<br/>"
        f"/api/v1.0/stations (Returns a json list of stations)<br/>"
        f"/api/v1.0/tobs (Returns a json list of temperature observations for the previous year of the most active station)<br/>"
        f"/api/v1.0/start_date (Returns minimum, maximum and average temperatures from your date (on or after 2010-01-01) until the end date, 2017-08-23)<br/>"
        f"/api/v1.0/start_date/end_date (Returns min, max, and avg temperatures for your choice of dates, between 2010-01-01 and 2017-08-23)<br/>"
        f"*Note: for dates, date must be in format yyyy-mm-dd<br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Copied code from the Jupyter notebook where the code for this already existed
    last_date = session.query(func.max(measurement.date)).all()

    ## Design a query to retrieve the last 12 months of precipitation data and plot the results. 
    # Starting from the most recent data point in the database. 
    end_date = dt.date.fromisoformat(last_date[0][0])

    # Calculate the date one year from the last date in data set.
    begin_date = end_date - dt.timedelta(days=365)

    # Perform a query to retrieve the data and precipitation scores
    precipitation = session.query(measurement.date, measurement.prcp).filter(measurement.date >= begin_date).filter(measurement.date <= end_date).all()

    # Save the query results as a Pandas DataFrame. Explicitly set the column names
    prcp_df = pd.DataFrame(data=precipitation, columns = ['Date', 'Precipitation'])

    # Sort the dataframe by date
    prcp_df = prcp_df.sort_values(['Date'], ascending=True).reset_index(drop=True)

    # Change date to be the index    
    prcp_df.set_index('Date', inplace=True)

    # create a dictionary and jsonify it
    prcp_dict = jsonify(prcp_df.to_dict()['Precipitation'])

    # return the json
    return(prcp_dict)

@app.route("/api/v1.0/stations")
def stations():
    # Return a JSON list of stations from the dataset
    # Query the stations
    station_query = session.query(station.station).all()
    # Append them to a jsonifiable list
    list_of_stations = [station_query[x][0] for x in range(len(station_query))]
    return(jsonify(list_of_stations))

@app.route("/api/v1.0/tobs")
def tobs():
    # Query the dates and temperature observations of the most-active station for the previous year of data
    # Design a query to find the most active stations (i.e. which stations have the most rows?)
    sel = [measurement.station, func.count(measurement.id)]
    active_stations = session.query(*sel).group_by(measurement.station).order_by(func.count(measurement.id).desc()).all()
    most_active_station = active_stations[0][0]
    # We can now find the specific measurements at said station
    station_tobs = session.query(func.min(measurement.tobs), func.max(measurement.tobs), func.avg(measurement.tobs)).\
        filter(measurement.station == most_active_station).filter(measurement.date >= '2016-08-23').filter(measurement.date <= '2017-08-23').all()
    return(f"The minimum temperature over the last year of data was {station_tobs[0][0]} degrees. <br/>"
           f"The maximum temperature over the last year of data was {station_tobs[0][1]} degrees. <br/>"
           f"The average temperature over the last year of data was {station_tobs[0][2]} degrees. <br/>")

@app.route("/api/v1.0/<start>")
def tobs_start(start):
    # For a specified start, calculate TMIN, TAVG, and TMAX for all the dates greater than or equal to the start date
    # Pretty much the same as station_tobs above, except filter for a specific date
    overall_tobs = session.query(func.min(measurement.tobs), func.max(measurement.tobs), func.avg(measurement.tobs)).\
        filter(measurement.date >= start).all()
    # And print out the results
    return(f"The minimum temperature since {start} was {overall_tobs[0][0]} degrees. <br/>"
           f"The maximum temperature since {start} was {overall_tobs[0][1]} degrees. <br/>"
           f"The average temperature since {start} was {overall_tobs[0][2]} degrees. <br/>")

@app.route("/api/v1.0/<start>/<end>")
def tobs_start_end(start, end):
    # For a specified start date and end date, calculate TMIN, TAVG, and TMAX for the dates from the start date to the end date, inclusive.
    # Almost exactly the same as tobs_start except another filter
    start_end_tobs = session.query(func.min(measurement.tobs), func.max(measurement.tobs), func.avg(measurement.tobs)).\
        filter(measurement.date >= start).filter(measurement.date <= end).all()
    #And print out the results
    return(f"The minimum temperature between {start} and {end} was {start_end_tobs[0][0]} degrees. <br/>"
           f"The maximum temperature between {start} and {end} was {start_end_tobs[0][1]} degrees. <br/>"
           f"The average temperature between {start} and {end} was {start_end_tobs[0][2]} degrees. <br/>")










if __name__ == "__main__":
    app.run(debug=True)
