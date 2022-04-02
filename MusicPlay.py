from tkinter import *
from tkinter import ttk
import os
import database
from tkinter import filedialog
import pygame
import time

database.createdb()

APP_TITLE = "Music Player"
DIMENSION = "500x400"

root = Tk()
root.title("Music Player")
root.geometry("500x400")

# Create Master Frame
master_frame = Frame(root)
master_frame.pack(pady=20)

# Create Playlist Box
song_box = Listbox(master_frame, bg="black", fg="green", width=60,
                   selectbackground="green", selectforeground="black")
song_box.grid(row=0, column=0)

songs_list = database.search("")["Songs"]
for song in songs_list:
    name = song[0]
    song_box.insert(END, name)

# Initialze Pygame Mixer
pygame.mixer.init()


def show_time():
    if stopped:
        return
    # Grab Current Song Elapsed Time
    current_time = pygame.mixer.music.get_pos() / 1000

    # throw up temp label to get data
    #slider_label.config(text=f'Slider: {int(my_slider.get())} and Song Pos: {int(current_time)}')
    # convert to time format
    converted_current_time = time.strftime('%M:%S', time.gmtime(current_time))

    # Get Currently Playing Song
    #current_song = song_box.curselection()
    # Grab song title from playlist
    song = song_box.get(ACTIVE)

    # Get song Length
    global song_length
    song_length = float(database.search(song)['Songs'][0][3])

    # Convert to Time Format
    converted_song_length = time.strftime('%M:%S', time.gmtime(song_length))

    # Increase current time by 1 second
    current_time += 1

    if int(my_slider.get()) == int(song_length):
        status_bar.config(
            text=f'Time Elapsed: {converted_song_length}  of  {converted_song_length}  ')
    elif paused:
        pass
    elif int(my_slider.get()) == int(current_time):
        # Update Slider To position
        slider_position = int(song_length)
        my_slider.config(to=slider_position, value=int(current_time))

    else:
        # Update Slider To position
        slider_position = int(song_length)
        my_slider.config(to=slider_position, value=int(my_slider.get()))

        # convert to time format
        converted_current_time = time.strftime(
            '%M:%S', time.gmtime(int(my_slider.get())))

        # Output time to status bar
        status_bar.config(
            text=f'Time Elapsed: {converted_current_time}  of  {converted_song_length}  ')

        # Move this thing along by one second
        next_time = int(my_slider.get()) + 1
        my_slider.config(value=next_time)
    status_bar.after(1000, show_time)


def slide(x):
    song = song_box.get(ACTIVE)
    song_path = database.search(song)["Songs"][0][2]
    pygame.mixer.music.load(song_path)
    pygame.mixer.music.play(loops=0, start=int(my_slider.get()))


def play(song=None):
    global stopped
    if stopped == False:
        stop()
    stopped = False
    show_time()
    if song == None:
        song = song_box.get(ACTIVE)
    song_path = database.search(song)['Songs'][0][2]
    pygame.mixer.music.load(song_path)
    pygame.mixer.music.play(loops=0)


global stopped
stopped = False


def stop():
    status_bar.config(text="")
    my_slider.config(value=0)

    # Stop Song From Playing
    pygame.mixer.music.stop()
    song_box.selection_clear(ACTIVE)

    # Set stopped vairable to True
    global stopped
    stopped = True


# Create Global Pause Variable
global paused
paused = False


def pause(is_paused):
    global paused
    paused = is_paused
    if paused:
        # Unpause
        pygame.mixer.music.unpause()
        paused = False
    else:
        # Pause
        pygame.mixer.music.pause()
        paused = True


def previous_song():
    status_bar.config(text='')
#     my_slider.config(value=0)
    # Get the current song tuple number
    prev_one = song_box.curselection()
    # Add one to the current song number
    prev_one = prev_one[0]-1
    # Grab song title from playlist
    song = song_box.get(prev_one)

    # Play prev song
    play(song)
    my_slider.config(value=0)

    # Clear active bar in playlist listbox
    song_box.selection_clear(0, END)

    # Activate new song bar
    song_box.activate(prev_one)

    # Set Active Bar to Next Song
    song_box.selection_set(prev_one, last=None)


