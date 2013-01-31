import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import csv
import os
import numpy as np
from collections import Counter

def interpolate(data, newFramerate, oldFramerate):
	xp = []
	x = []
	count = 0
	currentFrame = 0

	extraFrames = -1 + float(newFramerate)/oldFramerate
	extraFrames += extraFrames/(len(data)-1) + 1
	increment = 1./extraFrames
	for value in range(len(data)):
		xp.append(count)
		count+=1
	while currentFrame < xp[-1]:
		x.append(currentFrame)
		currentFrame += increment
	x.append(xp[-1])
	return np.interp(x, xp, data)

def addOneHour(hms):
	''' add one hour in hours, min, sec '''
	hms = 3600+convertToInt(hms)
	return convertToHMS(hms)

def convertTo24(int, cutoff):
	''' adds 12 hours in seconds to int if int is less than cutoff time in hours (meaning it's probably PM)'''
	if int < (cutoff*3600):
		return int+43200
	return int

def convertToInt(hms):
	'''takes a string representing the time as hours:minutes:seconds,
		and converts to an int representing the time as seconds'''
	l = hms.split(':')
	return int(l[0]) * 3600 + int(l[1]) * 60 + int(l[2])

def convertToHMS(int):
	'''takes an integer representing the time in seconds, 
		and converts to a string representing the time as hours:minutes:seconds'''
	hours = int/3600
	minutes = (int - (3600*hours))/60
	seconds = (int - (3600*hours) - (60*minutes))
	if hours-9 < 0:
		hours = '0'+str(hours)
	if minutes-9 <0:
		minutes = '0'+str(minutes)
	if seconds-9 < 0:
		seconds = '0'+str(seconds)
	return "{0}:{1}:{2}".format(hours, minutes, seconds)

def getTimes(path, intervention = False):
	''' get start and end times for all participants from a csv file
		assumes only 1 start and end time per participant,
		unless participant is labeled differently for different instances.
		if more than 1 time for a particular participant, takes later one '''
	with open(path, 'rU') as csvfile:
		edaReader = csv.reader(csvfile)
		timesByPart = {}
		for row in edaReader:
			if row[0] != '':
				if 47 < ord(row[0][0]) < 58:
					# example: timesByPart['21Pre'] = [8:14:14, 8:32:11, Females, '']
					date = row[0].split('/')
					if intervention == False:
						# add one hour because of daylight savings time
						if int(date[0])>10 and int(date[1])>4:
							startTime = row[4]
							try:
								startTime = addOneHour(startTime)
							except:
								pass
							endTime = row[5]
							try:
								endTime = addOneHour(endTime)
							except:
								pass
							timesByPart[row[3]+row[1][0:3]]=[startTime, endTime, row[2],row[6]]
						else:
							timesByPart[row[3]+row[1][0:3]]=row[4:6]+[row[2],row[6]]
					else:
						if int(date[0])>10 and int(date[1])>4:
							startTime = row[2]
							try:
								startTime = addOneHour(startTime)
							except:
								pass
							endTime = row[3]
							try:
								endTime = addOneHour(endTime)
							except:
								pass
							timesByPart[row[1]+'Int']=[startTime, endTime, '', row[5]]
						else:
							timesByPart[row[1]+'Int']=row[2:4]+['',row[5]]
		csvfile.close()
		return timesByPart

