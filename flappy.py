import random
import time
import os
import base64
import sys
from tkinter import Tk, PhotoImage, Canvas, ALL
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

# config settings
FPS = 60
DELAY = 4
WIDTH = 700
HEIGHT = 700
SIZE = (WIDTH, HEIGHT)
GIFS = {"standard": "main_bird.gif"}
RESULTS_FILE = "data.txt"

# game settings
BIRD_WINDOW_SIZE = 250
COLUMN_DEPTH = 300
START_COLUMN_FROM = 450
COLUMN_SIZE = 80
RANDOM_MAX_DIFFERENCE = 200
BIRD_COORDINATE = (100, 300)

# bird animation settings
BIRD_DOWN_ANIMATION = [4, 4, 4, 4, 4]
BIRD_UP_ANIMATION = [-4, -4, -4, -4, -4]

BIRD_COLLISION_POINTS = [(124, 40), (64, 0), (30, 30), (0, 88), (0, 155), (80, 95), (80, 168)]
# BIRD_COLLISION_POINTS = []
# BIRD_COLLISION_POINTS = [(80, 168)]
BIRD_IMAGE_SIZE = (124, 168)


NEW_START = True


class MainModel(Canvas):
    def __init__(self):
        Canvas.__init__(self, width=SIZE[0], height=SIZE[1], background="#2BF0D9", highlightthickness=0)
        self.init_game()
        self.pack()

    def init_game(self):
        self.count_steps = 0
        self.in_game = True
        self.animation_buffer = []
        self.inside_column = False
        self.main_switcher_column_inside = False

        # setting images
        try:
            self.bird_standard = PhotoImage(file=GIFS["standard"])

        except IOError:
            sys.exit(1)

        self.draw_rectangles()
        self.bird_create()
        self.bind_all("<Key>", self.key_down)
        self.after(int(1000 / FPS), self.main_loop)

        if NEW_START:
            self.in_game = False
            self.new_start_game()

    # rectangles
    # controllers
    def draw_rectangles(self):
        start = int(START_COLUMN_FROM)
        while start < HEIGHT * 2:
            one, two = self.generate_coordinates()
            self.create_rectangle_by_coordinates(start, one, two)

            start += COLUMN_DEPTH + COLUMN_SIZE

    @staticmethod
    def check_inside_rectangle(square_coordinates, point):
        x, y = point

        new_square_coordinates = [
            (square_coordinates[0], square_coordinates[1]),
            (square_coordinates[0], square_coordinates[3]),
            (square_coordinates[2], square_coordinates[3]),
            (square_coordinates[2], square_coordinates[1]),
        ]

        polygon = Polygon(new_square_coordinates)
        new_point = Point(x, y)

        return polygon.contains(new_point)

    @staticmethod
    def generate_coordinates():
        random_max = HEIGHT - BIRD_WINDOW_SIZE
        one = random.randint(random_max / 2 - RANDOM_MAX_DIFFERENCE / 2, random_max / 2)

        if random.randint(0, 1):
            return random_max - one, one

        return one, random_max - one

    def move_rectangles(self):
        columns = self.find_withtag("column")
        for column in columns:
            self.move(column, -DELAY, 0)

    def create_rectangle_by_coordinates(self, x, y1, y2):
        self.create_rectangle(x, y1, x + COLUMN_SIZE, 0, tag="column", fill="green", outline="")
        self.create_rectangle(x, HEIGHT - y2, x + COLUMN_SIZE, HEIGHT, tag="column", fill="green", outline="")

    def create_next_rectangle(self):
        columns = self.find_withtag("column")
        column_x1, column_y1, column_x2, column_y2 = self.coords(columns[-1])
        if column_x1 < WIDTH + DELAY + 100:
            one, two = self.generate_coordinates()
            self.create_rectangle_by_coordinates(column_x1 + COLUMN_DEPTH + COLUMN_SIZE, one, two)

    def remove_rectangles(self):
        column1 = self.find_withtag("column")[0]
        column2 = self.find_withtag("column")[1]

        x1, y1, x2, y2 = self.coords(column1)

        if x1 < -COLUMN_SIZE:
            self.delete(column1)
            self.delete(column2)

    # main for rectangles
    def rectangle_live_cycle(self):
        self.move_rectangles()
        self.create_next_rectangle()
        self.remove_rectangles()

    # bird
    # controllers
    def move_bird(self):
        if self.animation_buffer:
            next_item = self.animation_buffer.pop(0)
            bird = self.find_withtag("bird")
            self.move(bird, 0, next_item)

    def update_counter(self):
        self.count_steps += 1

        old_counter = self.find_withtag("counter")
        self.delete(old_counter)

        self.create_text(40, 30, text=self.count_steps, fill="#222", font="Times 30", tag="counter")

    def bird_create(self):
        self.create_image(BIRD_COORDINATE[0], BIRD_COORDINATE[1], image=self.bird_standard, tag="bird")
        self.create_text(40, 30, text=self.count_steps, fill="#222", font="Times 30", tag="counter")

    def check_collisions(self):
        column = self.find_withtag("column")[0]
        column_coordinates = self.coords(column)

        if not self.inside_column and self.main_switcher_column_inside and \
                column_coordinates[0] <= BIRD_IMAGE_SIZE[1] / 2 + BIRD_COORDINATE[0]:
            self.inside_column = True

        if not self.main_switcher_column_inside and column_coordinates[0] >= BIRD_IMAGE_SIZE[1] / 2 + BIRD_COORDINATE[
            0]:
            self.main_switcher_column_inside = True

        if self.inside_column:
            column_coordinates_1 = column_coordinates
            column_coordinates_2 = self.coords(self.find_withtag("column")[1])

            bird = self.find_withtag("bird")
            x, y = self.coords(bird)

            y -= BIRD_IMAGE_SIZE[0] / 2
            x -= BIRD_IMAGE_SIZE[1] / 2

            for y_dop, x_dop in BIRD_COLLISION_POINTS:
                new_x = x + x_dop
                new_y = y + y_dop

                if self.check_inside_rectangle(column_coordinates_1, [new_x, new_y]) or \
                        self.check_inside_rectangle(column_coordinates_2, [new_x, new_y]):
                    self.game_over()

            if column_coordinates[0] + COLUMN_SIZE + BIRD_IMAGE_SIZE[1] / 2 < BIRD_COORDINATE[0]:
                self.update_counter()
                self.inside_column = False
                self.main_switcher_column_inside = False

    # main
    # loop
    def main_loop(self):
        if self.in_game:
            self.rectangle_live_cycle()
            self.move_bird()
            self.check_collisions()
            self.after(int(1 / FPS * 1000), self.main_loop)

    def key_down(self, e):
        key = e.keysym

        if key == "Escape":
            self.pause_game()

        if key == "Down":
            self.animation_buffer.extend(BIRD_DOWN_ANIMATION)
        elif key == "Up":
            self.animation_buffer.extend(BIRD_UP_ANIMATION)

        if key == "Return":
            if not self.in_game:
                self.delete(ALL)
                self.init_game()
                self.pack()

    def save_result_in_file(self):
        # коряво, я знаю, просто не хочется переделывать)
        if not os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, "wb") as log:
                log.write(base64.b64encode(str(self.count_steps).encode()))
            self.high_score = self.count_steps
        else:
            with open(RESULTS_FILE) as log:
                data = log.read()

            try:
                high = int(base64.b64decode(data).decode())
            except:
                os.remove(RESULTS_FILE)
                raise IOError("Вы испортили файл data.txt((")

            if high < self.count_steps:
                with open(RESULTS_FILE, "wb") as log:
                    log.write(base64.b64encode(str(self.count_steps).encode()))
                    self.high_score = self.count_steps
            else:
                self.high_score = high

    def save_result(self):
        # Это еще +- но все равно плохо)
        try:
            if not os.environ.get("FLAPPY_BIRD_HIGH_SCORE"):
                os.environ["FLAPPY_BIRD_HIGH_SCORE"] = str(self.count_steps)

            high = int(os.environ["FLAPPY_BIRD_HIGH_SCORE"])
            if self.count_steps > high:
                os.environ["FLAPPY_BIRD_HIGH_SCORE"] = str(self.count_steps)
                self.high_score = self.count_steps
            else:
                self.high_score = high
        except:
            self.save_result_in_file()

    def game_over(self):
        self.in_game = False

        self.delete(ALL)
        self.save_result_in_file()

        self.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#85F6C2", outline="")
        self.create_text(WIDTH / 2, HEIGHT / 3 - 80, text="GAME OVER", font="Times 40", fill="#222")
        self.create_text(WIDTH / 2, HEIGHT / 3, text=f"Your score: {self.count_steps}", fill="#222", font="Times 25")
        self.create_text(WIDTH / 2, HEIGHT / 3 + 40, text=f"High score: {self.high_score}", fill="red", font="Times 25")
        self.create_text(WIDTH / 2, HEIGHT / 4 * 3, text='Press "Enter" to restart game!', fill="#222")

    def pause_game(self):
        if self.in_game:
            self.in_game = False
            self.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#85F6C2", outline="", tag="main_background")
            self.create_text(WIDTH / 2, HEIGHT / 3, text="GAME PAUSED", font="Times 40", fill="#222",
                             tag="main_background")
            self.create_text(WIDTH / 2, HEIGHT / 4 * 3, text='Press "Enter" to restart game!', fill="#222",
                             tag="main_background")
        else:
            main_background = self.find_withtag("main_background")
            for i in main_background:
                self.delete(i)

            self.in_game = True
            self.after(int(1 / FPS * 1000), self.main_loop)

    def new_start_game(self):
        global NEW_START

        self.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#85F6C2", outline="", tag="main_background")
        self.create_text(WIDTH / 2, HEIGHT / 3, text="HELLO!", font="Times 40", fill="#222",
                         tag="main_background")
        self.create_text(WIDTH / 2, HEIGHT / 4 * 3, text='Press "Enter" to start game!', fill="#222",
                         tag="main_background")

        NEW_START = False


def main():
    tk = Tk()
    tk.title("flappy bird game")
    MainModel()
    tk.mainloop()


if __name__ == "__main__":
    main()
