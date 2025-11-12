import json
import os
import random
import sys

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
    def __init__(self, food_type="normal"):
        self.width = 15
        self.height = 15
        super().__init__(0, 0, self.width, self.height)  # x, y are set later
        self.food_type = food_type
        
        # Set color and points based on food type
        if food_type == "golden":
            self.setBrush(QBrush(QColor("gold")))
            self.points = 3
        elif food_type == "speed_boost":
            self.setBrush(QBrush(QColor("cyan")))
            self.points = 1
        elif food_type == "slow_down":
            self.setBrush(QBrush(QColor("purple")))
            self.points = 1
        else:  # normal
            self.setBrush(QBrush(QColor("orange")))
            self.points = 1


# Class representing individual SnakeCube (each segment of the snake)
class SnakeCube(QGraphicsRectItem):
    def __init__(self):
        self.width = 15
        self.height = 15
        super().__init__(0, 0, self.width, self.height)  # x, y are set later
        self.setBrush(QBrush(QColor("green")))


# Class representing Obstacle
class Obstacle(QGraphicsRectItem):
    def __init__(self, x, y, width=30, height=30, obstacle_type="static"):
        super().__init__(x, y, width, height)
        self.obstacle_type = obstacle_type
        
        if obstacle_type == "wall":
            self.setBrush(QBrush(QColor("gray")))
        else:
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
        self.levelLabel = QtWidgets.QLabel("Level: 1", self.window)
        self.escLabel = QtWidgets.QLabel("\"esc\" to pause", self.window)
        self.scoreLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.scoreLabel.setStyleSheet("color: white; font-size: 20px;")
        self.scoreLabel.setGeometry(350, 10, 100, 30)
        
        self.levelLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.levelLabel.setStyleSheet("color: cyan; font-size: 20px;")
        self.levelLabel.setGeometry(10, 10, 100, 30)
        
        self.powerUpLabel = QtWidgets.QLabel("", self.window)
        self.powerUpLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.powerUpLabel.setStyleSheet("color: yellow; font-size: 16px;")
        self.powerUpLabel.setGeometry(250, 350, 300, 30)
        self.powerUpLabel.hide()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.tick)
        self.base_speed = 150  # Base game speed
        self.timer.start(self.base_speed)  # Set a slower timer for better game speed

        self.scene.keyPressEvent = self.scene_key_press

        # Initialize game elements
        self.obstacles = []  # List to hold obstacles
        self.food_count = 0  # Counter for food consumed
        self.level = 1  # Current game level
        self.points_to_next_level = 5  # Points needed to advance to next level
        self.high_score = self.load_high_score()  # Track high score
        self.speed_boost_active = False  # Track if speed boost is active
        self.snake = Snake()  # Initialize snake before food
        self.create_food()

        self.in_menu = True
        self.menu_selection = 0
        self.start_button = None
        self.quit_button = None
        self.show_start_menu()

        self.window.show()

    def update_score(self):
        self.scoreLabel.setText(f"Score: {self.snake.score}")
        
    def update_level(self):
        self.levelLabel.setText(f"Level: {self.level}")
    
    def load_high_score(self):
        # Load high score from file
        high_score_file = "snake_highscore.json"
        try:
            if os.path.exists(high_score_file):
                with open(high_score_file, 'r') as f:
                    data = json.load(f)
                    return data.get('high_score', 0)
        except Exception as e:
            print(f"Error loading high score: {e}")
        return 0
    
    def save_high_score(self):
        # Save high score to file
        high_score_file = "snake_highscore.json"
        try:
            with open(high_score_file, 'w') as f:
                json.dump({'high_score': self.high_score}, f)
        except Exception as e:
            print(f"Error saving high score: {e}")

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
        # Try multiple times to find a valid position that doesn't collide with obstacles
        max_attempts = 20
        for attempt in range(max_attempts):
            x = self.scene.width() * (0.1 + 0.8 * (random.random()) - 0.5)
            y = self.scene.height() * (0.1 + 0.8 * (random.random()) - 0.5)
            
            # Randomly determine food type (10% golden, 10% speed boost, 10% slow down, 70% normal)
            rand_val = random.random()
            if rand_val < 0.10:
                food_type = "golden"
            elif rand_val < 0.20:
                food_type = "speed_boost"
            elif rand_val < 0.30:
                food_type = "slow_down"
            else:
                food_type = "normal"
            
            temp_food = Food(food_type)
            temp_food.setX(x)
            temp_food.setY(y)
            
            # Check if food collides with any obstacles
            collision_with_obstacles = False
            for obstacle in self.obstacles:
                if temp_food.collidesWithItem(obstacle):
                    collision_with_obstacles = True
                    break
            
            # Check if food collides with snake
            collision_with_snake = False
            for cube in self.snake.cube_list:
                if temp_food.collidesWithItem(cube):
                    collision_with_snake = True
                    break
            
            # If no collision, place the food
            if not collision_with_obstacles and not collision_with_snake:
                self.food = temp_food
                self.scene.addItem(self.food)  # Add the food item to the scene
                return
        
        # If we couldn't find a valid position, just place it anyway (fallback)
        self.food = Food("normal")
        x = self.scene.width() * (0.1 + 0.8 * (random.random()) - 0.5)
        y = self.scene.height() * (0.1 + 0.8 * (random.random()) - 0.5)
        self.food.setX(x)
        self.food.setY(y)
        self.scene.addItem(self.food)

    def create_obstacle(self):
        # Create a new obstacle and place it randomly in the scene
        # Try multiple times to find a valid position
        max_attempts = 10
        for attempt in range(max_attempts):
            x = self.scene.width() * (0.1 + 0.8 * (random.random()) - 0.5)
            y = self.scene.height() * (0.1 + 0.8 * (random.random()) - 0.5)
            
            # Create temporary obstacle to check collisions
            temp_obstacle = Obstacle(x, y)
            
            # Check if obstacle collides with snake
            collision_with_snake = False
            for cube in self.snake.cube_list:
                if temp_obstacle.collidesWithItem(cube):
                    collision_with_snake = True
                    break
            
            # Check if obstacle collides with food
            collision_with_food = temp_obstacle.collidesWithItem(self.food)
            
            # Check if obstacle collides with existing obstacles
            collision_with_obstacles = False
            for existing_obstacle in self.obstacles:
                if temp_obstacle.collidesWithItem(existing_obstacle):
                    collision_with_obstacles = True
                    break
            
            # If no collision, place the obstacle
            if not collision_with_snake and not collision_with_food and not collision_with_obstacles:
                obstacle = Obstacle(x, y)
                self.obstacles.append(obstacle)
                self.scene.addItem(obstacle)
                return
        
        # If we couldn't find a valid position after max_attempts, don't create obstacle
        print(f"Warning: Could not find valid position for obstacle after {max_attempts} attempts")

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
            # Apply food effects based on type
            food_type = self.food.food_type
            self.snake.score += self.food.points  # Score updated based on food type
            self.food_count += 1  # Increment food count
            
            # Handle special food effects
            if food_type == "golden":
                # Show golden food message briefly
                self.show_powerup_message("⭐ Golden Food! +3 Points! ⭐", "gold")
            elif food_type == "speed_boost":
                # Temporarily increase speed
                current_speed = self.timer.interval()
                new_speed = max(30, current_speed - 50)
                self.timer.setInterval(new_speed)
                self.speed_boost_active = True
                self.show_powerup_message("⚡ Speed Boost! Going Fast! ⚡", "cyan")
                # Reset speed after 5 seconds
                QtCore.QTimer.singleShot(5000, self.reset_speed)
            elif food_type == "slow_down":
                # Temporarily decrease speed
                current_speed = self.timer.interval()
                new_speed = min(200, current_speed + 50)
                self.timer.setInterval(new_speed)
                self.speed_boost_active = True
                self.show_powerup_message("🐌 Slow Motion! Take it Easy! 🐌", "purple")
                # Reset speed after 5 seconds
                QtCore.QTimer.singleShot(5000, self.reset_speed)
            
            self.update_score()
            self.scene.removeItem(self.food)
            self.create_food()
            self.snake.grow()

            # Check if level up is needed (consistent: every N apples)
            if self.food_count >= self.level * self.points_to_next_level:
                self.level_up()

            # Add obstacle every 5 food items consumed
            if self.food_count % 5 == 0:
                self.create_obstacle()

        # Check collision with obstacles
        for obstacle in self.obstacles:
            if head.collidesWithItem(obstacle):
                self.game_over()
                return

    def show_powerup_message(self, message, color):
        # Show power-up message temporarily
        self.powerUpLabel.setText(message)
        self.powerUpLabel.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
        self.powerUpLabel.show()
        # Hide after 3 seconds
        QtCore.QTimer.singleShot(3000, self.powerUpLabel.hide)
    
    def reset_speed(self):
        # Reset speed to level-appropriate speed
        if not self.speed_boost_active:
            return
        new_speed = max(70, self.base_speed - (self.level - 1) * 10)
        self.timer.setInterval(new_speed)
        self.speed_boost_active = False
        self.show_powerup_message("⏱️ Normal Speed Restored", "white")
    
    def create_level_obstacles(self):
        # Create level-specific obstacle patterns - more gradual introduction
        if self.level == 5:
            # Add first horizontal wall at level 5
            self.create_wall_obstacle(-300, -100, 150, 20)
        
        if self.level == 7:
            # Add second horizontal wall at level 7
            self.create_wall_obstacle(150, 80, 150, 20)
        
        if self.level == 10:
            # Add first vertical wall at level 10
            self.create_wall_obstacle(-200, -150, 20, 100)
        
        if self.level == 12:
            # Add second vertical wall at level 12
            self.create_wall_obstacle(200, 0, 20, 100)
        
        if self.level == 15:
            # Add corner obstacles at level 15
            self.create_wall_obstacle(-350, -180, 80, 20)
            self.create_wall_obstacle(-350, -180, 20, 80)
    
    def create_wall_obstacle(self, x, y, width, height):
        # Create a wall-type obstacle
        wall = Obstacle(x, y, width, height, "wall")
        self.obstacles.append(wall)
        self.scene.addItem(wall)
    
    def level_up(self):
        self.level += 1
        self.update_level()
        
        # Increase game speed more gradually (slower progression)
        new_speed = max(70, self.base_speed - (self.level - 1) * 10)
        self.timer.setInterval(new_speed)
        
        # Add obstacles more gradually - only every other level
        if self.level % 2 == 0:
            self.create_obstacle()
        
        # Add level-specific obstacle patterns only at key levels
        self.create_level_obstacles()
        
        # Show level up message in the game (no pop-up)
        self.show_powerup_message(f"🎉 LEVEL {self.level}! 🎉", "yellow")
    
    def game_pause(self):
        self.timer.stop()
        msg1 = QMessageBox()
        msg1.setWindowTitle("Game Paused")
        msg1.setText(f"Level: {self.level}\nYour score: {self.snake.score}\n Do you want to continue?")
        msg1.setIcon(QMessageBox.Information)
        continue_button = msg1.addButton("Continue", QMessageBox.ActionRole)
        abort_button = msg1.addButton("Quit", QMessageBox.RejectRole)
        msg1.exec()
        if msg1.clickedButton() == continue_button:  # Reinitialize timer to resume game
            current_speed = max(70, self.base_speed - (self.level - 1) * 10)
            self.timer.start(current_speed)
        elif msg1.clickedButton() == abort_button:
            self.game_over()

    def game_over(self):
        self.timer.stop()
        
        # Update high score
        if self.snake.score > self.high_score:
            self.high_score = self.snake.score
            self.save_high_score()  # Save new high score to file
            high_score_text = "\n🎉 NEW HIGH SCORE! 🎉"
        else:
            high_score_text = f"\nHigh Score: {self.high_score}"
        
        msg = QMessageBox()
        msg.setWindowTitle("Game Over")
        msg.setText(f"Level Reached: {self.level}\nYour Score: {self.snake.score}{high_score_text}")
        msg.setIcon(QMessageBox.Information)
        msg.exec()

        # Reset the game state
        self.snake = Snake()
        self.obstacles.clear()  # Clear obstacles
        self.scene.clear()  # Clear the entire scene to remove all items
        self.food = None  # Reset food
        self.level = 1  # Reset level

        self.in_menu = True
        self.menu_selection = 0
        self.start_button = None
        self.quit_button = None

        self.show_start_menu()
        self.update_score()
        self.update_level()

    def show_start_menu(self):
        self.in_menu = True
        self.scene.clear()
        
        # Show high score in menu
        self.high_score_menu = QtWidgets.QLabel(f"High Score: {self.high_score}", self.window)
        self.high_score_menu.setAlignment(QtCore.Qt.AlignCenter)
        self.high_score_menu.setStyleSheet("color: gold; font-size: 24px; font-weight: bold;")
        self.high_score_menu.setGeometry(250, 50, 300, 50)
        self.high_score_menu.show()

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
        self.dummy_text.deleteLater()
        self.high_score_menu.deleteLater()
        self.in_menu = False
        self.snake = Snake()
        self.level = 1  # Reset level
        self.create_food()
        self.obstacles.clear()  # Clear any existing obstacles
        self.food_count = 0  # Reset food count
        self.timer.start(self.base_speed)  # Reset game timer to base speed
        self.update_score()
        self.update_level()


if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