def next_song():
    # Reset Slider and Status Bar
    status_bar.config(text='')

    # Get the current song tuple number
    next_one = song_box.curselection()
    # Add one to the current song number
    next_one = next_one[0]+1
    # Grab song title from playlist
    song = song_box.get(next_one)

    # Play the song
    play(song)
    my_slider.config(value=0)

    # Clear active bar in playlist listbox
    song_box.selection_clear(0, END)

    # Activate new song bar
    song_box.activate(next_one)

    # Set Active Bar to Next Song
    song_box.selection_set(next_one, last=None)


def delete_song():
    stop()
    database.deleteSong(song_box.get(ACTIVE))
    song_box.delete(ANCHOR)


def control_vol(x):
    pygame.mixer.music.set_volume(volume_slider.get())


def browseDirectories():
    dirname = filedialog.askdirectory(initialdir=os.path.expanduser('~'),
                                      title="Select a Directory")

    if dirname:
        addDir(dirname)


def browseSongs():
    songname = filedialog.askopenfilename(title="Select a Song",
                                          filetypes=(("Audio files", "*.mp3"),
                                                     ("Audio files", "*.ogg"),
                                                     ("Audio files", "*.wav")))
    if songname:
        name, _ = database.addSingle(songname)
        song_box.insert(END, name)
#         Button(master = root, text = "Successfully added 1 song!",state="disabled", width = 25).pack()


def addDir(dir):
    try:
        n, names = database.addRecords(dir)
        if not n:
            msg = "No songs in the given directory"
        else:
            msg = f"Successfully added {n} song" + "s"*int(n != 1) + "!"
            for name in names:
                song_box.insert(END, name)
    except ValueError as e:
        msg = e

#     Button(master = root, text = msg, state="disabled",width=25).grid()


# Define Player Control Button Images
back_btn_img = PhotoImage(file='images/back50.png', master=root)
forward_btn_img = PhotoImage(file='images/forward50.png', master=root)
play_btn_img = PhotoImage(file='images/play50.png', master=root)
pause_btn_img = PhotoImage(file='images/pause50.png', master=root)
stop_btn_img = PhotoImage(file='images/stop50.png', master=root)

# Create Player Control Frame
controls_frame = Frame(master_frame)
controls_frame.grid(row=1, column=0, pady=20)

# Create Volume Label Frame
volume_frame = LabelFrame(master_frame, text='Volume')
volume_frame.grid(row=0, column=1, padx=20)

# Create Player Control Buttons
back_button = Button(controls_frame, image=back_btn_img,
                     borderwidth=0, command=previous_song)
forward_button = Button(
    controls_frame, image=forward_btn_img, borderwidth=0, command=next_song)
play_button = Button(controls_frame, image=play_btn_img,
                     borderwidth=0, command=play)
pause_button = Button(controls_frame, image=pause_btn_img,
                      borderwidth=0, command=lambda: pause(paused))
stop_button = Button(controls_frame, image=stop_btn_img,
                     borderwidth=0, command=stop)


back_button.grid(row=0, column=0, padx=10)
forward_button.grid(row=0, column=1, padx=10)
play_button.grid(row=0, column=2, padx=10)
pause_button.grid(row=0, column=3, padx=10)
stop_button.grid(row=0, column=4, padx=10)

menubar = Menu(root)
filemenu = Menu(menubar)
deletemenu = Menu(menubar)
menubar.add_cascade(label="Add Songs", menu=filemenu)
menubar.add_cascade(label="Delete Songs", menu=deletemenu)
filemenu.add_command(label="Add Directory", command=browseDirectories)
filemenu.add_command(label="Add Song", command=browseSongs)
deletemenu.add_command(label="Delete Song", command=delete_song)
root.config(menu=menubar)

# Create Status Bar
status_bar = Label(root, text='', bd=1, relief=GROOVE, anchor=E)
status_bar.pack(fill=X, side=BOTTOM, ipady=2)

# Create Music Position Slider
my_slider = ttk.Scale(master_frame, from_=0, to=100,
                      orient=HORIZONTAL, value=0, command=slide, length=360)
my_slider.grid(row=2, column=0, pady=10)

# Create Music Position Slider
volume_slider = ttk.Scale(volume_frame, from_=0, to=1,
                          orient=VERTICAL, value=1, command=control_vol, length=120)
volume_slider.pack(pady=10)

root.mainloop()
pygame.mixer.music.stop()
