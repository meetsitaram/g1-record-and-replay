# New Feature : G1 Music
This new feature is to teach unitree g1 humaniod how to play music notes on different musical instruments with its two arms while sitting on a chair. 

## Approach
The appraoch is to use the record and replay functionality that is already implemented in this repo. In order to play any music given a musical instrument like a piano or a drum, we will have to first break down the music into a sequence of notes like C -> A -> C -> D. In order to play each note, we will record one episode that will begin while g1 is holding its hand above the key to press, and end with g1 hitting or touching the key. There will also be episodes to record the initial position to be on to move from the beginning resting sitting position, and also to record the end position from which it will move back to the final resting position. Then, in order to play the music, we will provide sequence to notes and using the replay functionality, we will play episodes corresponding to each note in a sequence from beginning till the end.

## Implementation
1 - create a sub directory in this repo specific to this feature 
 a - initialize with skeleton code that takes details on the musical instrument to play and also the list of notes to support. 
 b - for each note, it should also provide option to assign what hand to use - either left arm or right arm. so there will be a clear one-to-one mapping of note <-> hand.
 c - it will also save all these details as a config file.
2 - Implement a MusicRecorder Class that will internally use the Recorder class to record, and provide additional functionality on top of it. 
 a - This script will take in the instrument and notes details that are setup by the script in the previous step
 b - It will prompt the user to press some key when ready. 
 c - It will then go through a sequence of init-play, iterate through all the notes one at a time first for right arm and then for left arm, add  final-play and instruct the user to record each episode when ready. 
 d - It will save all episodes corresponding to each note in a separate file. 
 e - It also provides a helper function that can print all details of any given note including the episode file  path, time length, fps, etc.
3 - Implement a EpisodeTrimmer class that will help in tweeking the episodes for any given note
 a - Given an episode, it can help in trimming initial few frames or final frames of the episode.
 b - save the modified episode as the one corresponding to the music note, but also backup the original episode  with a different file name. 
4 - Implement a MusicReplayer class that will internally use the Replayer class to replay, and provide additional functionlity on top of it.
 a - This script will take in a music song as a sequence of notes for each, e.g. C1:left;C2:right -> A2:right -> B1:left; B1:right -> G2:right, and replays those on the g1 with either left, or right or both based on the input notes provided. 
 b - It will also add init-play before the sequence and final-play at the end of the sequence. 

