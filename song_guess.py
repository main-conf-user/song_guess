from tkinter import Tk, PhotoImage, Label, Frame, Button, Entry, Canvas, DISABLED, NORMAL, END, TOP
from tkinter.ttk import Scrollbar, Style
from tkinter.font import Font
from textwrap import fill
from pygame import mixer


class SongGuess():

    def __init__(self,
                 root,
                 title='SONG_GUESS',
                 win_text='VICTORY',
                 loss_text='DEFEAT',
                 bg='#000000',
                 fg='#ffffff',
                 play_button_colour='#787878',
                 prior_guesses_colour='#787878',
                 prior_guesses_box_colour='#111212',
                 prior_guesses_font_size=8,
                 icon=None,
                 valid_answers=None,
                 song_path=None,
                 guesses_per_round=1,
                 plays_allowed_per_clip=1,
                 song_pieces=10, #either a number to divide song into, or list of specified stop times
                 game_visual=None,
                 song_volume=0.5,
                 debug_highlighter_thickness=0):


        self.game_finished = False #set to False when game ends to catch possible error of submit_guess method call after entry_field destroyed

        self.after_id = None #for catching error of button reactivation referenced post endgame destruction

        self.bg = bg
        self.prior_guesses_colour = prior_guesses_colour
        self.debug_highlighter_thickness = debug_highlighter_thickness
        self.valid_answers = valid_answers
        self.song_path = song_path
        self.guesses_per_round = guesses_per_round
        self.plays_allowed_per_clip = plays_allowed_per_clip
        self.plays_remaining_for_this_clip = plays_allowed_per_clip
        self.guesses_this_round = 0
        self.guess_log = []
        self.guesses_thus_far = 0
        self.round_idx = 0

        self.prior_guesses_font = Font(family='fixedsys',size=prior_guesses_font_size,weight='normal')

        self.win_text = win_text
        self.loss_text = loss_text

        mixer.init()
        self.mixer = mixer.Sound(song_path)
        self.mixer.set_volume(song_volume)
        self.sound_length_s = self.mixer.get_length()
        self.sound_length_ms = self.sound_length_s*1000

        if type(song_pieces) == list:
            self.reveal_section_lengths = [int(piece) for piece in song_pieces] #ensures pieces are readable integers
        elif type(song_pieces) == int:
            self.reveal_section_length = self.sound_length_ms/song_pieces
            self.reveal_section_lengths = [int(self.reveal_section_length*num) for num in range(1,song_pieces)] + [int(self.sound_length_ms+1)]

        self.final_round_idx = len(self.reveal_section_lengths)

        number_of_clips = len(self.reveal_section_lengths)
        self.total_guesses_allowed = number_of_clips * guesses_per_round

        self.root=root
        root.title(title)
        root.config(bg=bg)
        root.attributes('-fullscreen',True)


        if icon:
            try:
                if icon.endswith(('.gm','.ppm','.gif','.png')):
                    iconified_img = PhotoImage(file=icon)
                    root.iconphoto(True,iconified_img)
                elif icon.endswith('.ico'):
                    root.iconbitmap(icon)
            except Exception as e:
                print(f'ERROR SETTING ICON: {e}')

        self.root.grid_columnconfigure(0,weight=1)
        self.root.grid_rowconfigure(0,weight=1)

        self.host_frame = Frame(root,
                                bg=bg,
                                highlightthickness=debug_highlighter_thickness)
        self.host_frame.grid(row=0,
                             column=0,
                             sticky='nsew')
        self.host_frame.grid_columnconfigure(0,weight=50)
        self.host_frame.grid_columnconfigure(1,weight=1)

        self.image_frame = Frame(self.host_frame,
                                 bg=bg,
                                 highlightthickness=debug_highlighter_thickness)
        self.image_frame.grid(row=0,
                              column=0,
                              padx=20,
                              pady=20,
                              sticky='nsew')
        self.image_frame.grid_rowconfigure(0,weight=1)
        self.image_frame.grid_columnconfigure(0,weight=1)            

        self.interaction_frame = Frame(self.host_frame,
                                     bg=bg,
                                     highlightthickness=debug_highlighter_thickness)
        self.interaction_frame.grid(row=0,
                                    column=1,
                                    padx=(20,100),
                                    pady=20,
                                    sticky='nsew')
        self.interaction_frame.grid_rowconfigure(0,weight=1)
        self.interaction_frame.grid_rowconfigure(1,weight=2)
        self.interaction_frame.grid_rowconfigure(2,weight=25)
        self.interaction_frame.grid_columnconfigure(0,weight=1)

        self.guess_frame = Frame(self.interaction_frame,
                                 bg=bg,
                                 highlightthickness=debug_highlighter_thickness)
        self.guess_frame.grid(row=0,
                              column=0,
                              padx=0,
                              pady=0,
                              sticky='n')
        self.guess_frame.grid_rowconfigure(0,weight=1)
        self.guess_frame.grid_columnconfigure(0,weight=1)

        self.play_frame = Frame(self.interaction_frame,
                                bg=bg,
                                highlightthickness=debug_highlighter_thickness)
        self.play_frame.grid(row=1,
                             column=0,
                             padx=0,
                             pady=0,
                             sticky='nsew')
        self.play_frame.grid_rowconfigure(0,weight=1)
        self.play_frame.grid_columnconfigure(0,weight=1)

        self.game_info_frame = Frame(self.interaction_frame,
                                     bg=bg,
                                     highlightthickness=debug_highlighter_thickness)
        self.game_info_frame.grid(row=2,
                                  column=0,
                                  padx=0,
                                  pady=0,
                                  sticky='nsew')
        self.game_info_frame.grid_rowconfigure(0,weight=1)
        self.game_info_frame.grid_columnconfigure(0,weight=1)

        if game_visual:
            try:
                self.game_visual = PhotoImage(file=game_visual)
            except Exception as e:
                print(f'ERROR: {e}')
                self.game_visual = None
        else:
            self.game_visual=None

        self.image = Label(self.image_frame,
                           text='SCREEN',
                           font=('fixedsys',15),
                           bg=bg,
                           fg=fg,
                           highlightthickness=debug_highlighter_thickness,
                           anchor='center',
                           justify='center',
                           image=self.game_visual)
        self.image.grid(row=0,
                        column=0,
                        padx=0,
                        pady=0,
                        sticky='n')

        self.entry_field = Entry(self.guess_frame,
                                 width=35,
                                 font=('fixedsys',15),
                                 bg=bg,
                                 fg=fg,
                                 highlightthickness=7,
                                 highlightbackground=fg,
                                 highlightcolor=fg)
        self.entry_field.grid(row=0,
                              column=0,
                              padx=0,
                              pady=0,
                              sticky='ew')

        self.play_button = Button(self.play_frame,
                                  bg=bg,
                                  text='PLAY SNIPPET',
                                  fg=play_button_colour,
                                  font=('fixedsys',50,'bold'),
                                  command=self.play_song_clip)
        self.play_button.grid(row=0,
                              column=0,
                              padx=0,
                              pady=0,
                              sticky='new')

        self.prior_guesses_title = Label(self.game_info_frame,
                                         text='GUESS LOG:  ',
                                         font=('fixedsys',10),
                                         bg=bg,
                                         fg=prior_guesses_colour,
                                         anchor='w',
                                         justify='left',
                                         highlightthickness=debug_highlighter_thickness)
        self.prior_guesses_title.grid(row=1,
                                      column=0,
                                      padx=0,
                                      pady=(0,20),
                                      sticky='nsew')        

        self.game_details = Frame(self.game_info_frame,
                                  bg=bg,
                                  highlightthickness=debug_highlighter_thickness)
        self.game_details.grid(row=0,
                                column=0,
                                padx=0,
                                pady=100,
                                sticky='nsew')
        self.game_details.grid_columnconfigure(0,weight=1)
        self.game_details.grid_rowconfigure(0,weight=1)
        self.game_details.grid_rowconfigure(1,weight=1)
        self.game_details.grid_rowconfigure(2,weight=1)
        self.game_details.grid_rowconfigure(3,weight=1)

        self.round_frame = Frame(self.game_details,
                                 bg=bg,
                                 highlightthickness=debug_highlighter_thickness)
        self.round_frame.grid(row=0,
                              column=0,
                              padx=0,
                              pady=0,
                              sticky='nsew')

        self.round_label_str = Label(self.round_frame,
                                     text='ROUND',
                                     font=('fixedsys',8),
                                     bg=bg,
                                     fg=prior_guesses_colour,
                                     anchor='w',
                                     justify='left',
                                     highlightthickness=debug_highlighter_thickness)
        self.round_label_str.grid(row=0,
                                  column=0,
                                  padx=0,
                                  pady=0,
                                  sticky='nsew')

        self.round_label_num = Label(self.round_frame,
                                     text=f"{self.round_idx+1}/{self.final_round_idx+1}",
                                     font=('fixedsys',8),
                                     bg=bg,
                                     fg=fg,
                                     anchor='w',
                                     justify='left',
                                     highlightthickness=debug_highlighter_thickness)
        self.round_label_num.grid(row=0,
                                  column=1,
                                  padx=0,
                                  pady=0,
                                  sticky='nsew')

        self.guesses_thus_far_frame = Frame(self.game_details,
                                            bg=bg,
                                            highlightthickness=debug_highlighter_thickness)
        self.guesses_thus_far_frame.grid(row=1,
                                         column=0,
                                         padx=0,
                                         pady=0,
                                         sticky='nsew')

        self.guesses_thus_far_label_str = Label(self.guesses_thus_far_frame,
                                                text='TOTAL GUESSES MADE',
                                                font=('fixedsys',8),
                                                bg=bg,
                                                fg=prior_guesses_colour,
                                                anchor='w',
                                                justify='left',
                                                highlightthickness=debug_highlighter_thickness)
        self.guesses_thus_far_label_str.grid(row=0,
                                             column=0,
                                             padx=0,
                                             pady=0,
                                             sticky='nsew')

        self.guesses_thus_far_label_num = Label(self.guesses_thus_far_frame,
                                                text=self.guesses_thus_far,
                                                font=('fixedsys',8),
                                                bg=bg,
                                                fg=fg,
                                                anchor='w',
                                                justify='left',
                                                highlightthickness=debug_highlighter_thickness)
        self.guesses_thus_far_label_num.grid(row=0,
                                             column=1,
                                             padx=0,
                                             pady=0,
                                             sticky='nsew')

        self.guesses_remaining_this_round_frame = Frame(self.game_details,
                                                        bg=bg,
                                                        highlightthickness=debug_highlighter_thickness)
        self.guesses_remaining_this_round_frame.grid(row=2,
                                                     column=0,
                                                     padx=0,
                                                     pady=0,
                                                     sticky='nsew')

        self.guesses_remaining_this_round_label_str = Label(self.guesses_remaining_this_round_frame,
                                                            text='GUESSES REMAINING THIS ROUND',
                                                            font=('fixedsys',8),
                                                            bg=bg,
                                                            fg=prior_guesses_colour,
                                                            anchor='w',
                                                            justify='left',
                                                            highlightthickness=debug_highlighter_thickness)
        self.guesses_remaining_this_round_label_str.grid(row=0,
                                                         column=0,
                                                         padx=0,
                                                         pady=0,
                                                         sticky='nsew')         

        self.guesses_remaining_this_round_label_num = Label(self.guesses_remaining_this_round_frame,
                                                            text=self.guesses_per_round-self.guesses_this_round,
                                                            font=('fixedsys',8),
                                                            bg=bg,
                                                            fg=fg,
                                                            anchor='w',
                                                            justify='left',
                                                            highlightthickness=debug_highlighter_thickness)
        self.guesses_remaining_this_round_label_num.grid(row=0,
                                                         column=1,
                                                         padx=0,
                                                         pady=0,
                                                         sticky='nsew')         

        self.plays_remaining_for_this_clip_frame = Frame(self.game_details,
                                                         bg=bg,
                                                         highlightthickness=debug_highlighter_thickness)
        self.plays_remaining_for_this_clip_frame.grid(row=3,
                                                      column=0,
                                                      padx=0,
                                                      pady=0,
                                                      sticky='nsew')

        self.plays_remaining_for_this_clip_label_str = Label(self.plays_remaining_for_this_clip_frame,
                                                             text='PLAYS REMAINING FOR THIS CLIP',
                                                             font=('fixedsys',8),
                                                             bg=bg,
                                                             fg=prior_guesses_colour,
                                                             anchor='w',
                                                             justify='left',
                                                             highlightthickness=debug_highlighter_thickness)
        self.plays_remaining_for_this_clip_label_str.grid(row=0,
                                                          column=0,
                                                          padx=0,
                                                          pady=0,
                                                          sticky='nsew')                 

        self.plays_remaining_for_this_clip_label_num = Label(self.plays_remaining_for_this_clip_frame,
                                                             text=self.plays_remaining_for_this_clip,
                                                             font=('fixedsys',8),
                                                             bg=bg,
                                                             fg=fg,
                                                             anchor='w',
                                                             justify='left',
                                                             highlightthickness=debug_highlighter_thickness)
        self.plays_remaining_for_this_clip_label_num.grid(row=0,
                                                          column=1,
                                                          padx=0,
                                                          pady=0,
                                                          sticky='nsew')                 

        self.guess_history_frame = Frame(self.game_info_frame,
                                         bg=bg,
                                         highlightthickness=1,
                                         highlightcolor=prior_guesses_box_colour)
        self.guess_history_frame.grid(row=2,
                                      column=0,
                                      padx=0,
                                      pady=0,
                                      sticky='nsew')
        self.guess_history_frame.grid_columnconfigure(0,weight=50)
        self.guess_history_frame.grid_columnconfigure(0,weight=1)

        self.guess_log_canvas = Canvas(self.guess_history_frame,
                                       bg=bg,
                                       highlightthickness=debug_highlighter_thickness)
        self.guess_log_canvas.grid(row=0,
                                   column=0,
                                   padx=0,
                                   pady=0,
                                   sticky='nsew')

        style=Style()
        style.theme_use('clam')
        style.configure("MY.Vertical.TScrollbar",
                        background=bg,
                        foreground=bg,
                        bordercolor=prior_guesses_colour, 
                        arrowcolor=bg,
                        darkcolor=bg,
                        lightcolor=prior_guesses_box_colour,
                        troughcolor=bg,
                        gripcount=3)

        self.guess_log_scrollbar = Scrollbar(self.guess_history_frame,
                                             orient='vertical',
                                             style='MY.Vertical.TScrollbar',
                                             command=self.guess_log_canvas.yview)

        self.guess_log_frame = Frame(self.guess_log_canvas,
                                         bg=bg,
                                         highlightthickness=debug_highlighter_thickness)
        self.guess_log_canvas.create_window((0,0), 
                                            window=self.guess_log_frame,
                                            anchor='nw')

        self.endgame_label = Label(root,
                                   font=('fixedsys',70,'bold'),
                                   bg=bg,
                                   fg=fg)


        root.bind('<Escape>',self.exit_fullscreen)
        root.bind('<F11>',self.enter_fullscreen)
        root.bind('<Return>',self.submit_guess)

        self.guess_log_frame.bind("<Configure>",self.canvas_reconfigure)


    def exit_fullscreen(self,event=None):
        self.root.attributes('-fullscreen',False)
        self.root.state('zoomed')

    def enter_fullscreen(self,event=None):
        self.root.attributes('-fullscreen',True)

    def canvas_reconfigure(self,event):
        self.guess_log_canvas.configure(scrollregion=self.guess_log_canvas.bbox("all"))

        if self.guess_log_scrollbar not in self.guess_history_frame.grid_slaves():
            guess_log_canvas_height = self.guess_log_canvas.winfo_height()
            guess_log_frame_height = self.guess_log_frame.winfo_height()
            if guess_log_frame_height > guess_log_canvas_height:
                self.guess_log_scrollbar.grid(row=0,
                                              column=1,
                                              sticky='nsew')
                self.guess_log_canvas.configure(yscrollcommand=self.guess_log_scrollbar.set)                

    def disable_play_button(self):
        if self.play_button['state'] == 'normal':
            self.play_button.configure(state=DISABLED)

    def enable_play_button(self):
        try:
            if self.play_button['state'] == 'disabled':
                self.play_button.configure(state=NORMAL)
        except Exception as e:
            print(e)
            print('TclError raised when self.root.after tries enable_play_button after self.play_button destroyed\nmanaged to get through try,except block and after_cancel methods')

    def cleanup(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id=None
        self.mixer.stop()

    def clear_game_widgets(self):
        self.host_frame.destroy()

    def raise_endgame_screen(self,text):
        self.endgame_label.grid(row=0,
                                column=0,
                                sticky='nsew')
        self.endgame_label.configure(text=text)

    def wrap_up(self):
        self.raise_endgame_screen(self.valid_answers[0])
        self.mixer.play()
        self.root.after(int(self.sound_length_ms+1),self.root.destroy)       

    def play_song_clip(self):
        self.plays_remaining_for_this_clip-=1
        self.update_plays_remaining_for_this_clip_display()
        self.disable_play_button()
        play_idx = self.round_idx
        play_time_ms = self.reveal_section_lengths[play_idx]
        self.mixer.play(maxtime=play_time_ms)
        if self.plays_remaining_for_this_clip:
            self.after_id = self.root.after(play_time_ms,self.enable_play_button) #logs id of .after allowing for cancellation in event of endgame or new round

    def config_guess_log(self):
        previous_guesses = self.guess_log_frame.grid_slaves()
        if previous_guesses:
            for guess in previous_guesses:
                current_row = guess.grid_info()['row']
                new_row = current_row + 1
                guess.grid(row=new_row)
                self.guess_log_frame.grid_rowconfigure(new_row,weight=1)

        prepped_text = self.config_text_for_guess_log(widget=self.guess_log_canvas,
                                                      font=self.prior_guesses_font,
                                                      text=self.guess_log[-1])

        new_log = Label(self.guess_log_frame,
                        text='=> '+prepped_text,
                        font=self.prior_guesses_font,
                        bg=self.bg,
                        fg=self.prior_guesses_colour,
                        highlightthickness=self.debug_highlighter_thickness,
                        anchor='nw',
                        justify='left')
        new_log.grid(row=0,
                     column=0,
                     sticky='nsew')

    def config_text_for_guess_log(self,
                                  widget,
                                  font,
                                  text,
                                  safety_margin=2):
        self.root.update()
        line_width = widget.winfo_width()
        char_width = font.measure('W')
        chars_per_line = line_width // char_width

        prepped_text = fill(width=chars_per_line-safety_margin,
                            text=text)
        return prepped_text

    def update_round_display(self):
        self.round_label_num.configure(text=f"{self.round_idx+1}/{self.final_round_idx+1}")

    def update_total_guesses_display(self):
        self.guesses_thus_far_label_num.configure(text=self.guesses_thus_far)

    def update_guesses_this_round_display(self):
        self.guesses_remaining_this_round_label_num.configure(text=self.guesses_per_round-self.guesses_this_round)

    def update_plays_remaining_for_this_clip_display(self):
        self.plays_remaining_for_this_clip_label_num.configure(text=self.plays_remaining_for_this_clip)

    def submit_guess(self,event=None):
        if not self.game_finished:
            guess = self.entry_field.get().strip().upper()
            if guess:
                self.guess_log.append(guess)
                self.entry_field.delete(0,END)
                self.config_guess_log()
                self.guesses_this_round += 1
                self.update_guesses_this_round_display()
                self.guesses_thus_far += 1
                self.update_total_guesses_display()
                self.check_guess(guess)

    def check_guess(self,guess):
        if guess in self.valid_answers:
            self.game_finished = True
            self.victory_condition()
        elif self.guesses_this_round == self.guesses_per_round:
            if self.round_idx == self.final_round_idx:
                self.game_finished = True
                self.loss_condition()
            else:
                self.setup_next_turn()

    def setup_next_turn(self):
        self.cleanup()
        self.round_idx += 1
        self.update_round_display()
        self.plays_remaining_for_this_clip = self.plays_allowed_per_clip
        self.update_plays_remaining_for_this_clip_display()
        self.guesses_this_round = 0
        self.update_guesses_this_round_display()
        self.enable_play_button()               

    def victory_condition(self):
        self.cleanup()
        self.clear_game_widgets()
        self.raise_endgame_screen(self.win_text)
        self.root.after(5000,self.wrap_up)

    def loss_condition(self):
        self.cleanup()
        self.mixer.stop()
        self.clear_game_widgets()
        self.raise_endgame_screen(self.loss_text)
        self.root.after(5000,self.wrap_up)


if __name__ == '__main__':

    root = Tk()
    game = SongGuess(root,
                     game_visual='Harlem.png',
                     valid_answers=['CHRISTMAS NIGHT IN HARLEM'],
                     song_path='Christmas Night in Harlem.mp3',
                     win_text="DID YOU GUESS IT?\nWHY YES INDEED\nA BRIGHT SPARK MIND\nSEIZED VICTORY",
                     loss_text="DID YOU GUESS IT?\nWELL NO NOT QUITE\nBUT THEN AGAIN\nYOU'RE NOT SO BRIGHT",
                     guesses_per_round=1,
                     plays_allowed_per_clip=2,
                     song_pieces=40)
    root.mainloop()

