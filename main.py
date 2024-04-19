import sys, os
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
    def __init__(self, x, y):
        self.width = 15
        self.height = 15
        super().__init__(
            x - self.width / 2, y - self.height / 2, self.width, self.height
        )
        self.setBrush(QBrush(QColor("orange")))


class SnakeCube(QGraphicsRectItem):
    def __init__(self, x, y):
        self.width = 5
        self.height = 5
        super().__init__(
            x - self.width / 2, y - self.height / 2, self.width, self.height
        )
        self.setBrush(QBrush(QColor("green")))


class Snake:
    def __init__(self):
        self.score = 0
        self.direction = self.get_random_direction()
        self.cube_list = [SnakeCube(0, 0) for i in range(2)]

    def get_random_direction(self):
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        return random.choice(directions)

    def move(self):
        print("\n")
        for sc in self.cube_list:
            print(f"{sc.x()},{sc.y()},{self.direction[0]},{self.direction[1]}")
        print("\n")
        cln=len(self.cube_list)
        if cln>1:
            for i in range(cln - 1, 0, -1):
                self.cube_list[i].setX(self.cube_list[i - 1].x())
                self.cube_list[i].setY(self.cube_list[i - 1].y())
        self.cube_list[0].setX(self.cube_list[0].x()+self.direction[0]*self.cube_list[0].width)
        self.cube_list[0].setY(self.cube_list[0].y()+self.direction[1]*self.cube_list[0].height)

    def grow(self):
        last_cube = self.cube_list[-1]
        new_x = last_cube.x() - self.direction[0] * last_cube.width
        new_y = last_cube.y() - self.direction[1] * last_cube.height
        new_cube = SnakeCube(new_x, new_y)
        self.move()
        self.cube_list.append(new_cube)
        self.move()

    def change_direction(self, direction):
        dx, dy = direction
        if (dx, dy)!= (-self.direction[0], -self.direction[1]):
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

        self.snake = Snake()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_snake)
        self.timer.start(1000)

        self.scene.keyPressEvent = self.scene_key_press

        self.create_food()

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
        self.update_snake()

    def update_snake(self):
        for sc in self.snake.cube_list:
            self.scene.removeItem(sc)
        self.snake.move()
        self.check_collision()
        for sc in self.snake.cube_list:
            self.scene.addItem(sc)

    def create_food(self):
        x = self.scene.width() * (0.1 + 0.8 * (random.random()) - 0.5)
        y = self.scene.height() * (0.1 + 0.8 * (random.random()) - 0.5)
        self.food = Food(x, y)
        self.scene.addItem(self.food)

    def check_collision(self):
        head = self.snake.cube_list[0]
        if len(self.snake.cube_list) < 1:
            self.game_over()
        elif (
            abs(head.x()) > self.graphicsView.viewport().width() / 2
            or abs(head.y()) > self.graphicsView.viewport().height() / 2
        ):
            self.game_over()
        elif head.collidesWithItem(self.food):
            self.scene.removeItem(self.food)
            self.snake.score += 1
            self.snake.grow()
            self.create_food()

    def game_over(self):
        msg = QMessageBox()
        msg.setWindowTitle("Game Over")
        msg.setText(f"Your score: {self.score}")
        msg.setIcon(QMessageBox.Information)
        msg.exec()
        self.scene.clear()


if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
