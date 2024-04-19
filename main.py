import sys, os
from random import random
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
        super().__init__(x - self.width / 2, y - self.height / 2, self.width, self.height)
        self.setBrush(QBrush(QColor("orange")))


class SnakeCube(QGraphicsRectItem):
    def __init__(self, x, y):
        self.width = 5
        self.height = 5
        super().__init__(x - self.width / 2, y - self.height / 2, self.width, self.height)
        self.setBrush(QBrush(QColor("green")))

    def grow(self):
        pass
        # self.width += 20
        # self.height += 20


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
        self.scene.setBackgroundBrush(QBrush(QColor("pink")))
        self.graphicsView.setScene(self.scene)

        self.graphicsView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphicsView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphicsView.setAlignment(QtCore.Qt.AlignCenter)
        self.scene.setSceneRect(-400, -200, 800, 400)

        self.snake = SnakeCube(0, 0)
        self.scene.addItem(self.snake)

        self.scene.keyPressEvent = self.scene_key_press

        self.score = 0
        self.create_food()

        self.window.show()

    def scene_key_press(self, event):
        if event.key() == QtCore.Qt.Key_Left:
            self.snake.setPos(self.snake.x() - self.snake.width, self.snake.y())
        elif event.key() == QtCore.Qt.Key_Right:
            self.snake.setPos(self.snake.x() + self.snake.width, self.snake.y())
        elif event.key() == QtCore.Qt.Key_Up:
            self.snake.setPos(self.snake.x(), self.snake.y() - self.snake.height)
        elif event.key() == QtCore.Qt.Key_Down:
            self.snake.setPos(self.snake.x(), self.snake.y() + self.snake.height)
        self.check_collision()

    def create_food(self):
        x = self.scene.width() * (0.1 + 0.8 * (random()) - 0.5)
        y = self.scene.height() * (0.1 + 0.8 * (random()) - 0.5)
        self.food = Food(x, y)
        self.scene.addItem(self.food)

    def check_collision(self):
        if self.snake.collidesWithItem(self.food):
            self.scene.removeItem(self.food)
            self.score += 1
            self.create_food()
            self.snake.grow()
        elif (
            abs(self.snake.x()) > self.graphicsView.viewport().width() / 2
            or abs(self.snake.y()) > self.graphicsView.viewport().height() / 2
        ):
            self.game_over()

    def game_over(self):
        msg = QMessageBox()
        msg.setWindowTitle("Game Over")
        msg.setText(f"Your score: {self.score}")
        msg.setIcon(QMessageBox.Information)
        msg.exec()
        self.scene.clear()
        self.create_food()
        self.snake = SnakeCube(0, 0)
        self.scene.addItem(self.snake)
        self.score = 0


if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
