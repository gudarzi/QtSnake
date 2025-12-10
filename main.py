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


# --- Utility Functions ---


# Function to get the resource path for loading UI files
def get_resource_path(path):
   try:
       base_path = sys._MEIPASS
   except Exception:
       base_path = os.path.abspath(".")
   return os.path.join(base_path, path)


# Function to prevent game breaking mechanics, managing movement and boundary/collision checks
def move_items_while_respecting_border(item, scene, snake_cubes, obstacles, move_obstacles=True):
   # Foods and obstacles can move (food moves in level 3, obstacle moves in level 4)


   if isinstance(item, Obstacle) and not move_obstacles:
       return


   # Initialize velocity if not set
   if getattr(item, 'vx', 0) == 0 and getattr(item, 'vy', 0) == 0:
       speed = getattr(item, 'speed', 2)
       if random.random() < 0.5:
           item.vx = random.choice([-1, 1]) * speed
           item.vy = 0
       else:
           item.vx = 0
           item.vy = random.choice([-1, 1]) * speed


       # Start timer to change direction every 2 seconds, for randomness in movement
       if not getattr(item, '_direction_timer_set', False):
           item._direction_timer_set = True
           def change_direction():
               if hasattr(item, 'vx') and hasattr(item, 'vy'):
                   if random.random() < 0.5:
                       item.vx = random.choice([-1, 1]) * speed
                       item.vy = 0
                   else:
                       item.vx = 0
                       item.vy = random.choice([-1, 1]) * speed
              
               QtCore.QTimer.singleShot(2000, change_direction)
           QtCore.QTimer.singleShot(2000, change_direction)


   # Set new position
   new_x = item.x() + item.vx
   new_y = item.y() + item.vy


   rect = item.sceneBoundingRect()
   scene_rect = scene.sceneRect()


   # Respect screen bounds left/right
   if new_x < scene_rect.left():
       new_x = scene_rect.left()
       item.vx = -item.vx
   elif new_x + rect.width() > scene_rect.right():
       new_x = scene_rect.right() - rect.width()
       item.vx = -item.vx


   # Respect screen bounds top/bottom
   if new_y < scene_rect.top():
       new_y = scene_rect.top()
       item.vy = -item.vy
   elif new_y + rect.height() > scene_rect.bottom():
       new_y = scene_rect.bottom() - rect.height()
       item.vy = -item.vy


   # Check for collision with snake cubes and reverse direction
   for cube in snake_cubes:
       if item.collidesWithItem(cube):
           item.vx = -item.vx
           item.vy = -item.vy
           new_x = max(scene_rect.left(), min(new_x, scene_rect.right() - rect.width()))
           new_y = max(scene_rect.top(), min(new_y, scene_rect.bottom() - rect.height()))
           break


   # Move to new position
   item.setX(new_x)
   item.setY(new_y)




# --- Game Element Classes ---


# Class representing Food item for the snake to consume
class Food(QGraphicsRectItem):
   def __init__(self, food_type="normal"):
       self.width = 15
       self.height = 15
       super().__init__(0, 0, self.width, self.height)
       self.food_type = food_type
       # Velocity for moving food
       self.vx = 0
       self.vy = 0


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
       # Shield food type logic
       elif food_type == "shield":
           self.setBrush(QBrush(QColor("magenta")))
           self.points = 0
       else:  # normal
           self.setBrush(QBrush(QColor("orange")))
           self.points = 1
          
  
   # Moves the food item while respecting the border and checking for collisions
   def move_food(self, scene, snake_cubes, obstacles):
       move_items_while_respecting_border(self, scene, snake_cubes, self, obstacles)




# Class representing individual SnakeCube (each segment of the snake)
class SnakeCube(QGraphicsRectItem):
   def __init__(self):
       self.width = 15
       self.height = 15
       super().__init__(0, 0, self.width, self.height)
       self.setBrush(QBrush(QColor("green")))