def readDataFromFile(path, getStartTime = False):
	''' Opens csv file and returns a tuple of a list of x values and a list of extracted data.
		Assumes all data rows start with a number or a negation, 2nd column of data rows contains a numner,
		and 6th column contains EDA data

		If getStartTime is set to true, also returns the sampling rate and start time.'''
	edaList = []
	xValues = []
	with open(path, 'rU') as csvfile:
		edaFile = csv.reader(csvfile)
		index = 0
		if getStartTime:
			for row in edaFile:
				if row[0][0:4] == 'Samp':
					samplingRate = int(row[0][-1])
				elif row[0][0:5] == 'Start':
					l = row[0].split(' ')
					startTime = convertToInt(l[3])
				elif row[0] != '':
					if 47 < ord(row[0][1]) < 58:
						edaList.append(float(row[5]))
						xValues.append(index)
						index += 1
			csvfile.close()
			return (xValues, edaList, samplingRate, startTime)
		else:
			for row in edaFile:
				if row[0] != '':
					if 47 < ord(row[0][1]) < 58:
						edaList.append(float(row[5]))
						xValues.append(index)
						index += 1
			csvfile.close()
			return (xValues, edaList)

def getStats(data):
	'''returns statistical info about data'''
	normalizedData = normalize(data, max(data))
	return (round(np.mean(data),3),round(np.median(data),3),Counter(data).most_common(1),round(np.std(data),3), \
			round(np.mean(normalizedData),3),round(np.median(normalizedData),3),Counter(normalizedData).most_common(1),round(np.std(normalizedData),3))

def getFiles(dir):
	''' visits all files in directory parameter, and
		returns a list of their locations and their names'''
	files=[]
	fileNames=[]
	arg=None
	def visit(arg,dirname, names):
		try:
			for name in names:
				file=open(dirname+'/'+name, 'r')
				file.close()
				if name != ".DS_Store":
					files.append(dirname+'/'+name)
					fileNames.append(name)
		except:
			pass
	os.path.walk(dir, visit, arg)
	return (files, fileNames)

def getCounselorFiles(dir):
	''' visits all counselor files in directory parameter, and
	returns a list of their locations and their names'''
	files=[]
	fileNames=[]
	arg=None
	def visit(arg,dirname, names):
		try:
			for name in names:
				if 47 < ord(name[0]) < 58:
					file=open(dirname+'/'+name, 'r')
					file.close()
					files.append(dirname+'/'+name)
					fileNames.append(name)
				if name == "readme.txt":
					files.append(dirname+'/'+name)
					fileNames.append(name)
		except:
			pass
	os.path.walk(dir, visit, arg)
	return (files, fileNames)

def getStudentFiles(dir):
	''' visits all student files in directory parameter, and
	returns a list of their locations and their names'''
	files=[]
	fileNames=[]
	arg=None
	def visit(arg,dirname, names):
		try:
			for name in names:
				if name[0] == "P" and name[-3:] == "csv":
					file=open(dirname+'/'+name, 'r')
					file.close()
					files.append(dirname+'/'+name)
					fileNames.append(name)
				if name == "readme.txt":
					files.append(dirname+'/'+name)
					fileNames.append(name)
		except:
			pass
	os.path.walk(dir, visit, arg)
	return (files, fileNames)

def normalize(v, vmax):
	''' takes an array and it's max element, and returns
		a normalized version '''
	if vmax != 0 and vmax != 0.:
		return [round(v[i]/vmax, 3) for i in range(len(v))]
	else:
		return v

def smooth(array, factor):
	''' averages every factor elements in array to smooth it out'''
	if factor != 0 and factor != 0. and factor != 1 and factor != 1.:
		newArray = array[:]
		for location in range(len(newArray)/factor):
			if newArray:
				mean = plt.np.mean(newArray[location*factor:location*factor+factor])
			else:
				mean = 0
			for num in range(factor):
				newArray[location*factor + num] = round(mean, 3)
		if newArray[(len(newArray)/factor)*factor:len(newArray)]:
			lastMean = plt.np.mean(newArray[(len(newArray)/factor)*factor:len(newArray)])
		else:
			lastMean = 0.
		for num in range((len(newArray)/factor)*factor, len(newArray)):
			newArray[num] = round(lastMean, 3)
		return newArray
	else:
		return array

def standardizeTime(dataList):
	''' standarize length of each array in dataList '''
	maxLen = max([len(x) for x in dataList])
	for data in dataList:
		data.extend([0 for x in range(maxLen - len(data))])