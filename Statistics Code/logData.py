import logDataFunc

# extract EDA data from directory
# and log into csv file with statistical data
# also align data and log each participant's normalized data to a separate file interpolated to 30 fps

intFile = "/Users/Ben/Documents/UROPcode/Actual Stuff/interventionTimeTable.csv"
prePosFile = "/Users/Ben/Documents/UROPcode/Actual Stuff/prePosTimeTable.csv"
dir = "/Users/Ben/Documents/UROPcode/Actual Stuff/OrganizedData"

fileData = logDataFunc.getDataTimes(intFile, prePosFile, dir)
consFileData = logDataFunc.consolidate(fileData)

# log statistics
logDataFunc.logDataStats(consFileData)
# log data
logDataFunc.logInterpolateMultipleFiles(consFileData, 30)
print "Successfully logged data to ./Statistics.csv"