#!/bin/python

import mysql.connector
import pprint
import timeit
from progressbar import ProgressBar, Bar, ReverseBar, ETA

def getTerminalSize():
    import os
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
        '1234'))
        except:
            return
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (env.get('LINES', 25), env.get('COLUMNS', 80))

        ### Use get(key[, default]) instead of a try/catch
        #try:
        #    cr = (env['LINES'], env['COLUMNS'])
        #except:
        #    cr = (25, 80)
    return int(cr[1]), int(cr[0])

oldDatabaseConfig = {
  'user': 'root',
  'password': '***',
  'host': '127.0.0.1',
  'database': 'test-schema',
  'raise_on_warnings': True,
}

newDatabaseConfig = {
  'user': 'root',
  'password': '***',
  'host': '127.0.0.1',
  'database': 'kiosk',
  'raise_on_warnings': True,
}

pp = pprint.PrettyPrinter(indent=4)
start = timeit.default_timer()

all_sports = ("SELECT * FROM `sport`;")

all_teams = ("SELECT * FROM `team`;")

all_participation = """SELECT * FROM `athletesportparticipation` WHERE AthleteID = {t};"""

get_athlete_count = ("SELECT COUNT(*) FROM `athlete`;")

get_team_count = ("SELECT COUNT(*) FROM `team`;")

get_new_athlete_id = ("SELECT `entity_id` FROM `athlete` ORDER BY `entity_id` DESC LIMIT 1;")

get_new_image_id = ("SELECT `media_id` FROM `image` ORDER BY `media_id` DESC LIMIT 1;")

get_new_video_id = ("SELECT `media_id` FROM `video` ORDER BY `media_id` DESC LIMIT 1;")

get_new_audio_id = ("SELECT `media_id` FROM `audio` ORDER BY `media_id` DESC LIMIT 1;")

get_new_text_id = ("SELECT `media_id` FROM `text` ORDER BY `media_id` DESC LIMIT 1;")

add_participation = """INSERT INTO `participation`(`athlete_id`, `sport_id`, `role`, `start`, `end`) VALUES ({aid}, {sid}, {role}, {start}, {end});"""

add_team = """INSERT INTO `team`(`sport_id`, `year`) VALUES ({sid}, {year});"""

add_association = """INSERT INTO `media_association`(`entity_id`, `media_id`) VALUES ({eid}, {mid});"""

add_image = """INSERT INTO `image`(`path`, `title`, `caption`, `width`, `height`, `size`) VALUES ("{path}", {title}, {caption}, {width}, {height}, {size});"""

add_video = """INSERT INTO `video`(`path`, `title`, `caption`, `width`, `height`, `length`, `size`) VALUES ("{path}", {title}, {caption}, {width}, {height}, {length}, {size});"""

add_athlete = ("INSERT INTO `athlete` "
	"	(`title`, `first_name`, `middle_name`, `last_name`, `gender`, `hof_induction_year`)"
	"VALUES "
	"	(%s, %s, %s, %s, %s, %s);")

oldQueryAllAthletes = ("SELECT * FROM `test-schema`.athlete")

oldData = mysql.connector.connect(**oldDatabaseConfig)
oldData1 = mysql.connector.connect(**oldDatabaseConfig)
newData = mysql.connector.connect(**newDatabaseConfig)

oldCursor = oldData.cursor()
oldCursor1 = oldData1.cursor()

newCursor = newData.cursor()

sportTable = {}
(cWidth, cHeight) = getTerminalSize()
widgets = [Bar('>'), ' ', ETA(), ' ', ReverseBar('<')]

newCursor.execute(all_sports)

for(id, shortName, fullName, gender) in newCursor:
	sportTable[fullName] = id

# pp.pprint(sportTable)


