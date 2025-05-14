# Project Plan

## Top Objectives:
1. I will generate complex and unique recommendations that are accurate.
2. My system will allow users to login into their own, personal Spotify account via user authentication within the Spotify API.
3. I will extract the user's top artists / tracks / genres and other user information to provide relavent details / recommendations.
4. I will make an easy-to-use accessible user interface with use of python libraries like Tkinter.
5. It will allow users to customise different factors of what type of songs my system will recommended. There will be a variety and range of recommendation algorithms.
6. My playlists will reflect the user's unique music taste and their listening history.
7. The playlists that my system generates will be able to upload these to the users Spotify library, the user can choose whether they want to do this or not.
8. I will use Object Oriented Programming to make my code more efficient and organised.
9. I store the client credientials and other API keys safely and securely within my folder and my repo so that they are private and not accessible to anyone else.

## Code Milestones

- Milestone 1 (12th may 2025) - basic recommendations and a simple working UI with user authorization.
- Milestone 2 (2nd june 2025) - more complex recommendation algorithms and features with a variety of suggestions. Data structures and complex algorithms to make code A level standard. 
- Milestone 3 (30th june 2025) - UI is easy-to-use and displayed approriately, and code is well-organised.
- Milestone 4 **FINAL** (8th september 2025) - UI is complete and accessbile, any other small features complete.

### Milestone 1 

***Basic recommendations and a simple working UI with user authorization.***

I have completed what I wanted to during this timeframe, I feel I am up-to-date with my code since I have been working on it reguarly. 
I have created the basics of the UI using Tkinter, I made frames which switch when you click buttons, allowing you to access different frames for the different recommendations. 
3 different recommendation algorithms have been created:
1. User-based - generates songs based on user's listening history, and a time-range then retrieveing their top artists from that time frame and getting similar artists and their songs.
2. Genres - generates songs based of user's genre input, this is done using the last.fm API
3. Weather-based - generates songs using the open weather API to fetch weather from current town and filter genres from the season / time / weather.

Some other features I have made are a random album picker from the user's spotify library. The ability to add the recommended songs to the user's library, by addind playlists.
There is also a small user stats page which I am going to develop.
I have also created the user authorization which is the main pre-requesite for all my objectives, I completed this using multiple libraries to make it as efficient as possible: spotipy, flask, webbrowser etc.

#### Targets

I hope to develop the weather / season / time-of-day recommendations since I haven't completed it yet. I also wish to generate some more unique recommendation algorithms.
I also need to fix a bug that is occuring in the add_to_playlist function. 