# Class representing Obstacle
class Obstacle(QGraphicsRectItem):
   def __init__(self, x, y, width=30, height=30, obstacle_type="moving", speed=1):
       super().__init__(x, y, width, height)
       self.obstacle_type = obstacle_type
       # Speed and velocity for moving obstacles
       self.speed = speed
       self.vx = 0
       self.vy = 0


       if obstacle_type == "wall":
           self.setBrush(QBrush(QColor("gray")))
       else:
           self.setBrush(QBrush(QColor("red")))
       self.setPen(QtCore.Qt.NoPen)
      
  
   # Moves the obstacle item while respecting the border and checking for collisions
   def move_obstacle(self, scene, snake_cubes, food, obstacles):
       move_items_while_respecting_border(self, scene, snake_cubes, food, obstacles)




# Class representing the Snake and its behavior
class Snake(QtWidgets.QGraphicsScene):
   def __init__(self):
       super().__init__()
       self.score = 0
       self.direction = (1, 0)  # Start moving right
       self.cube_list = [SnakeCube() for i in range(2)]  # Snake is initially 2 cubes large
       self.color = "green"  # Default color
       self.apply_color()
       self.move()


   # Moves the snake by shifting the head forward and placing the tail behind it
   def move(self):
       head = self.cube_list[0]
       tail = self.cube_list[-1]
       tail.setX(head.x() + self.direction[0] * head.width)
       tail.setY(head.y() + self.direction[1] * head.height)
       self.cube_list.insert(0, self.cube_list.pop())


   # Adds a new cube to the end of the snake
   def grow(self):
       new_cube = SnakeCube()
       self.cube_list.append(new_cube)
       self.apply_color()
       self.move()


   # Updates the snake's direction, preventing immediate 180-degree turns
   def change_direction(self, direction):
       dx, dy = direction
       if (dx, dy) != (-self.direction[0], -self.direction[1]):
           self.direction = (dx, dy)


   # Sets the snake's primary color
   def set_color(self, color):
       self.color = color
       self.apply_color()


   # Applies the current primary color to all snake segments
   def apply_color(self):
       for cube in self.cube_list:
           cube.setBrush(QBrush(QColor(self.color)))