# Make a quick and dirty sportID translation table
oldCursor.execute(all_sports)
for(id, name, gender, order, bg, spbg) in oldCursor:
	if name == 'Rifle Team':
		sportTable[id] = sportTable["Men's Rifle"]
	elif name == "Women's Softball":
		sportTable[id] = sportTable["Softball"]
	elif name == "Archery":
		sportTable[id] = sportTable["Women's Archery"]
	elif name == "Boxing":
		sportTable[id] = sportTable["Men's Boxing"]
	elif name == "Polo":
		sportTable[id] = sportTable["Men's Polo"]
	elif name == "Athletic Games":
		sportTable[id] = sportTable["Women's Athletic Games"]
	elif name in ['Head Coaching', 'Assistant Coaching']:
		continue
	else:
		sportTable[id] = sportTable[name]

# pp.pprint(sportTable)

print()
print("Starting database conversion...")
print("WARNING! Resize window events interupt system calls and crash process!")
print()



counts = {
	'processedAthletes': 0,
	'failures': 0,
	'blankTitles': 0,
	'blankMiddles': 0,
	'coachingTitles': 0,
	'successes': 0,
	'psuccesses': 0,
	'pfailures': 0,
	'coachingParts': 0,
	'badParts': 0,
	'pnoDates': 0,
	'tsuccesses': 0,
	'tfailed': 0,
	'blankUclaPhoto': 0,
	'uclaPhotoFailures':0,
	'uclaPhotoSuccesses':0,
	'identicalPostPhoto': 0,
	'blankPostPhoto': 0,
	'postPhotoSuccesses': 0,
	'postPhotoFailures': 0,
	'uclaVideoSuccesses': 0,
	'uclaVideoFailures': 0,
	'blankUclaVideo': 0,
	'postVideoSuccesses': 0,
	'postVideoFailures': 0,
	'blankPostVideo': 0,
	'identicalPostVideo': 0,
	'weirdVBVideo': 0
}

oldCursor.execute(get_team_count)
(num_teams, ) = oldCursor.fetchone()
num_teams *= 10
pbar = ProgressBar(num_teams, widgets=widgets).start()

oldCursor.execute(all_teams)
for(tid, year, sid, displayName, story, roster, photo, video) in oldCursor:
	pbar.update(10*(counts['tsuccesses']+counts['tfailed'])+1)
	newSportID = sportTable[sid]

	try:
		newTeam_query = add_team.format(sid = newSportID, year= year)
		newCursor.execute(newTeam_query)
		newData.commit()
	except mysql.connector.Error as err:
		print("{}".format(err))
		counts['tfailed'] += 1
		continue

	counts['tsuccesses'] += 1

pbar.finish()

oldCursor.execute(get_athlete_count)
(num_athletes, ) = oldCursor.fetchone()
num_athletes *= 10
pbar = ProgressBar(num_athletes, widgets=widgets).start()

oldCursor.execute(oldQueryAllAthletes)
weirdPeople = []

