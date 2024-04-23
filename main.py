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
from PySide6 import QtCore


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


class Snake:
    def __init__(self):
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

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(100)

        self.scene.keyPressEvent = self.scene_key_press

        self.create_food()
        self.snake = Snake()

        self.window.show()

    def scene_key_press(self, event):
        if event.key() == QtCore.Qt.Key_Left:
            self.snake.change_direction((-1, 0))
        elif event.key() == QtCore.Qt.Key_Right:
            self.snake.change_direction((1, 0))
        elif event.key() == QtCore.Qt.Key_Up:
            self.snake.change_direction((0, -1))
        elif event.key() == QtCore.Qt.Key_Down:
            self.snake.change_direction((0, 1))
        self.tick()  # makes the snake go faster as long as the button is pressed!

    def tick(self):
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
        if (
            abs(head.x()) > self.graphicsView.viewport().width() / 2
            or abs(head.y()) > self.graphicsView.viewport().height() / 2
        ):
            self.game_over()
        elif (
            self.food.x() - self.food.width / 2
            <= head.x()
            <= self.food.x() + self.food.width / 2
            and self.food.y() - self.food.height / 2
            <= head.y()
            <= self.food.y() + self.food.height / 2
        ):
            self.snake.score += 1
            self.food = 0
            items_to_remove = []
            for item in self.scene.items():
                if isinstance(item, Food):
                    items_to_remove.append(item)
            for item in items_to_remove:
                self.scene.removeItem(item)
            self.create_food()
            self.snake.grow()

    def game_over(self):
        self.timer.stop()
        msg = QMessageBox()
        msg.setWindowTitle("Game Over")
        msg.setText(f"Your score: {self.snake.score}")
        msg.setIcon(QMessageBox.Information)
        msg.exec()
        self.scene.clear()
        self.snake = Snake()
        self.create_food()
        self.timer.start(100)


if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
