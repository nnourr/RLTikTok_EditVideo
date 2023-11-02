from urllib.request import urlretrieve
from flask import Flask, request
from RLGoalFrame import findGoal
from datetime import timedelta
import moviepy.editor as mpe 
from flask_cors import CORS
from pathlib import Path
from time import sleep
import pandas as pd
import random
import json
import os

# uhhh yup this is a web app yup yup mmhmmm
app = Flask(__name__)
CORS(app)

def printErrorMessage (exception, path):
	print (f"had trouble editing post")
	print (f"path: {path}")
	print (f"exception: {exception}")

# this function will edit the videos
@app.route('/', methods = ["POST"])
def editPost ():
	# setting up google
	root = Path(__file__).parent
	
	# just some some feedback
	print ("editing post...")

	music_path = 'C:\Users\User\Documents\CIS3760\prez\RLTikTok_EditVideo\editVideo\music'
	# reading songs csv
	songs_info = pd.read_csv(os.path.join(music_path, "musicInfo.csv"))

	raw_post_path = ''

	# if post is a video
	post = mpe.VideoFileClip(raw_post_path)

	post = post.resize (width = 1080)
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
			goal_sound = mpe.AudioFileClip(os.path.join(goal_path, 'goal0.mp3')).volumex(0.4)

			# trim the music to drop when the goal is scored
			music = music.subclip(((int(songs_info.at[music_selector, 'dropTime'])) - goal_time), music.duration)

			# add the effects
			music = mpe.CompositeAudioClip([music, goal_sound.set_start(goal_time), fx_sound.set_start(goal_time)])

		# if a goal wasn't found
		else:
			# set up a generic drop time of 5 seconds
			music = music.subclip(((int(songs_info.at[music_selector, 'dropTime'])) - 5), music.duration)
	post_duration = post.duration

	# get the endscreen
	endscreen = mpe.VideoFileClip(os.path.join(template_path, "endScreen.mp4")).resize(width = 1080)

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
		print ("successfully edited video!")

	else:
		printErrorMessage ("final vid not created", raw_post_path)
		endscreen.close()
		post.close()
		return -1

	# do this if we are re-editing
	if re_edit:
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

	if re_edit:
		document.reference.update ({"filepath": new_source}) 
	
	try:
		os.remove (final_video_path)
	except:
		pass
	try:
		os.remove (raw_post_path)
	except:
		pass



	return new_source


if __name__ == "__main__":
	app.run(host='0.0.0.0',port=int(os.environ.get('PORT',8080)))