for(oaid, title, firstName, middleName, lastName, gender, uclaPhoto, postPhoto, uclaVideo, postVideo, uclaStory, postStory, hof, hofDate) in oldCursor:
	pbar.update(10*counts['processedAthletes']+1)

	if gender == 'Female':
		newGender = 'F'
	else:
		newGender = 'M'

	newTitle = title
	if newTitle == '':
		newTitle = None
		counts['blankTitles'] += 1
	elif newTitle in ['Coach', 'Asst. Coach']:
		newTitle = None
		counts['coachingTitles'] += 1

	newMiddle = middleName
	if middleName == '':
		newMiddle = None
		counts['blankMiddles'] += 1

	# print("{} {} {} {} {}".format(newTitle, firstName, newMiddle,lastName,hofDate))
	try:
		newCursor.execute(add_athlete, (newTitle, firstName, newMiddle, lastName, newGender, hofDate))
		newData.commit()
		counts['successes'] += 1
	except mysql.connector.Error as err:
		# print("{}".format(err))
		counts['failures'] += 1
		weirdPeople.append([newTitle, firstName, newMiddle, lastName, newGender, hofDate])
		continue
	

	newCursor.execute(get_new_athlete_id)
	for(nAID) in newCursor:
		newAthleteID = nAID[0]

	# print(newAthleteID)

	part_query = all_participation.format(t=oaid)

	oldCursor1.execute((part_query))
	for(aid, sportID, dateStart, dateEnd) in oldCursor1:
		if sportID in [134,245]:
			counts['coachingParts'] += 1
			continue 

		if not sportID in sportTable.keys():
			counts['badParts'] += 1
			continue

		if dateStart == None or dateEnd == None:
			counts['pnoDates'] += 1
			continue

		newSportID = sportTable[sportID]

		try:
			newPart_query = add_participation.format(aid=newAthleteID, sid=newSportID, role="'Athlete'", start="'"+str(dateStart)+"'", end="'"+str(dateEnd)+"'")
			newCursor.execute(newPart_query)
			newData.commit()
		except mysql.connector.Error as err:
			print("{}".format(err))
			counts['pfailures'] += 1
			continue
		counts['psuccesses'] += 1
		# print(newPart_query)

	if uclaPhoto in [None, '']:
		counts['blankUclaPhoto'] += 1
	else:
		try : 
			new_image = add_image.format(path=uclaPhoto, title="'UCLA Photo'", caption='null', width='null', height='null', size='null')
			# print(new_image)
			newCursor.execute(new_image)
			newData.commit()

			newCursor.execute(get_new_image_id)
			(newImageID, ) = newCursor.fetchone()


			new_association = add_association.format(eid=newAthleteID, mid=newImageID)
			newCursor.execute(new_association)
			newData.commit()

			counts['uclaPhotoSuccesses'] +=1

		except mysql.connector.Error as err:
			print("{}".format(err))
			counts['uclaPhotoFailures'] += 1

	if postPhoto in [None, '']:
		counts['blankPostPhoto'] += 1
	elif postPhoto == uclaPhoto:
		counts['identicalPostPhoto'] += 1
	else:
		try : 
			new_image = add_image.format(path=postPhoto, title="'Post UCLA Photo'", caption='null', width='null', height='null', size='null')
			# print(new_image)
			newCursor.execute(new_image)
			newData.commit()

			newCursor.execute(get_new_image_id)
			(newImageID, ) = newCursor.fetchone()

			new_association = add_association.format(eid=newAthleteID, mid=newImageID)
			newCursor.execute(new_association)
			newData.commit()

			counts['postPhotoSuccesses'] +=1

		except mysql.connector.Error as err:
			print("{}".format(err))
			counts['postPhotoFailures'] += 1

	if uclaVideo in [None, '']:
		counts['blankUclaVideo'] += 1
	elif uclaVideo == 'volleyball_highlights.mp4' and counts['weirdVBVideo'] > 0:
		counts['weirdVBVideo'] += 1
	else:
		if uclaVideo == 'volleyball_highlights.mp4':
			counts['weirdVBVideo'] += 1
		try : 
			new_video = add_video.format(path=uclaVideo, title="'UCLA Video'", caption='null', width='null', height='null', length='null', size='null')
			# print(new_image)
			newCursor.execute(new_video)
			newData.commit()

			newCursor.execute(get_new_video_id)
			(newVideoID, ) = newCursor.fetchone()


			new_association = add_association.format(eid=newAthleteID, mid=newVideoID)
			newCursor.execute(new_association)
			newData.commit()

			counts['uclaVideoSuccesses'] +=1

		except mysql.connector.Error as err:
			print("{}".format(err))
			counts['uclaVideoFailures'] += 1

	if postVideo in [None, '']:
		counts['blankPostVideo'] += 1
	elif postVideo == uclaVideo:
		counts['identicalPostVideo'] += 1
	else:
		try : 
			new_video = add_video.format(path=postVideo, title="'Post UCLA Video'", caption='null', width='null', height='null', length='null', size='null')
			# print(new_image)
			newCursor.execute(new_video)
			newData.commit()

			newCursor.execute(get_new_video_id)
			(newVideoID, ) = newCursor.fetchone()


			new_association = add_association.format(eid=newAthleteID, mid=newVideoID)
			newCursor.execute(new_association)
			newData.commit()

			counts['postVideoSuccesses'] +=1

		except mysql.connector.Error as err:
			print("{}".format(err))
			counts['postVideoFailures'] += 1

	counts['processedAthletes'] += 1



