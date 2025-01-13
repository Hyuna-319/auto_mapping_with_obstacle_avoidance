# Install Guide



<br>



📌 Auto Mapping & Wall Follow
------
**1. Install packages** 

```
git clone https://github.com/Hyuna-319/auto_mapping_with_obstacle_avoidance.git
sudo apt install ros-humble-irobot-create-description
```
```
mkdir -p ~/turtlebot4_ws/src
cd ~/turtlebot4_ws/src
git clone https://github.com/turtlebot/turtlebot4.git -b humble
```


**2. Set up workspace**
```
cd ~/Downloads/auto_mapping_with_obstacle_avoidance_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
```

```
cd ~/turtlebot4_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
```

**3. Execution**
```
ros2 launch turtlebot4_navigation slam.launch.py
ros2 launch turtlebot4_viz view_robot.launch.py
ros2 launch turtlebot4_navigation nav2.launch.py
```

```
ros2 launch turtlebot4_navigation slam.launch.py params:=$HOME/slam.yaml
ros2 launch turtlebot4_navigation nav2.launch.py params_file:=$HOME/nav2.yaml
```
```
ros2 run turtlebot4_project automap
ros2 run turtlebot4_project follow
```

<br>

📌 Object Tracking
------

```
cd ~/Downloads/object_tracking
python3 orb_detect,py
```

