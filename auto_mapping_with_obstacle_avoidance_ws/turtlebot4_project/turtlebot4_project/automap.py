import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Bool
import math
import time 
import numpy as np
from sklearn.cluster import DBSCAN
from nav_msgs.msg import Odometry
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSHistoryPolicy, QoSReliabilityPolicy

class ImprovedExploration(Node):
    def __init__(self):
        super().__init__('improved_exploration')

        qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,   # 최신 메시지만 수신
            history=QoSHistoryPolicy.KEEP_LAST,       
            depth=10                                 
        )
        self.map_sub = self.create_subscription(OccupancyGrid, '/map', self.map_callback, 10)
        self.goal_pub = self.create_publisher(PoseStamped, '/goal_pose', 10)
        self.unknown_cells = []  # 미탐색 영역의 좌표
        self.current_goal = None  # 현재 설정된 목표 지점
        self.last_goal_time = self.get_clock().now()
        self.goal_interval = 5  # 목표 설정 간격 (초)
        self.exploration_done_pub = self.create_publisher(Bool, '/exploration_done', 10)
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, qos)


        # 로봇 위치 추적  변수
        self.robot_position = None
        self.last_position = None
        self.last_position_update_time = self.get_clock().now()
        self.robot_time = self.get_clock().now()
        self.robot_time = self.get_clock().now()
        
    def map_callback(self, msg):
        
        width = msg.info.width
        height = msg.info.height
        resolution = msg.info.resolution
        origin_x = msg.info.origin.position.x
        origin_y = msg.info.origin.position.y

        self.unknown_cells.clear()
        step = 1  # 탐색 속도를 높이기 위해 스킵 간격 설정

        for y in range(1, height - 1, step):
            for x in range(1, width - 1, step):
                index = x + (y * width)
                if msg.data[index] == -1 and self.is_near_free_space(x, y, width, msg.data):
                    world_x = origin_x + (x * resolution)
                    world_y = origin_y + (y * resolution)
                    self.unknown_cells.append((world_x, world_y))

        if self.unknown_cells and self.is_time_to_set_new_goal():
            self.send_goal(msg)  # 맵 데이터를 전달
        elif not self.unknown_cells:
            self.get_logger().info('미탐색 영역이 없습니다.')
            self.publish_exploration_done()  # 탐색 완료 퍼블리시
    
    def odom_callback(self, msg):
        """
        /odom  로봇의 위치를 갱신
        """
        # /odom 메시지에서 위치 추출
        robot_x = msg.pose.pose.position.x
        robot_y = msg.pose.pose.position.y
        self.get_logger().info(f"현재 로봇 위치: x={robot_x}, y={robot_y}")

        # 로봇 위치 갱신
        self.update_robot_position(robot_x, robot_y)


    def update_robot_position(self, robot_x, robot_y):
        """
        로봇 위치 갱신 및 변화 확인
        """
        self.robot_position = (robot_x, robot_y)
        if self.last_position is None:
            self.last_position = self.robot_position
            self.last_position_update_time = self.get_clock().now()
            return

        # 위치 변화 계산
        distance = math.sqrt((robot_x - self.last_position[0]) ** 2 + (robot_y - self.last_position[1]) ** 2)

        # 0.1m 이상 움직이면 위치 갱신
        if distance >0.1:
            self.last_position = self.robot_position
            self.last_position_update_time = self.get_clock().now()
        else:
            # 마지막 위치 업데이트 이후 15초가 경과했는지 확인
            current_time = self.get_clock().now()
            elapsed_time = (current_time - self.last_position_update_time).nanoseconds / 1e9
            loading_time = (current_time - self.robot_time).nanoseconds /1e9
            if elapsed_time > 15 and loading_time > 120.0:
                self.get_logger().info('15초 이상 위치가 변하지 않았습니다. 미탐지 영역이 없을 수 있습니다.')
                self.publish_exploration_done()  # 탐색 완료 퍼블리시
                time.sleep(5)

    def publish_exploration_done(self):
        done_msg = Bool()
        done_msg.data = True
        self.exploration_done_pub.publish(done_msg)
        self.get_logger().info("탐색 완료 되었습니다.")

    def is_time_to_set_new_goal(self):
        current_time = self.get_clock().now()
        if (current_time - self.last_goal_time).nanoseconds / 1e9 >= self.goal_interval:
            self.last_goal_time = current_time
            return True
        return False
    
    def is_near_free_space(self, x, y, width, data):
        neighbors = [
            (x - 1, y), (x + 1, y),
            (x, y - 1), (x, y + 1),
            (x - 1, y - 1), (x - 1, y + 1),
            (x + 1, y - 1), (x + 1, y + 1)
        ]

        for nx, ny in neighbors:
            index = nx + (ny * width)
            if 0 <= index < len(data) and data[index] == 0:  # 자유 공간 조건
                return True
        return False


    def send_goal(self, msg):
        if self.robot_position is None:
            self.get_logger().info("로봇 위치 정보가 없습니다. 목표 전송을 중단합니다.")
            return

        robot_x, robot_y = self.robot_position
        clusters = self.find_frontier_clusters()
        best_frontier = self.select_best_frontier(clusters, robot_x, robot_y)

        if best_frontier is None:
            self.get_logger().info('적절한 프론티어를 찾을 수 없습니다.')
            return

        target_x, target_y = best_frontier

        goal = PoseStamped()
        goal.header.frame_id = 'map'
        goal.header.stamp = self.get_clock().now().to_msg()

        if not self.is_wall(target_x, target_y, msg.info, msg.data) and self.is_within_limit(robot_x, robot_y, target_x, target_y):
            goal.pose.position.x = target_x
            goal.pose.position.y = target_y
            goal.pose.orientation.w = 1.0
            self.goal_pub.publish(goal)
            self.get_logger().info(f'목표 지점 전송: x={target_x}, y={target_y}')
        else:
            self.get_logger().info('목표 지점이 벽이거나 너무 멀어서 전송하지 않음.')


    def is_wall(self, x, y, map_info, map_data):
        """
        지정된 좌표가 벽인지 확인
        """
        # 월드 좌표를 맵 좌표로 변환
        map_x = int((x - map_info.origin.position.x) / map_info.resolution)
        map_y = int((y - map_info.origin.position.y) / map_info.resolution)

        # 좌표가 맵 범위 내에 있는지 확인
        if map_x < 0 or map_y < 0 or map_x >= map_info.width or map_y >= map_info.height:
            return True  # 맵 범위 밖은 벽으로 간주

        # 1D index 계산
        index = map_x + (map_y * map_info.width)

        # 벽 여부 확인 (OccupancyGrid  100은 벽을 나타냄)
        if 0 <= index < len(map_data) and map_data[index] == 100:
            return True

        return False

    def is_within_limit(self, robot_x, robot_y, target_x, target_y):
        max_distance = 5.0
        distance = math.sqrt((target_x - robot_x) ** 2 + (target_y - robot_y) ** 2)
        return distance <= max_distance

    def find_frontier_clusters(self):
        """
        DBSCAN 클러스터링을 사용해 프론티어를 그룹화
        """
        unknown_array = np.array(self.unknown_cells)
        clustering = DBSCAN(eps=0.05, min_samples=5).fit(unknown_array)

        clusters = {}
        for i, label in enumerate(clustering.labels_):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(self.unknown_cells[i])

        return clusters

    def select_best_frontier(self, clusters, robot_x, robot_y):
        """
        가장 큰 크기이거나 로봇과 가장 가까운 프론티어 선택
        """
        best_frontier = None
        max_size = 0
        min_distance = float('inf')

        for label, points in clusters.items():
            if label == -1:  # 노이즈 클러스터 무시
                continue

            size = len(points)
            center_x = sum(p[0] for p in points) / size
            center_y = sum(p[1] for p in points) / size
            distance = math.sqrt((center_x - robot_x)**2 + (center_y - robot_y)**2)

            if size > max_size or (size == max_size and distance < min_distance):
                max_size = size
                min_distance = distance
                best_frontier = (center_x, center_y)

        return best_frontier


def main(args=None):
    rclpy.init(args=args)
    node = ImprovedExploration()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

