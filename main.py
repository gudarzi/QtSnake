import sys, os, random
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


# Function to get the resource path for loading UI files
def get_resource_path(path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, path)


# Class representing Food item for the snake to consume
class Food(QGraphicsRectItem):
    def __init__(self):
        self.width = 15
        self.height = 15
        super().__init__(0, 0, self.width, self.height)  # x, y are set later
        self.setBrush(QBrush(QColor("orange")))


# Class representing individual SnakeCube (each segment of the snake)
class SnakeCube(QGraphicsRectItem):
    def __init__(self):
        self.width = 15
        self.height = 15
        super().__init__(0, 0, self.width, self.height)  # x, y are set later
        self.setBrush(QBrush(QColor("green")))


# Class representing Obstacle
class Obstacle(QGraphicsRectItem):
    def __init__(self, x, y, width=30, height=30):
        super().__init__(x, y, width, height)
        self.setBrush(QBrush(QColor("red")))  # Set obstacle color to red for visibility
        self.setPen(QtCore.Qt.NoPen)  # Remove border for cleaner look


# Class representing the Snake and its behavior
class Snake(QtWidgets.QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.score = 0
        self.direction = (1, 0)  # Start moving right
        self.cube_list = [SnakeCube() for i in range(2)]  # Snake is initially 2 cubes large
        self.move()

    def move(self):
        head = self.cube_list[0]
        tail = self.cube_list[-1]
        tail.setX(head.x() + self.direction[0] * head.width)  # Set tail position based on direction snake is heading
        tail.setY(head.y() + self.direction[1] * head.height)
        self.cube_list.insert(0, self.cube_list.pop())  # Insert tail at the beginning and remove from end

    def grow(self):
        new_cube = SnakeCube()
        self.cube_list.append(new_cube)
        self.move()

    def change_direction(self, direction):
        dx, dy = direction
        if (dx, dy) != (-self.direction[0], -self.direction[1]):  # Prevent snake from going in the opposite direction
            self.direction = (dx, dy)


# Main Window class for the Snake Game
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
        self.escLabel = QtWidgets.QLabel("\"esc\" to pause", self.window)
        self.scoreLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.scoreLabel.setStyleSheet("color: white; font-size: 20px;")
        self.scoreLabel.setGeometry(350, 10, 100, 30)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(150)  # Set a slower timer for better game speed

        self.scene.keyPressEvent = self.scene_key_press

        # Initialize game elements
        self.obstacles = []  # List to hold obstacles
        self.food_count = 0  # Counter for food consumed
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
            # Handle menu navigation and game start
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
            # Handle snake movement with arrow keys or WASD
            if event.key() == QtCore.Qt.Key_Left or event.key() == QtCore.Qt.Key_A:
                self.snake.change_direction((-1, 0))
            elif event.key() == QtCore.Qt.Key_Right or event.key() == QtCore.Qt.Key_D:
                self.snake.change_direction((1, 0))
            elif event.key() == QtCore.Qt.Key_Up or event.key() == QtCore.Qt.Key_W:
                self.snake.change_direction((0, -1))
            elif event.key() == QtCore.Qt.Key_Down or event.key() == QtCore.Qt.Key_S:
                self.snake.change_direction((0, 1))
            elif event.key() == QtCore.Qt.Key_Escape:
                self.game_pause()
            self.tick()  # Move snake with every key press

    def tick(self):
        if not self.in_menu:
            # Update the scene without removing all elements
            self.render_elements()
            self.snake.move()
            self.check_collision()

    def render_elements(self):
        # Re-add food item if it exists
        if self.food and self.food.scene() != self.scene:
            self.scene.addItem(self.food)

        # Re-add all snake cubes to the scene
        for sc in self.snake.cube_list:
            if sc.scene() != self.scene:
                self.scene.addItem(sc)

        # Re-add all obstacles to the scene
        for obstacle in self.obstacles:
            if obstacle.scene() != self.scene:
                self.scene.addItem(obstacle)

    def create_food(self):
        # Create a new food object and place it in the scene
        x = self.scene.width() * (0.1 + 0.8 * (random.random()) - 0.5)
        y = self.scene.height() * (0.1 + 0.8 * (random.random()) - 0.5)
        self.food = Food()
        self.food.setX(x)
        self.food.setY(y)
        self.scene.addItem(self.food)  # Add the food item to the scene

    def create_obstacle(self):
        # Create a new obstacle and place it randomly in the scene
        x = self.scene.width() * (0.1 + 0.8 * (random.random()) - 0.5)
        y = self.scene.height() * (0.1 + 0.8 * (random.random()) - 0.5)
        obstacle = Obstacle(x, y)
        self.obstacles.append(obstacle)
        self.scene.addItem(obstacle)  # Add the obstacle to the scene

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
            self.snake.score += 1  # Score is updated by 1 for every food consumed
            self.food_count += 1  # Increment food count
            self.update_score()
            self.scene.removeItem(self.food)
            self.create_food()
            self.snake.grow()

            # Add obstacle every 5 food items consumed
            if self.food_count % 5 == 0:
                self.create_obstacle()

        # Check collision with obstacles
        for obstacle in self.obstacles:
            if head.collidesWithItem(obstacle):
                self.game_over()
                return

    def game_pause(self):
        self.timer.stop()
        msg1 = QMessageBox()
        msg1.setWindowTitle("Game Paused")
        msg1.setText(f"Your score: {self.snake.score}\n Do you want to continue?")
        msg1.setIcon(QMessageBox.Information)
        continue_button = msg1.addButton("Continue", QMessageBox.ActionRole)
        abort_button = msg1.addButton("Quit", QMessageBox.RejectRole)
        msg1.exec()
        if msg1.clickedButton() == continue_button:  # Reinitialize timer to resume game
            self.timer.start(150)
        elif msg1.clickedButton() == abort_button:
            self.game_over()

    def game_over(self):
        self.timer.stop()
        msg = QMessageBox()
        msg.setWindowTitle("Game Over")
        msg.setText(f"Your score: {self.snake.score}")
        msg.setIcon(QMessageBox.Information)
        msg.exec()

        # Reset the game state
        self.snake = Snake()
        self.obstacles.clear()  # Clear obstacles
        self.scene.clear()  # Clear the entire scene to remove all items
        self.food = None  # Reset food

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
        self.obstacles.clear()  # Clear any existing obstacles
        self.food_count = 0  # Reset food count
        self.timer.start(150)  # Reset game timer
        self.update_score()


if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
