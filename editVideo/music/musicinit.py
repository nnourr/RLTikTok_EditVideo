import os
import pandas as pd
import random
musicPath = r'D:\Documents\python projects\RLTikTok_EditVideo\editVideo\music'

allSongs = pd.read_csv(os.path.join(musicPath, 'musicInfo.csv'))

musicInfo = []
for blah, blahh, files in os.walk(musicPath):
    for item in files:
        if item.endswith('.mp3'):
            musicInfo.append([(str(os.path.join(musicPath, item))), str(item), 0])

musicInfo = pd.DataFrame(musicInfo,columns=['dir', 'name', 'dropTime'])

allSongs = allSongs.append(musicInfo, ignore_index=True)
allSongs = allSongs.drop_duplicates(subset = 'name')

indexFile = open(os.path.join(musicPath, 'musicIndex.txt'))
index = int(indexFile.readline().strip())
indexFile.close()

for i, row in allSongs[index:].iterrows():
    dropTime = input("drop time for {}: ".format(row['name']))
    allSongs.loc[[i], ['dropTime']] = dropTime

allSongs.to_csv(path_or_buf=os.path.join(musicPath, 'musicInfo.csv'), index=False)

indexFile = open(os.path.join(musicPath, 'musicIndex.txt'), 'w')
indexFile.write(str(allSongs.shape[0]))
indexFile.close()

audioSelector = random.randint(0,(allSongs.shape[0]-1))
print(str(allSongs.loc[[audioSelector], ['name']]))