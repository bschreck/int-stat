import fileHelperFunc
import csv
import numpy as np
from collections import Counter

def align(newName, fileData, xValues, data, startTime, endTime, edaStartTime, samplingRate, statData = None, startTime2 = None, endTime2 = None, gender = None, extraInfo = None):
	# check if we have a start time, because in one instance the start and end times were not recorded
	if startTime:

		# convert integer startTime to hours, min, sec
		hmsStart = fileHelperFunc.convertToHMS(startTime)

		# case where human-recorded start time is before logger file EDA-recorded start time
		if edaStartTime > startTime:
			addSamples = (edaStartTime - startTime) * samplingRate
			newXValues = [x for x in range(len(xValues)+addSamples)]

			# we prepend with zero's to align file
			newData = ([0]*addSamples) + data

			# 2 part case
			if startTime2:
				part2Data = newData[(startTime2-startTime)*samplingRate:]
				newData = newData[:(endTime-startTime)*samplingRate]
		# case where human-recorded start time is after logger file EDA-recorded start time
		else:

			# we remove some samples to align file
			cutoff = (startTime - edaStartTime) * samplingRate
			newData = data[cutoff:]
			newXValues = [x-cutoff for x in xValues[cutoff:]]

	# if no recorded start time
	else:
		hmsStart = None
		newData = data
		newXValues = xValues

	if endTime and not endTime2:

		# convert interger endTime to hours, min, sec
		hmsEnd = fileHelperFunc.convertToHMS(endTime)
		# human-recorded ending sample
		edaEndSample = edaStartTime*samplingRate + len(xValues)
		# logger-recorded ending sample
		endSample = endTime*samplingRate

		startSample = startTime*samplingRate

		# case where human-recorded end time is after logger file EDA-recorded end time
		if endSample > edaEndSample:
			addSamples = endSample - edaEndSample

			# we append zero's to align file
			newData.extend([0 for x in range(addSamples)])
			newXValues.extend([x+len(newXValues) for x in range(addSamples)])
		
		# case where human-recorded end time is before logger file EDA-recorded end time		
		else:

			# we remove samples to align file
			newData = newData[:endSample - startSample]
			newXValues = newXValues[:endSample - startSample]

	# if no endTime recorded
	else:
		hmsEnd = None

	# set duration in hours, min, sec
	if endTime and startTime:
		hmsDuration = fileHelperFunc.convertToHMS(endTime-startTime)
	else:
		hmsDuration = None

	# case where two parts of data
	if endTime2:
		hmsEnd = fileHelperFunc.convertToHMS(endTime2)
		hmsDuration = fileHelperFunc.convertToHMS(endTime2-startTime)
		edaEndSample = edaStartTime*samplingRate + len(xValues)
		endSample = endTime2*samplingRate
		addSamples = endSample - edaEndSample
		newData.extend([0 for x in range(addSamples)])
		newXValues.extend([x+len(newXValues) for x in range(addSamples)])

	# record new aligned data and statistics into dictionary
	fileData[newName] = [newXValues, newData, samplingRate, hmsStart, hmsEnd, hmsDuration, gender, extraInfo, statData]

