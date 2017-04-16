import pickle
import os

thefile = open(os.curdir+os.sep+'城市一览表.pkl','rb')
thedict = pickle.load(thefile)

def get_cityname(city_name):
    return(thedict[city_name])

