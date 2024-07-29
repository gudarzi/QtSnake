import sys, os, time, itertools
import random
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsScene,
    QGraphicsView,
    QMainWindow,
    QMessageBox,
    QGraphicsRectItem,
)
from PySide6.QtUiTools import QUiLoader
from PySide6 import QtCore, QtWidgets


def get_resource_path(path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, path)


class Food(QGraphicsRectItem):
    def __init__(self):
        self.width = 15
        self.height = 15
        super().__init__(0, 0, self.width, self.height)  # x, y are set later
        self.setBrush(QBrush(QColor("orange")))


class SnakeCube(QGraphicsRectItem):
    def __init__(self):
        self.width = 5
        self.height = 5
        super().__init__(0, 0, self.width, self.height)  # x, y are set later
        self.setBrush(QBrush(QColor("green")))


class Snake(QtWidgets.QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.score = 0
        self.direction = self.get_random_direction()
        self.cube_list = [SnakeCube() for i in range(2)]
        self.move()
        
    def get_random_direction(self):
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        return random.choice(directions)

    def move(self):
        # st=time.perf_counter_ns()
        
        # method 1
        # cln = len(self.cube_list)
        # for i in range(cln - 1, 0, -1):
        #     self.cube_list[i].setX(self.cube_list[i - 1].x())
        #     self.cube_list[i].setY(self.cube_list[i - 1].y())
        # self.cube_list[0].setX(self.cube_list[0].x() + self.direction[0] * self.cube_list[0].width)
        # self.cube_list[0].setY(self.cube_list[0].y() + self.direction[1] * self.cube_list[0].height)
        
        # method 2
        head = self.cube_list[0]
        tail = self.cube_list[-1]
        tail.setX(head.x() + self.direction[0] * head.width)
        tail.setY(head.y() + self.direction[1] * head.height)
        # self.cube_list = [self.cube_list[-1]] + self.cube_list[:-1]
        
        # method 2.5
        self.cube_list.insert(0, self.cube_list.pop())

        # et=time.perf_counter_ns()
        # print(et-st)

    def grow(self):
        new_cube = SnakeCube()
        self.cube_list.append(new_cube)
        self.move()

    def change_direction(self, direction):
        dx, dy = direction
        if (dx, dy) != (-self.direction[0], -self.direction[1]):
            self.direction = (dx, dy)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        ui_file_path = "main.ui"
        ui_file_abs_path = get_resource_path(ui_file_path)
        ui_file = QtCore.QFile(ui_file_abs_path)
        if not ui_file.open(QtCore.QIODevice.ReadOnly):
            print(f"Cannot open {ui_file_abs_path}: {ui_file.errorString()}")
            sys.exit(-1)

        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()
        if not self.window:
            print(loader.errorString())
            sys.exit(-1)

        self.graphicsView = self.window.findChild(QGraphicsView, "graphicsView")
        self.scene = QGraphicsScene(self.graphicsView)
        self.scene.setBackgroundBrush(QBrush(QColor("black")))
        self.graphicsView.setScene(self.scene)

        self.graphicsView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphicsView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphicsView.setAlignment(QtCore.Qt.AlignCenter)
        self.scene.setSceneRect(-400, -200, 800, 400)

        self.scoreLabel = QtWidgets.QLabel("Score: 0", self.window)
        self.scoreLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.scoreLabel.setStyleSheet("color: white; font-size: 20px;")
        self.scoreLabel.setGeometry(350, 10, 100, 30)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(100)

        self.scene.keyPressEvent = self.scene_key_press

        self.create_food()
        self.snake = Snake()

        self.in_menu = True
        self.menu_selection = 0
        self.start_button = None
        self.quit_button = None
        self.show_start_menu()

        self.window.show()

    def update_score(self):
        self.scoreLabel.setText(f"Score: {self.snake.score}")

    def scene_key_press(self, event):
        if self.in_menu:
            if event.key() == QtCore.Qt.Key_Up or event.key() == QtCore.Qt.Key_W:
                self.menu_selection = 0
                self.update_menu_selection()
            elif event.key() == QtCore.Qt.Key_Down or event.key() == QtCore.Qt.Key_S:
                self.menu_selection = 1
                self.update_menu_selection()
            elif event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
                if self.menu_selection == 0:
                    self.start_game()
                elif self.menu_selection == 1:
                    QApplication.quit()
        else:
            if event.key() == QtCore.Qt.Key_Left or event.key() == QtCore.Qt.Key_A:  # added WASD support
                self.snake.change_direction((-1, 0))
            elif event.key() == QtCore.Qt.Key_Right or event.key() == QtCore.Qt.Key_D:
                self.snake.change_direction((1, 0))
            elif event.key() == QtCore.Qt.Key_Up or event.key() == QtCore.Qt.Key_W:
                self.snake.change_direction((0, -1))
            elif event.key() == QtCore.Qt.Key_Down or event.key() == QtCore.Qt.Key_S:
                self.snake.change_direction((0, 1))
            self.tick()  # makes the snake go faster as long as the button is pressed!

    def tick(self):
        if not self.in_menu:
            self.scene.clear()
            if self.food != 0:
                new_food = Food()
                new_food.setX(self.food.x())
                new_food.setY(self.food.y())
                self.scene.addItem(new_food)
            self.snake.move()
            for sc in self.snake.cube_list:
                new_sc = SnakeCube()
                new_sc.setX(sc.x())
                new_sc.setY(sc.y())
                self.scene.addItem(new_sc)
            self.check_collision()

    def create_food(self):
        self.food = 0
        x = self.scene.width() * (0.1 + 0.8 * (random.random()) - 0.5)
        y = self.scene.height() * (0.1 + 0.8 * (random.random()) - 0.5)
        self.food = Food()
        self.food.setX(x)
        self.food.setY(y)

    def check_collision(self):
        head = self.snake.cube_list[0]

        # Check collision with boundaries using scene's bounding rectangle
        if not self.scene.sceneRect().contains(head.sceneBoundingRect()):
            self.game_over()
            return

        # Check self-collision by comparing positions
        head_pos = (head.x(), head.y())
        for cube in self.snake.cube_list[1:]:
            if head_pos == (cube.x(), cube.y()):
                self.game_over()
                return

        # Check collision with the food
        if head.collidesWithItem(self.food):
            self.snake.score += 1
            self.update_score()
            self.scene.removeItem(self.food)
            self.create_food()
            self.snake.grow()

    def game_over(self):
        self.timer.stop()
        msg = QMessageBox()
        msg.setWindowTitle("Game Over")
        msg.setText(f"Your score: {self.snake.score}")
        msg.setIcon(QMessageBox.Information)
        msg.exec()

        self.snake = Snake()

        self.in_menu = True
        self.menu_selection = 0
        self.start_button = None
        self.quit_button = None

        self.show_start_menu()
        self.update_score()

    def show_start_menu(self):
        self.in_menu = True
        self.scene.clear()

        self.start_button = QtWidgets.QLabel("START", self.window)
        self.start_button.setAlignment(QtCore.Qt.AlignCenter)
        self.start_button.setStyleSheet("color: white; font-size: 30px;")
        self.start_button.setGeometry(350, 150, 100, 50)
        self.start_button.show()
        self.start_button.mousePressEvent = self.start_button_clicked  

        self.quit_button = QtWidgets.QLabel("QUIT", self.window)
        self.quit_button.setAlignment(QtCore.Qt.AlignCenter)
        self.quit_button.setStyleSheet("color: white; font-size: 30px;")
        self.quit_button.setGeometry(350, 250, 100, 50)
        self.quit_button.show()
        self.quit_button.mousePressEvent = self.quit_button_clicked  

        self.dummy_text = QtWidgets.QLabel("Use Keyboard Keys or Mouse To Navigate!", self.window)
        self.dummy_text.setAlignment(QtCore.Qt.AlignCenter)
        self.dummy_text.setStyleSheet("color: green; font-size: 14px;")
        self.dummy_text.setGeometry(250, 350, 300, 50)
        self.dummy_text.show()

        self.update_menu_selection()
        self.window.update()
            
    def update_menu_selection(self):
        if self.menu_selection == 0:
            self.start_button.setStyleSheet("color: yellow; font-size: 30px;")
            self.quit_button.setStyleSheet("color: white; font-size: 30px;")
        else:
            self.start_button.setStyleSheet("color: white; font-size: 30px;")
            self.quit_button.setStyleSheet("color: yellow; font-size: 30px;")

    def start_button_clicked(self, event):
        self.start_game()

    def quit_button_clicked(self, event):
        QApplication.quit()

    def start_game(self):
        self.start_button.deleteLater()
        self.quit_button.deleteLater()
        self.in_menu = False
        self.snake = Snake()
        self.create_food()
        self.timer.start(100)
        self.update_score()

if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
