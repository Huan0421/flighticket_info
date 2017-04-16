import os
os.system('pip install xlrd')
import xlrd

thebook = xlrd.open_workbook(os.curdir+os.sep+'城市一览表.xlsx')
thesheet = thebook.sheet_by_index(0)
thedict = {}
for i in range(thesheet.nrows):
    thedict[str(thesheet.cell_value(i,0))]=str(thesheet.cell_value(i,1))

import pickle
pickle_file = open(os.curdir+os.sep+'城市一览表.pkl','wb')
pickle.dump(thedict,pickle_file)
pickle_file.close()