def getDataTimes(intFile, prePosFile, dir):
	''' # extract EDA data from directory
		assumes spreadsheets of start and finish times are located in a separate directory from the actual data
		also assumes EDA data files are named 'participantnumberTestModality.csv', where participant number is a 2 digit integer,
		    Test is one of Int, Pre, or Pos, and Modality is either l or r
		returns a dictionary keyed by participant number, and containing aligned eda values with times, sampling rate,
		    start time, and any additional info specified by the time table '''
	# get dictionaries of start and end times for each log file recorded
	intTimes = fileHelperFunc.getTimes(intFile, True)
	prePosTimes = fileHelperFunc.getTimes(prePosFile)

	# search directory for log files
	(files, fileNames) = fileHelperFunc.getFiles(dir)

	# initialize dictionary to store all the data and it's associated statistics
	fileData = {}

	# loop through each file
	for index in range(len(files)):

		# partNumber is the participant number
		# test is one of ava, pre, and post
		# newName converts all partNumbers to 2 digits in the name referenced

		# for 2-digit file indices
		if fileNames[index][1] != '_':
			partNumber = fileNames[index][0:2]
			test = fileNames[index][3:6]
			newName = fileNames[index]

		# for 1-digit file indices
		else:
			partNumber = fileNames[index][0]
			test = fileNames[index][2:5]
			newName = '0'+fileNames[index]

		# initialize variables for case where data split into two parts
		startTime2 = None
		endTime2 = None

		if test == "ava":
			startTime = fileHelperFunc.convertToInt(intTimes[partNumber+'Int'][0])
			startTime = fileHelperFunc.convertTo24(startTime,8)
			endTime = fileHelperFunc.convertToInt(intTimes[partNumber+'Int'][1])
			endTime = fileHelperFunc.convertTo24(endTime,8)

			# 77 has two parts, and we need to take out the middle
			if partNumber == '77':
				startTime2 = fileHelperFunc.convertToInt(intTimes['77 part 2Int'][0])
				startTime2 = fileHelperFunc.convertTo24(startTime2,8)
				endTime2 = fileHelperFunc.convertToInt(intTimes['77 part 2Int'][1])
				endTime2 = fileHelperFunc.convertTo24(endTime2,8)
			gender = intTimes[partNumber+'Int'][2]
			extraInfo = intTimes[partNumber+'Int'][3]

		elif test == "pre":
			startTime = fileHelperFunc.convertToInt(prePosTimes[partNumber+'Pre'][0])
			startTime = fileHelperFunc.convertTo24(startTime,12)
			endTime = fileHelperFunc.convertToInt(prePosTimes[partNumber+'Pre'][1])
			endTime = fileHelperFunc.convertTo24(endTime,12)
			gender = prePosTimes[partNumber+'Pre'][2]
			extraInfo = prePosTimes[partNumber+'Pre'][3]

		elif test == "pos":
			# there was one case where start and end times weren't recorded, so in that case we set them to None
			if prePosTimes[partNumber+'Pos'][0]:
				startTime = fileHelperFunc.convertToInt(prePosTimes[partNumber+'Pos'][0])
				startTime = fileHelperFunc.convertTo24(startTime,12)
			else:
				startTime = None
			if prePosTimes[partNumber+'Pos'][1]:
				endTime = fileHelperFunc.convertToInt(prePosTimes[partNumber+'Pos'][1])
				endTime = fileHelperFunc.convertTo24(endTime,12)
			else:
				endTime = None
			gender = prePosTimes[partNumber+'Pos'][2]
			extraInfo = prePosTimes[partNumber+'Pos'][3]

		# get data from the log file
		(xValues, data, samplingRate, edaStartTime) = fileHelperFunc.readDataFromFile(files[index], getStartTime = True)
		# get statistics from the data
		statData = fileHelperFunc.getStats(data)
		align(newName, fileData, xValues, data, startTime, endTime, edaStartTime, samplingRate, statData, startTime2, endTime2, gender, extraInfo)
	return fileData
		# Align data according to start and end times on timetable spreadsheet:

def consolidate(fileData):
	# consolidate data for different versions of same participant into one dictionary entry
	ConsFileData = {}

	# initialize format of dictionary entries
	for data in fileData:
		if data[:2] not in ConsFileData:
			ConsFileData[data[:2]] = ['precl', 'precr', 'presl', 'presr', 'poscl', 'poscr', 'possl', 'possr', 'intl', 'intr']


	for data in fileData:
		# file name is 'partNum_pre_cl'
		if data[3:6] == 'pre' and data[-6] == 'c' and data[-5] == 'l':
			ConsFileData[data[:2]][0] = fileData[data]

		# file name is 'partNum_pre_cr'
		elif data[3:6] == 'pre' and data[-6] == 'c':
			ConsFileData[data[:2]][1] = fileData[data]

		# file name is 'partNum_pre_sl'
		elif data[3:6] == 'pre' and data[-5] == 'l':
			ConsFileData[data[:2]][2] = fileData[data]

		# file name is 'partNum_pre_sr'
		elif data[3:6] == 'pre':
			ConsFileData[data[:2]][3] = fileData[data]

		# file name is 'partNum_pos_cl'
		elif data[3:6] == 'pos' and data[-6] == 'c' and data[-5] == 'l':
			ConsFileData[data[:2]][4] = fileData[data]

		# file name is 'partNum_pre_cr'
		elif data[3:6] == 'pos' and data[-6] == 'c':
			ConsFileData[data[:2]][5] = fileData[data]

		# file name is 'partNum_pos_cl'
		elif data[3:6] == 'pos' and data[-5] == 'l':
			ConsFileData[data[:2]][6] = fileData[data]

		# file name is 'partNum_pos_cr'
		elif data[3:6] == 'pos':
			ConsFileData[data[:2]][7] = fileData[data]

		# file name is 'partNum_avatar_pl'
		elif data[-5] == 'l':
			ConsFileData[data[:2]][8] = fileData[data]

		# file name is 'partNum_avatar_pr'
		else:
			ConsFileData[data[:2]][9] = fileData[data]

	return ConsFileData

