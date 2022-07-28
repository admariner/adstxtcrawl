import datetime
import pytz 
import speech_recognition as sr 
import pyttsx3  
  
# Initialize the recognizer  
r = sr.Recognizer()  

# initiate the class consisting all the date time functions

class DateTime:


#function to tell the current date and current day
	def tell_date(self):
		current_date = datetime.date.today()
		date = current_date.strftime("%B %d, %Y" + " that is " + "%A")
		print(date)
		return self.SpeakText(date)

#function for gettingthe current time

	def tell_time(self):
		current_time = datetime.datetime.now()
		time = current_time.strftime("%H:%M")
		# print(time)

		return self.SpeakText(time)


#function for getting the timein the 12 hr format
	def convert_12_hour_format(self):

		current_time = datetime.datetime.now()
		time = current_time.strftime("%H:%M")
		normal_time = datetime.datetime.strptime(str(time), "%H:%M")
		time = normal_time.strftime("%I:%M %p").lower()

		quarter = normal_time.minute
		hour = normal_time.hour

		if hour == 00:
			if quarter == 15 :
				return self.SpeakText("It is quarter past midnight")
			if quarter == 30:
				return self.SpeakText("It is half past midnight")
			if quarter == 45:
				return self.SpeakText("It is quarter to midnight")

		elif hour == 12:
			if quarter == 15:
				return self.SpeakText(f"It is quarter past {str(hour)}")
			if quarter == 30:
				return self.SpeakText(f"It is half past{str(hour)}")
			if quarter == 45:
				return self.SpeakText(f"It is quarter to{str(hour)}")
		else:
			return self.SpeakText(f"It is{str(time)}")


#function for getting the timezones
	def tell_timezones(self):

		ask_timezone = self.SpeakText("What is your choice of timezone?")

		print("What is your choice of timezone?")

		cmd = self.get_audio()

		print(cmd)

		self.SpeakText(self.UTC())


	def UTC(self):
		UTC = pytz.utc
		# print(datetime_utc)
		return datetime.datetime.now(UTC).strftime("%H:%M")

	def PST(self):
		PST = pytz.timezone('US/Pacific')
		# print(datetime_pst)
		return datetime.datetime.now(PST).strftime("%H:%M")

	def EST(self):
		EST = pytz.timezone('America/New_York')
		# print(datetime_est)
		return datetime.datetime.now(EST).strftime("%H:%M")

	def IST(self):
		IST = pytz.timezone('Asia/Kolkata')
		# print(datetime_ist)
		return datetime.datetime.now(IST).strftime("%H:%M")


# Function to convert text to speech 

	def SpeakText(self, command): 
	    # Initialize the engine 
	    engine = pyttsx3.init() 
	    newVoiceRate = 145
	   	# voices = engine.getProperty('voices')
	    engine.setProperty('volume', 0.7) 
	    engine.setProperty('voice', 4)
	    engine.setProperty('rate',newVoiceRate)
	    engine.say(command)  
	    engine.runAndWait()

#get the audio from the microphone

	def get_audio(self):
		with sr.Microphone() as source:
			audio = r.listen(source)
			said = ""
			try:
			    said = r.recognize_google(audio)
			except Exception as e:
				print("invalid sound")
		return said



# TimeObject = date_time()
# TimeObject.tell_date()
# TimeObject.tell_time()
# TimeObject.convert_12_hour_format()
# TimeObject.tell_timezones()