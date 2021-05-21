import os
import pandas as pd
import random
musicPath = r'D:\Documents\python projects\rocket league reddit extraction\music'

allSongs = pd.read_csv(musicPath+'musicInfo.csv')

musicInfo = []
for blah, blahh, files in os.walk(musicPath):
    for item in files:
        if item.endswith('.mp3'):
            musicInfo.append([(str(os.path.join(musicPath, item))), str(item), 0])

musicInfo = pd.DataFrame(musicInfo,columns=['dir', 'name', 'dropTime'])

allSongs = allSongs.append(musicInfo, ignore_index=True)
allSongs = allSongs.drop_duplicates(subset = 'name')

indexFile = open(musicPath + 'musicIndex.txt')
index = int(indexFile.readline().strip())
indexFile.close()

for i in range(index, allSongs.shape[0]):
    dropTime = input("drop time for {}: ".format(allSongs.loc[[i], ['name']]))
    allSongs.loc[[i], ['dropTime']] = dropTime

allSongs.to_csv(path_or_buf=musicPath+'musicInfo.csv', index=False)

indexFile = open(musicPath+'musicIndex.txt', 'w')
indexFile.write(str(allSongs.shape[0]))
indexFile.close()

audioSelector = random.randint(0,(allSongs.shape[0]-1))
print(str(allSongs.loc[[audioSelector], ['name']]))