def sortKeys(data):
	# sorts participant numbers
	intKeys = [int(x) for x in data.keys()]
	intKeys.sort()
	sortedKeys = []
	for x in intKeys:
		if x < 10:
			sortedKeys.append('0'+str(x))
		else:
			sortedKeys.append(str(x))
	return sortedKeys

def logDataStats(data):
	''' takes dictionary containing data keyed by participant number,
		and writes data about each participant to a file '''
	with open('Statistics'+'.csv', 'wb') as csvFile:
			writer = csv.writer(csvFile)

			writer.writerow(['Participant Number', 'Pre/Post/Intervention', 'Student/Counselor', 'Modality', \
							'Sampling Rate', 'Start Time', 'End Time', 'Duration', 'Gender', 'Extra Info',\
							'Mean', 'Median', 'Mode', 'Standard Deviation', \
							'Normalized Mean', 'Normalized Median', 'Normalized Mode', 'Normalized Standard Deviation'])

			wordTranspose = {'pre':'Pre', 'pos':'Post','int':'Intervention', 'c':'Counselor', 's':'Student', 'l':'Left', 'r':'Right'}
			types = ['precl', 'precr', 'presl', 'presr', 'poscl', 'poscr', 'possl', 'possr', 'intl', 'intr']

			sortedKeys = sortKeys(data)
			# for each participant
			for participant in sortedKeys:	
				# for each type of data	
				for index in range(len(data[participant])):
					# if data is there, and not the string placeholder
					if type(data[participant][index]) != str:
						#EDAData = data[participant][index][1]
						#if not EDAData:
						#	EDAData = [0]
							#normalizedEDAData = [0]

						# Labeling all intervention files as student
						if index > 7:
							partType = 'Student'
						else:
							#normalizedEDAData = fileHelperFunc.normalize(EDAData, max(EDAData))
							partType = wordTranspose[types[index][3]]
						writer.writerow([participant, wordTranspose[types[index][0:3]], partType, wordTranspose[types[index][-1]]]+\
										[data[participant][index][x] for x in range(2,8)]+\
										[data[participant][index][8][x] for x in range(8)])
					else:
						if index > 7:
							partType = 'Student'
						else:
							partType = wordTranspose[types[index][3]]
						writer.writerow([participant, wordTranspose[types[index][0:3]], partType, wordTranspose[types[index][-1]]]+[None]*14)

def logInterpolateMultipleFiles(data, fps):
	''' interpolates data to fps and logs each participant's set of data (pre, pos, int) to a file'''
	sortedKeys = sortKeys(data)
	for participant in sortedKeys:	
		with open('participants/'+participant+'.csv', 'wb') as csvFile:
		 	writer = csv.writer(csvFile)

			columns = [['precl'], ['precr'], ['presl'], ['presr'], ['poscl'], ['poscr'], ['possl'], ['possr'], ['intl'], ['intr']]
			# for each type of data	
			for index in range(10):
				# if data is there, and not the string placeholder
				if type(data[participant][index]) != str:
					EDAData = data[participant][index][1]
					if not EDAData:
						EDAData = [None]
						normalizedEDAData = [None]
						interNormalizedEDAData = [None]
					else:
						normalizedEDAData = fileHelperFunc.normalize(EDAData, max(EDAData))
						interNormalizedEDAData = fileHelperFunc.interpolate(normalizedEDAData, fps, data[participant][index][2])
					# Labeling all intervention files as student
					columns[index].extend(interNormalizedEDAData)
			for index in columns:
				index.extend([None for x in range(max([len(column) for column in columns]))])

			writer.writerow(['Participant = %s' % participant])
			writer.writerows(zip(columns[0], columns[1], columns[2], columns[3], columns[4], columns[5], columns[6], columns[7], columns[8], columns[9]))