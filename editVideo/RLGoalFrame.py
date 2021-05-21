import os
import cv2
import numpy as np
import time
from concurrent import futures
import av
import sys
import logging
from pathlib import Path

# defining global root path
root = Path(__file__).parent

def findMatch(score, frame, i, tolerance1, tolerance2):
    # get result matrix
    result = cv2.matchTemplate(frame, score, cv2.TM_CCOEFF_NORMED)

    # special cases because some scores are inherently easier to find
    # yes 0.3 makes a huge difference ok
    if i == 3 or i == 1:
        loc = np.where(result >= float(tolerance1)/100)
    else:
        loc = np.where(result >= float(tolerance2)/100)

    # if we have results above the threshhold 
    if len(loc[0]) > 0:
        # a match was found 
        return True
    else:
        return False

def checkForwards(scores, list_of_frames, no_of_frames, first_score, tolerance1, tolerance2):
    # set the score as 1 more than the current score
    score_index = first_score + 1
    next_score = scores [score_index]

    # iterate through the other half of the frames
    for frame_index in range (int(no_of_frames / 2), no_of_frames, 2):
        frame = list_of_frames [frame_index]

        # check each frame for the score
        if findMatch (next_score, frame, score_index, tolerance1, tolerance2) == True:
            return frame_index
    
    return -1

def checkBackwards(scores, list_of_frames, no_of_frames, first_score, tolerance1, tolerance2):
    score_index = first_score - 1
    prev_score = scores [score_index]
    for frame_index in range (int(no_of_frames / 2), 0, -2):
        frame = list_of_frames [frame_index]

        if findMatch (prev_score, frame, score_index, tolerance1, tolerance2) == True:
            return frame_index

    return -1

def findGoalByWidth (parameters, clipDir, list_of_frames, tolerance1, tolerance2):
    width = parameters [0]
    check_right = parameters [1]
    first_score = -1

    # initialize scores
    num_scores = 5
    scores = []
    if check_right:
        score_dir = os.path.join (root, "rightScores", "score{}.JPG")
        # trim frames to appropriate size
        list_of_frames = [frame[0: 70, 460: 560] for frame in list_of_frames]
    else:
        score_dir = os.path.join (root, "scores", "score{}.JPG")
        # trim frames to appropriate size
        list_of_frames = [frame[0: 70, 320: 400] for frame in list_of_frames]
    for i in range (0, num_scores + 1):
        scores.append(cv2.imread(score_dir.format(i), cv2.IMREAD_GRAYSCALE))

    logging.info (scores)

    scores = [cv2.GaussianBlur(score,(15,15),0) for score in scores]

    ratio = scores[0].shape[0]/scores[0].shape[1]
    scores = [cv2.resize(score, (width, int(ratio*width))) for score in scores]

    no_of_frames = len (list_of_frames)

    # check middle score
    for frame_index in range (int(no_of_frames/2) - 20, int(no_of_frames/2) + 21, 10):
        frame = list_of_frames[frame_index]
        
        # check frame against every score
        for score_index in range (0, len(scores)):
            score = scores[score_index]

            # check if a match is found
            if findMatch(score, frame, score_index, tolerance1, tolerance2) == True:
                first_score = score_index
                logging.info (f"first score is: {first_score} with width: {width}")
                break

        # if a score was found, stop checking
        if first_score > -1:
            break
    
    # if nothing found
    if first_score < 0:
        logging.info ("nothing found with width", width)
        return -1

    # check forwards
    # if score is 5, we cannot check for 6 so only check 4 backwards
    if first_score != 5:
        found_frame = checkForwards (scores, list_of_frames, no_of_frames, first_score, tolerance1, tolerance2)
        if found_frame > 0:
            return found_frame

    # check backwards:
    # if score is 0, there cannot be a previous goal so only check 1 forwards
    if first_score != 0:
        found_frame = checkBackwards (scores, list_of_frames, no_of_frames, first_score, tolerance1, tolerance2)
        if found_frame > 0:
            return found_frame
        
    logging.info ("couldn't find second score with width", width)
    return -1

def findGoal(clipDir, tolerance1, tolerance2):
    start = time.perf_counter()

    # setting up the frames
    container = av.open (clipDir)
    list_of_frames = [frame.to_ndarray() for frame in container.decode(video = 0)]
    list_of_frames = [cv2.GaussianBlur(frame,(13,13),0) for frame in list_of_frames]
    ratio = list_of_frames[0].shape[0]/list_of_frames[0].shape[1]
    list_of_frames = [cv2.resize(frame, (852, int(ratio*852))) for frame in list_of_frames]

    # parameters to map to function
    # param [a,b] where a is the width of the score image
    # and b is a bool to look to goals on the right
    parameters = [[25,0], [20,0], [16,0], [25,1], [20,1], [16,1]]

    with futures.ThreadPoolExecutor() as excecutor:
        # run process for each width
        frames = [excecutor.submit (findGoalByWidth, parameter, clipDir, list_of_frames, tolerance1, tolerance2) for parameter in parameters]

        # check if we found a goal
        for frame_num in futures.as_completed(frames):
            result = frame_num.result()

            # if result is bigger than 0, we found one (!!)
            if int(result) > 0:
                logging.info ("found a goal!")
                end = time.perf_counter()
                logging.info (f"script took {end - start} seconds to find a goal")
                logging.info ("")
                return result       

    # if we didn't return yet, nothing was found 
    end = time.perf_counter()
    logging.info (f"script took {end - start} seconds to not find a goal")
    logging.info ("")
    return 0

if __name__ == "__main__":
    start = time.perf_counter()
    clipDir = r'D:\Documents\python projects\rocket league reddit extraction\rawVids\This was definitely on purpose .mp4'
    try:
        foundFrame = findGoal(sys.argv[1], int(sys.argv[2])/100, int(sys.argv[3])/100)
    except:
        foundFrame = findGoal(sys.argv[1])

    logging.info ("result:",foundFrame)
    logging.info ("time with auto multiprocessing:", start - time.perf_counter())