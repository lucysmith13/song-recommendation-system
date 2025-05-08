import os, spotipy, tkinter as tk, requests, random, customtkinter as ctk, time
import dateutil.utils
from bottle import url
from spotipy.oauth2 import SpotifyOAuth
from PIL import Image, ImageTk
from tkinter import ttk, PhotoImage
import webview
import urllib.parse
from flask import Flask, request
import threading
import webbrowser
import re
import http.server
import socketserver
from tkinter import font, messagebox
import json
from io import BytesIO
import datetime
import time
from datetime import datetime, date
from dotenv import load_dotenv

class Stats():
    def __init__(self, access_token):
        self.sp = spotipy.Spotify(auth=access_token)

    def get_top_artists(self, limit, time_range):
        results = self.sp.current_user_top_artists(limit=limit, time_range=time_range)
        return [artist['name'] for artist in results['items']]

    def get_top_tracks(self, limit, time_range):
        results = self.sp.current_user_top_tracks(limit=limit, time_range=time_range)
        return [track['name'] for track in results['items']]