# --- Main Window Class ---


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
       # --- End of HUD Labels ---


       # Initialize game timer and set speed
       self.timer = QtCore.QTimer()
       self.timer.timeout.connect(self.tick)
       self.base_speed = 150
       self.timer.start(self.base_speed)


       # Set the scene's key press handler
       self.scene.keyPressEvent = self.scene_key_press


       # Initialize game state variables
       self.obstacles = []
       self.food_count = 0
       self.level = 1
       self.points_to_next_level = 5
       self.high_score = self.load_high_score()
       self.speed_boost_active = False
       self.snake = Snake()
      
       # Shield and Invincibility Variables
       self.shields = 0
       self.shield_food = None
       self.invincible = False
       self.invincible_timer = None
      
       self.create_food()


       # Menu state variables
       self.in_menu = True
       self.menu_selection = 0
      
       # Initialize menu elements to None before show_start_menu creates them
       self.start_button = None
       self.quit_button = None
       self.high_score_menu = None
       self.dummy_text = None


      
       self.show_start_menu()
      


       self.window.show()


   # --- Game Logic Methods ---


   # Updates the score display on the UI
   def update_score(self):
       self.scoreLabel.setText(f"Score: {self.snake.score}")


   # Updates the level display on the UI
   def update_level(self):
       self.levelLabel.setText(f"Level: {self.level}")


   # Loads the high score from a JSON file
   def load_high_score(self):
       high_score_file = "snake_highscore.json"
       try:
           if os.path.exists(high_score_file):
               with open(high_score_file, 'r') as f:
                   data = json.load(f)
                   return data.get('high_score', 0)
       except Exception as e:
           print(f"Error loading high score: {e}")
       return 0


   # Saves the current high score to a JSON file
   def save_high_score(self):
       high_score_file = "snake_highscore.json"
       try:
           with open(high_score_file, 'w') as f:
               json.dump({'high_score': self.high_score}, f)
       except Exception as e:
           print(f"Error saving high score: {e}")


   # Handles keyboard input for movement, menu navigation, and pausing
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


   # The main game loop function, executed by the QTimer
   def tick(self):
       if not self.in_menu:
          
           # Move food if the level is high enough
           if self.level >= 3 and self.food:
               self.food.move_food(self.scene, self.snake.cube_list, self.obstacles)
          
           # Move shield food if it exists and the level is high enough
           if self.shield_food and self.level >= 3:
               self.shield_food.move_food(self.scene, self.snake.cube_list, self.obstacles)




           # Move obstacles if the level is high enough (Level >= 4)
           for obs in self.obstacles:
               move_items_while_respecting_border(obs, self.scene, self.snake.cube_list, self.obstacles,
                                   move_obstacles=(self.level >= 4))
          
           # Move snake
           self.snake.move()


           # Re-render elements
           self.render_elements()


           # Check collisions
           self.check_collision()


   # Adds or ensures all game elements are present in the QGraphicsScene
   def render_elements(self):
       if self.food and self.food.scene() != self.scene:
           self.scene.addItem(self.food)
          
      
       if self.shield_food and self.shield_food.scene() != self.scene:
           self.scene.addItem(self.shield_food)


       for sc in self.snake.cube_list:
           if sc.scene() != self.scene:
               self.scene.addItem(sc)


       for obstacle in self.obstacles:
           if obstacle.scene() != self.scene:
               self.scene.addItem(obstacle)


   # Attempts to place a new Food item randomly on the scene
   def create_food(self):
       max_attempts = 20
       for attempt in range(max_attempts):
           x = self.scene.width() * (0.1 + 0.8 * (random.random()) - 0.5)
           y = self.scene.height() * (0.1 + 0.8 * (random.random()) - 0.5)


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


           collision_with_obstacles = any(temp_food.collidesWithItem(obstacle) for obstacle in self.obstacles)
           collision_with_snake = any(temp_food.collidesWithItem(cube) for cube in self.snake.cube_list)
          
          
           collision_with_shield = False
           if self.shield_food:
               collision_with_shield = temp_food.collidesWithItem(self.shield_food)


           # Check if the potential food position is safe from all other elements
           if not collision_with_obstacles and not collision_with_snake and not collision_with_shield:
               self.food = temp_food
               self.scene.addItem(self.food)
               return


       # Fallback: If no safe spot is found after max attempts, spawn normal food
       self.food = Food("normal")
       x = self.scene.width() * (0.1 + 0.8 * (random.random()) - 0.5)
       y = self.scene.height() * (0.1 + 0.8 * (random.random()) - 0.5)
       self.food.setX(x)
       self.food.setY(y)
       self.scene.addItem(self.food)


  
   # Attempts to place a Shield Food item randomly on the scene
   def spawn_shield_food(self):
       # Only spawn if no shield food exists
       if self.shield_food is not None:
           return


       max_attempts = 20
       for attempt in range(max_attempts):
           x = self.scene.width() * (0.1 + 0.8 * random.random() - 0.5)
           y = self.scene.height() * (0.1 + 0.8 * random.random() - 0.5)


           temp_food = Food("shield")
           temp_food.setX(x)
           temp_food.setY(y)


           # Check collision with snake, existing food, and obstacles
           collision = any(temp_food.collidesWithItem(item) for item in self.snake.cube_list + self.obstacles + [self.food])


           if not collision:
               self.shield_food = temp_food
               self.scene.addItem(self.shield_food)
               break


   # Attempts to place a new Obstacle item randomly on the scene
   def create_obstacle(self):
       max_attempts = 10
       for attempt in range(max_attempts):
           x = self.scene.width() * (0.1 + 0.8 * (random.random()) - 0.5)
           y = self.scene.height() * (0.1 + 0.8 * (random.random()) - 0.5)
          
           temp_obstacle = Obstacle(x, y)
          
           collision_with_snake = any(temp_obstacle.collidesWithItem(cube) for cube in self.snake.cube_list)
           collision_with_food = temp_obstacle.collidesWithItem(self.food)
          
           # Check collision with shield food (if it exists)
           collision_with_shield = False
           if self.shield_food:
                collision_with_shield = temp_obstacle.collidesWithItem(self.shield_food)


           collision_with_obstacles = any(temp_obstacle.collidesWithItem(existing_obstacle) for existing_obstacle in self.obstacles)


           # Check if the potential obstacle position is safe
           if not collision_with_snake and not collision_with_food and not collision_with_obstacles and not collision_with_shield:
               obstacle = Obstacle(x, y)
               self.obstacles.append(obstacle)
               self.scene.addItem(obstacle)
               return


       print(f"Warning: Could not find valid position for obstacle after {max_attempts} attempts")


  
   # Initiates a temporary period of invincibility
   def start_invincibility(self, duration=2000):
       self.invincible = True
       self.snake.set_color("gold")
       if self.invincible_timer and self.invincible_timer.isActive():
           self.invincible_timer.stop()
       self.invincible_timer = QtCore.QTimer.singleShot(duration, self.end_invincibility)


   # Ends the temporary invincibility period and reverts snake color
   def end_invincibility(self):
       self.invincible = False
       if self.shields == 0:
           self.snake.set_color("green")
       else:
           self.snake.set_color("magenta")


   # Checks for all possible game collisions (food, self, boundary, obstacle, shield food)
   def check_collision(self):
       head = self.snake.cube_list[0]


       # 1. Boundary/Self-Collision Check
       is_dangerous_collision = \
           not self.scene.sceneRect().contains(head.sceneBoundingRect()) or \
           any((head.x(), head.y()) == (cube.x(), cube.y()) for cube in self.snake.cube_list[1:])


       if is_dangerous_collision:
           self.handle_dangerous_collision()
           return


       # 2. Food Collision
       if head.collidesWithItem(self.food):
           food_type = self.food.food_type
           self.snake.score += self.food.points
           self.food_count += 1
          
           if food_type == "golden":
               self.show_powerup_message("⭐ Golden Food! +3 Points! ⭐", "gold")
           elif food_type == "speed_boost":
               current_speed = self.timer.interval()
               new_speed = max(30, current_speed - 50)
               self.timer.setInterval(new_speed)
               self.speed_boost_active = True
               self.show_powerup_message("⚡ Speed Boost! Going Fast! ⚡", "cyan")
               QtCore.QTimer.singleShot(5000, self.reset_speed)
           elif food_type == "slow_down":
               current_speed = self.timer.interval()
               new_speed = min(200, current_speed + 50)
               self.timer.setInterval(new_speed)
               self.speed_boost_active = True
               self.show_powerup_message("🐌 Slow Motion! Take it Easy! 🐌", "purple")
               QtCore.QTimer.singleShot(5000, self.reset_speed)
          
           self.update_score()
           self.scene.removeItem(self.food)
           self.create_food()
           self.snake.grow()


           # Check for level up condition
           if self.food_count >= self.level * self.points_to_next_level:
               self.level_up()


           # Spawn a random obstacle periodically
           if self.food_count % 5 == 0:
               self.create_obstacle()
      
       # 3. Obstacle Collision
       for obstacle in self.obstacles:
           if head.collidesWithItem(obstacle):
               self.handle_dangerous_collision()
               return


      
       # 4. Shield Food Collision
       if self.shield_food and head.collidesWithItem(self.shield_food):
           self.shields += 1
           self.snake.set_color("magenta")
           self.show_powerup_message(f"You collected a shield! Total: {self.shields}", "magenta")
           self.scene.removeItem(self.shield_food)
           self.shield_food = None


   # Displays a temporary message on the UI for power-ups
   def show_powerup_message(self, message, color):
       self.powerUpLabel.setText(message)
       self.powerUpLabel.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
       self.powerUpLabel.show()
       QtCore.QTimer.singleShot(3000, self.powerUpLabel.hide)


   # Resets the game speed to the current level's base speed after a power-up expires
   def reset_speed(self):
       if not self.speed_boost_active:
           return
       new_speed = max(70, self.base_speed - (self.level - 1) * 10)
       self.timer.setInterval(new_speed)
       self.speed_boost_active = False
       self.show_powerup_message("⏱️ Normal Speed Restored", "white")


   # Creates pattern-based, non-moving wall obstacles for various levels
   def create_level_obstacles(self):
       if self.level == 1:
           self.clear_all_obstacles()
           self.create_wall_obstacle(-300, -100, 150, 20)
      
       if self.level == 2:
           self.create_wall_obstacle(150, 80, 150, 20)
      
       if self.level == 4:
           self.create_wall_obstacle(-200, -150, 20, 100)
      
       if self.level == 6:
           self.create_wall_obstacle(200, 0, 20, 100)
      
       if self.level == 8:
           self.create_wall_obstacle(-350, -180, 80, 20)
           self.create_wall_obstacle(-350, -180, 20, 80)
          
       if self.level == 10:
           self.clear_all_obstacles()
           self.create_wall_obstacle(-150, -100, 50, 20)
           self.create_wall_obstacle(-150, -100, 20, 50)
           self.create_wall_obstacle(100, -100, 50, 20)
           self.create_wall_obstacle(130, -100, 20, 50)
           self.create_wall_obstacle(-150, 50, 50, 20)
           self.create_wall_obstacle(-150, 70, 20, 50)
           self.create_wall_obstacle(100, 50, 50, 20)
           self.create_wall_obstacle(130, 70, 20, 50)
          
       if self.level == 12:
           self.clear_all_obstacles()
           self.create_wall_obstacle(0, -200, 20, 150)
           self.create_wall_obstacle(0, 50, 20, 150)
          
       if self.level == 14:
           self.clear_all_obstacles()
           self.create_wall_obstacle(-300, -100, 200, 20)
           self.create_wall_obstacle(100, -50, 200, 20)
           self.create_wall_obstacle(-300, 0, 200, 20)
           self.create_wall_obstacle(100, 50, 200, 20)
          
   # Removes all obstacles from the scene and clears the list
   def clear_all_obstacles(self):
       for obstacle in self.obstacles:
           if obstacle.scene() == self.scene:
               self.scene.removeItem(obstacle)
       self.obstacles.clear()


   # Helper function to create a static wall obstacle
   def create_wall_obstacle(self, x, y, width, height):
       wall = Obstacle(x, y, width, height, "wall")
       self.obstacles.append(wall)
       self.scene.addItem(wall)


   # Increments the level, increases game speed, and creates new obstacles
   def level_up(self):
       self.level += 1
       self.update_level()


       new_speed = max(70, self.base_speed - (self.level - 1) * 10)
       self.timer.setInterval(new_speed)


       if self.level % 2 == 0 and self.level < 8:
           self.create_obstacle()


       self.create_level_obstacles()


       self.show_powerup_message(f"🎉 LEVEL {self.level}! 🎉", "yellow")


   # Pauses the game and displays a dialog box
   def game_pause(self):
       self.timer.stop()
       msg1 = QMessageBox()
       msg1.setWindowTitle("Game Paused")
       msg1.setText(f"Level: {self.level}\nYour score: {self.snake.score}\n Do you want to continue?")
       msg1.setIcon(QMessageBox.Information)
       continue_button = msg1.addButton("Continue", QMessageBox.ActionRole)
       abort_button = msg1.addButton("Quit", QMessageBox.RejectRole)
       msg1.exec()
       if msg1.clickedButton() == continue_button:
           current_speed = max(70, self.base_speed - (self.level - 1) * 10)
           self.timer.start(current_speed)
       elif msg1.clickedButton() == abort_button:
           self.game_over()


   # Handles the response to hitting a wall, self, or an obstacle
   def handle_dangerous_collision(self):
       """
       Handles the response to hitting a wall, self, or an obstacle.
       Uses a shield if available (and not invincible), otherwise triggers Game Over.
       """
       if self.invincible:
           return True # Collision ignored, snake is invincible


       if self.shields > 0:
           # Shield Consumption Logic
           self.shields -= 1
          
           # Determine new snake color: magenta if shields remain, green if shields hit 0
           new_color = "green" if self.shields == 0 else "magenta"
           self.snake.set_color(new_color)
          
           self.show_powerup_message(f"🛡️ Shield used! Remaining: {self.shields}", "magenta")
          
           self.start_invincibility(3000)
           return True # Shield was consumed
       else:
           # No shield, not invincible -> Game Over
           self.game_over()
           return False # Game Over triggered
  
   # Resets the game state and displays the Game Over message
   def game_over(self):
       self.timer.stop()
      
       # Stop power-up timers
       if hasattr(self, 'shield_timer') and self.shield_timer.isActive():
           self.shield_timer.stop()
       if self.invincible_timer and self.invincible_timer.isActive():
           self.invincible_timer.stop()


       # Check and save high score
       if self.snake.score > self.high_score:
           self.high_score = self.snake.score
           self.save_high_score()
           high_score_text = "\n🎉 NEW HIGH SCORE! 🎉"
       else:
           high_score_text = f"\nHigh Score: {self.high_score}"


       msg = QMessageBox()
       msg.setWindowTitle("Game Over")
       msg.setText(f"Level Reached: {self.level}\nYour Score: {self.snake.score}{high_score_text}")
       msg.setIcon(QMessageBox.Information)
       msg.exec()


       # Reset all game elements and state
       self.snake = Snake()
       self.obstacles.clear()
       self.scene.clear()
       self.food = None
       self.level = 1
       self.shields = 0
       self.shield_food = None
       self.invincible = False


       # Return to start menu
       self.in_menu = True
       self.menu_selection = 0
       self.show_start_menu()
       self.update_score()
       self.update_level()


   # Displays the main menu interface
   def show_start_menu(self):
       self.in_menu = True
       self.scene.clear()


       # Robust cleanup of old menu elements
       if self.start_button:
           try:
               self.start_button.deleteLater()
               self.quit_button.deleteLater()
               self.dummy_text.deleteLater()
               self.high_score_menu.deleteLater()
           except RuntimeError:
               pass
          
           self.start_button = None
           self.quit_button = None
           self.dummy_text = None
           self.high_score_menu = None
          
       # 1. High Score Label
       self.high_score_menu = QtWidgets.QLabel(f"High Score: {self.high_score}", self.window)
       self.high_score_menu.setAlignment(QtCore.Qt.AlignCenter)
       self.high_score_menu.setStyleSheet("color: gold; font-size: 24px; font-weight: bold;")
       self.high_score_menu.setGeometry(250, 50, 300, 50)
       self.high_score_menu.show()


       # 2. START Button
       self.start_button = QtWidgets.QLabel("START", self.window)
       self.start_button.setAlignment(QtCore.Qt.AlignCenter)
       self.start_button.setStyleSheet("color: white; font-size: 30px;")
       self.start_button.setGeometry(350, 150, 100, 50)
       self.start_button.show()
       self.start_button.mousePressEvent = self.start_button_clicked


       # 3. QUIT Button
       self.quit_button = QtWidgets.QLabel("QUIT", self.window)
       self.quit_button.setAlignment(QtCore.Qt.AlignCenter)
       self.quit_button.setStyleSheet("color: white; font-size: 30px;")
       self.quit_button.setGeometry(350, 250, 100, 50)
       self.quit_button.show()
       self.quit_button.mousePressEvent = self.quit_button_clicked


       # 4. Instructions Label
       self.dummy_text = QtWidgets.QLabel("Use Keyboard Keys or Mouse To Navigate!", self.window)
       self.dummy_text.setAlignment(QtCore.Qt.AlignCenter)
       self.dummy_text.setStyleSheet("color: green; font-size: 14px;")
       self.dummy_text.setGeometry(250, 350, 300, 50)
       self.dummy_text.show()


       self.update_menu_selection()
       self.window.update()


   # Highlights the currently selected menu option
   def update_menu_selection(self):
       if self.menu_selection == 0:
           self.start_button.setStyleSheet("color: yellow; font-size: 30px;")
           self.quit_button.setStyleSheet("color: white; font-size: 30px;")
       else:
           self.start_button.setStyleSheet("color: white; font-size: 30px;")
           self.quit_button.setStyleSheet("color: yellow; font-size: 30px;")


   # Mouse handler for the START button
   def start_button_clicked(self, event):
       self.start_game()


   # Mouse handler for the QUIT button
   def quit_button_clicked(self, event):
       QApplication.quit()


   # Initializes and starts a new game session
   def start_game(self):
       # Delete menu elements before starting the game
       if self.start_button:
           try:
               self.start_button.deleteLater()
               self.quit_button.deleteLater()
               self.dummy_text.deleteLater()
               self.high_score_menu.deleteLater()
           except RuntimeError:
               pass
              
           self.start_button = None
           self.quit_button = None
           self.dummy_text = None
           self.high_score_menu = None
          
       self.in_menu = False
       self.snake = Snake()
       self.level = 1
       self.shields = 0
       self.create_food()
       self.obstacles.clear()
       self.food_count = 0
       self.timer.start(self.base_speed)
       self.update_score()
       self.update_level()
      
       # Start timer for spawning shield food
       self.shield_timer = QtCore.QTimer()
       self.shield_timer.timeout.connect(self.spawn_shield_food)
       self.shield_timer.start(10000)


if __name__ == "__main__":
   QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
   app = QApplication(sys.argv)
   window = MainWindow()
   sys.exit(app.exec())



