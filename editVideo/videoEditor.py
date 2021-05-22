from google.cloud import storage, firestore
from urllib.request import urlretrieve
from flask import Flask, request
from RLGoalFrame import findGoal
from datetime import timedelta
import moviepy.editor as mpe 
from pathlib import Path
from time import sleep
import pandas as pd
import random
import os

# uhhh yup this is a web app yup yup mmhmmm
app = Flask(__name__)

def printErrorMessage (exception, path):
	print (f"had trouble editing post")
	print (f"path: {path}")
	print (f"exception: {exception}")

# this function will edit the videos
@app.route('/', methods = ["POST"])
def editPost ():
	# setting up google
	root = Path(__file__).parent
	os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(root, "rltiktok-firebase-adminsdk-68zrf-ec1ecfa21d.json")
	firebase_storage = storage.Client()
	bucket = firebase_storage.bucket("rltiktok.appspot.com")
	firestore_db = firestore.Client().collection (u"post_info")
	
	# just some some feedback
	print ("editing post...")

	# parsing and validating data from the request
	request_data = request.get_data()
	print (request_data)
	try:
		meme = int(request_data ["meme"])

		if "raw_post_url" in request_data:
			re_edit = False
			raw_post_url = request_data ["raw_post_url"]
			image = int(request_data ["image"])
			document = firestore_db.where ("filepath", "==", raw_post_url).limit(1).get()[0]
		else:
			re_edit = True
			source = request_data ["source"]
			document = firestore_db.where ("filepath", "==", source).limit(1).get()[0]
			raw_post_url = document.data.to_dict()["url"]
			image = int (document.data.to_dict()["image"])
				
		if "tolerance1" in request_data:
			tolerance1 = request_data ["tolerance1"]
			tolerance2 = request_data ["tolerance2"]
	except Exception as e:
		print ("error", e)
		return "wrong request format", 400

	# defining paths
	music_path = os.path.join (root, "music")
	goal_path = os.path.join (root, "goalSounds")
	template_path = os.path.join (root, "templates")
	raw_post_path = os.path.join (root, "temp_raw")
	final_video_path = os.path.join (root, "temp_final")

	# downloading the raw video
	for _ in range (0, 5): 
		try:
			urlretrieve(raw_post_url, raw_post_path)
			break 
		except:
			sleep (5)

	# reading songs csv
	songs_info = pd.read_csv(os.path.join(music_path, "musicInfo.csv"))

	# if post is a video
	if (not image):
		# try to open it
		try:
			post = mpe.VideoFileClip(raw_post_path)
		except Exception as e:
			printErrorMessage (e, raw_post_path)
			return -1

		# select and load music to add to clip
		music_selector = random.randint(0, (songs_info.shape[0]-1))
		music = mpe.AudioFileClip(os.path.join (music_path, str(songs_info.at[music_selector, 'name'])))

		if post.duration > 45:
			print ("this clip was too long")
			post.close()
			return -1  

		# check if post is not a meme
		if (not meme):
			# attempt to find the goal
			goal_time = findGoal(raw_post_path, tolerance1, tolerance2) / 30

			# if a goal was found
			if goal_time != 0:
	
				if goal_time > 10:
					prev_duration = post.duration
					post = post.subclip((goal_time - 10), post.duration)
					after_duration = post.duration
					goal_time -= (prev_duration - after_duration)

				#  if post is too long and boring
				if post.duration > 35:
					print ("this clip was too long")
					post.close()
					return -1  

				# select and load an effect to add to goal
				fx_selector = random.randint(0,1)
				fx_sound = mpe.AudioFileClip(os.path.join(goal_path, f'sfx{fx_selector}.mp3')).volumex(0.4)

				# select an load a goal sound to play at goal
				# TO DO: ADD MORE GOAL SOUNDS
				goal_sound = mpe.AudioFileClip(os.path.join(goal_path, 'goal0.mp3')).volumex(0.4)

				# trim the music to drop when the goal is scored
				music = music.subclip(((int(songs_info.at[music_selector, 'dropTime'])) - goal_time), music.duration)

				# add the effects
				music = mpe.CompositeAudioClip([music, goal_sound.set_start(goal_time), fx_sound.set_start(goal_time)])

			# if a goal wasn't found
			else:
				# set up a generic drop time of 5 seconds
				music = music.subclip(((int(songs_info.at[music_selector, 'dropTime'])) - 5), music.duration)

			# resize the post to fill screen
			post = post.resize (height = 1920)
			
		# if a meme
		else:
			post = post.resize (width = 1080)
			if post.duration > 45:
				print ("this clip was too long")
				post.close()
				return -1
			# set the default audio
			if post.audio == None:
				default_audio = music.subclip(((int(songs_info.at[music_selector, 'dropTime'])) - 5), music.duration)
			else:
				default_audio = post.audio

	# post is an image
	else:
		# try to open it
		try:
			post = mpe.ImageClip (raw_post_path).set_fps(30).set_duration(10).resize (width = 1080)
		except Exception as e:
			printErrorMessage(e, raw_post_path)
			return -1

		# select and load music to add to clip
		music_selector = random.randint(0, (songs_info.shape[0]-1))
		music = mpe.AudioFileClip(os.path.join (music_path, str(songs_info.at[music_selector, 'name'])))
		
		 # set up a generic drop time of 5 seconds
		music = music.subclip(((int(songs_info.at[music_selector, 'dropTime'])) - 5), music.duration)

	post_duration = post.duration

	# get the endscreen
	endscreen = mpe.VideoFileClip(os.path.join(template_path, "endScreen.mp4")).resize(width = 1060)

	# add the endscreen to end of post
	final_video = mpe.CompositeVideoClip([post.set_position("center"), endscreen.set_start(post.duration)], size = (1080,1920), bg_color = (0,0,0)).set_fps(post.fps)

	if ((not image and not meme) or image):
		final_video.audio =  music
	elif (meme):
		final_video.audio = default_audio

	# must set duration after setting audio
	final_video = final_video.set_duration(post_duration + 6)

	# write video to file and check if successful
	final_video.write_videofile(final_video_path, bitrate = "4000k")
	# checking if the final video was created successfully
	if os.path.exists (final_video_path):
		# delete old raw post
		try:
			os.remove(raw_post_path)
		except:
			pass
		# delete the local final vid
		try:
			os.remove (final_video_path)
		except:
			pass

	else:
		printErrorMessage ("final vid not created", raw_post_path)
		endscreen.close()
		post.close()
		return -1

	# do this if we are re-editing
	if re_edit:
		post_title = document.to_dict()["title"]
		# delete old final from storage
		try:
			video = bucket.blob (f"final_vids/{post_title}")
			video.delete()
		except Exception as e:
			printErrorMessage ("could not delete video", raw_post_path)

		# update firebase with new final
		final_vid_blob = bucket.blob(f"final_vids/{post_title}")
		final_vid_blob.upload_from_filename(final_video_path)
		final_vid_blob.make_public()
		new_source = final_vid_blob.generate_signed_url(expiration=timedelta(weeks = 4))

		document.reference.update ({"filepath": new_source})

		try:
			os.remove (final_video_path)
			os.remove (raw_post_path)
		except:
			pass
		return new_source
	else:
		return 1


if __name__ == "__main__":
	app.run(host='0.0.0.0',port=int(os.environ.get('PORT',8080)))