pbar.finish()
oldCursor.close()

oldData.close()
newData.close()

stop = timeit.default_timer()

print()
print("*** CONVERSION COMPLETE! ***".center(cWidth))
print(("took " + ("%.2f" % (stop-start))+" seconds").center(cWidth))
print()

print("===/ ATHLETE STATS \===".center(cWidth))
print(("Successful:                " + str(counts['successes'])).center(cWidth))
print(("Failed:                    " + str(counts['failures'])).center(cWidth))
print(("Blank titles converted:    " + str(counts['blankTitles'])).center(cWidth))
print(("Blank middles converted:   " + str(counts['blankMiddles'])).center(cWidth))
print(("Athlete titles suppressed: " + str(counts['coachingTitles'])).center(cWidth))
print()

print("===/ ATHLETE MEDIA \===".center(cWidth))
print(("Successful UCLA Photo:      " + str(counts['uclaPhotoSuccesses'])).center(cWidth))
print(("Failed UCLA Photo:          " + str(counts['uclaPhotoFailures'])).center(cWidth))
print(("Blank UCLA Photo:           " + str(counts['blankUclaPhoto'])).center(cWidth))
print()
print(("Successful Post Photo:      " + str(counts['postPhotoSuccesses'])).center(cWidth))
print(("Failed Post Photo:         " + str(counts['postPhotoFailures'])).center(cWidth))
print(("Identical Post Photo:       " + str(counts['identicalPostPhoto'])).center(cWidth))
print(("Blank Post Photo:           " + str(counts['blankPostPhoto'])).center(cWidth))
print()
print(("Successful UCLA Video:      " + str(counts['uclaVideoSuccesses'])).center(cWidth))
print(("Failed UCLA Video:          " + str(counts['uclaVideoFailures'])).center(cWidth))
print(("Blank UCLA Video:           " + str(counts['blankUclaVideo'])).center(cWidth))
print(("Single Shared VB Video:     " + str(counts['weirdVBVideo'])).center(cWidth))
print()
print(("Successful Post Video:      " + str(counts['postVideoSuccesses'])).center(cWidth))
print(("Failed Photo Video:         " + str(counts['postVideoFailures'])).center(cWidth))
print(("Identical Post Video:       " + str(counts['identicalPostVideo'])).center(cWidth))
print(("Blank Post Video:           " + str(counts['blankPostVideo'])).center(cWidth))
print()

print("===/ ATHLETE PARTICIPATION STATS \===".center(cWidth))
print(("Successful:                 " + str(counts['psuccesses'])).center(cWidth))
print(("Failed:                     " + str(counts['pfailures'])).center(cWidth))
print(("Coaching Parts:             " + str(counts['coachingParts'])).center(cWidth))
print(("Unknown Parts:              " + str(counts['badParts'])).center(cWidth))
print(("Bad Dates:                  " + str(counts['pnoDates'])).center(cWidth))
print()

# print("===/ PROBLEM ATHLETES \===".center(cWidth))
# pp.pprint(weirdPeople)

print("===/ TEAM STATS \===".center(cWidth))
print(("Successful: " + str(counts['tsuccesses'])).center(cWidth))
print(("Failed:     " + str(counts['tfailed'])).center(cWidth))
print()
