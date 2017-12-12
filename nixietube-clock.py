#!/usr/bin/python

import socket
from time import sleep, time
from subprocess import check_output, call, CalledProcessError
from datetime import datetime, date
from pytz import timezone
import thread

try:
	from mpd import MPDClient, ConnectionError
	mpdClient = MPDClient()
except ImportError:
	print 'python-mpd not installed disabling mpd support.'
	mpdClient = None

try:
	import RPi.GPIO as GPIO
except ImportError:
	print 'python-rpi.gpio not installed using stdout.'
	GPIO = None


#Number of active Nixie Tubes
tubes = 6

# GPIO mapping
gpioData = 11
gpioSerialClock = 12
gpioParallelLoad = 8

# Clock settings
TZ = timezone('US/Eastern')

# MPD Server settings
MPD_HOST = "10.1.1.195"
MPD_PORT = "6600"

# Updates display at most 10fps
FRAME_TIME = 0.25

if (GPIO):
	#Send a pulse out the indicated strobe pin
	def pulseGPIO(pin, direction=True, duration=0.001):
		GPIO.output(pin, direction)
		sleep(duration)
		GPIO.output(pin, not(direction))


	#Display digits on Nixies, bit by bit
	def nixieDigit(digit):
		digit = int(max(0, min( int(digit), 15)))
		for d in reversed(range (0, 4)):
			GPIO.output(gpioData, bool(digit & (1 << d)) )
			pulseGPIO(gpioSerialClock)


	#Display String of digits
	def nixieString(digitString):
		for c in reversed(str(digitString)):
			try:
				nixieDigit(int(c))
			except ValueError:
				nixieDigit(15)
		#Display number on Nixies
		pulseGPIO(gpioParallelLoad)
		#print 'Outputted to Nixies'


	#Init the GPIO pins
	def nixieInit():
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(gpioParallelLoad, GPIO.OUT)
		GPIO.setup(gpioSerialClock, GPIO.OUT)
		GPIO.setup(gpioData, GPIO.OUT)

		GPIO.output(gpioParallelLoad, False)
		GPIO.output(gpioSerialClock, False)
		GPIO.output(gpioData, False)

else:
	import sys
	
	def nixieString(digitString):
		sys.stdout.write('\b' * tubes + str(digitString)[:tubes])
		sys.stdout.flush()


	def nixieInit():
		pass


# returns a string to report the time or date and an expiration time stamp
def dateTimeString( intime ):
#	nixieString( datetime.now().strftime(" %H%M ") )
	TIME_DATE_MAX_OFFSET = len(" HHMMSS CCYY MM DD      ") - tubes
	timeStamp = datetime.fromtimestamp(intime, TZ)
	if dateTimeString.offset > 0 and dateTimeString.offset <= TIME_DATE_MAX_OFFSET:
		dateTimeString.offset += 1
		x = timeStamp.strftime(" %H%M%S %Y %m %d      ")
		return ((x[dateTimeString.offset:dateTimeString.offset+tubes]), intime + 0.2)
	elif timeStamp.second == 13:
		dateTimeString.offset=1
		return (timeStamp.strftime("%H%M%S"), intime + 0.2)
	elif timeStamp.microsecond < 500000:
		return (timeStamp.strftime("%H%M%S"), int(intime)+0.5 )
	else:
		return (timeStamp.strftime("%H%M  "), int(intime + 1) )

dateTimeString.offset = 0


# returns MPD service status string and an expiration time stamp or dateTimeString 
def mpcString(client, intime):
	if(client):
		if (mpcString.mpcHoldoff == 0):
			try:
				status=client.status()
				if(mpcString.oldVolume!=status['volume']):
					mpcString.volumeDisplayTimer = 1 / FRAME_TIME
					mpcString.oldVolume = status['volume']
				if(mpcString.volumeDisplayTimer > 0):
					mpcString.volumeDisplayTimer -= 1
					return ("  "+status['volume'].rjust(2,"0")+"  ", intime+FRAME_TIME);
				#print status
				if(status['state']=="play"):
					#volume = status['volume']
					songid = status['songid']
					timeFields = status['time'].split(":")
					#elTime = int(timeFields[0])
					elMin, elSec = divmod(int(timeFields[0]), 60)
					#totTime = time(second=int(timeFields[1]))
					digitString = songid.rjust(2,"0") + str(elMin).rjust(2," ") + str(elSec).rjust(2,"0")
					#print digitString
					return(digitString, intime + 1)
			except (socket.error, ConnectionError) as e:
				print "ConnectionError:", str(e)
				mpcString.mpcHoldoff = intime + 30
				try:
					client.disconnect()
					#client.connect(MPD_HOST, MPD_PORT)
				except (socket.error, ConnectionError) as e:
					print "Cleanup-ConnectionError:", str(e)
		elif (mpcString.mpcHoldoff <= intime):
			mpcString.mpcHoldoff = 0
			try:
				client.connect(MPD_HOST, MPD_PORT)
			except socket.error as e:
				print "Failed to reconnect MPD client:", str(e)
			return dateTimeString(intime)
	return dateTimeString(intime)

mpcString.oldVolume = 0
mpcString.volumeDisplayTimer = 0
mpcString.mpcHoldoff = 1


if __name__=="__main__":

	emptyString='     '
	keepLooping=True
	currentMsg = ""
	print 'Hit Ctrl-C to Exit'
	try:
		nixieInit()
		if(mpdClient):
			mpdClient.timeout = 1
			#mpdClient.nixieClockConnected = False
			#mpdClient.connect(MPD_HOST, MPD_PORT)
		while keepLooping:
			msg, expiration = mpcString(mpdClient, time())
			#msg, expiration = dateTimeString(time())
			if (msg != currentMsg):
				thread.start_new_thread(nixieString, ( msg, ) )
			sleep(min(1,max(0.001, expiration-time())))

	except:
		# Do normal cleanup
		print "Exception detected"

	#Cleanup...
	print "Exiting..."
	try:
		nixieString('aaaaaa')
	except:
		pass
	if(mpdClient):
		try:
			mpdClient.close()
			mpdClient.disconnect()
		except:
			pass
	if(GPIO):
		try:
			GPIO.cleanup()
		except:
			pass
	print "Done."
