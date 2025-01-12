import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from irobot_create_msgs.action import WallFollow
from builtin_interfaces.msg import Duration
from std_msgs.msg import Bool
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from geometry_msgs.msg import Twist

class WallFollowNavigator(Node):

    def __init__(self):
        super().__init__('wall_follow_navigator')
        self.action_client = ActionClient(self, WallFollow, '/wall_follow')
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.follow_side = 1
        self.wall_following_active = False
        self.exploration_done_sub = self.create_subscription(
            Bool, '/exploration_done', self.exploration_done_callback, 10)
        self.timer = None
        self.retry_count = 0
        self.max_retries = 3
        self.callback_group = ReentrantCallbackGroup()

    def exploration_done_callback(self, msg):
        self.get_logger().info(f"Received /exploration_done message: {msg.data}")
        if msg.data and not self.wall_following_active:
            self.wall_following_active = True
            self.start_wall_following_timer()

    def start_wall_following_timer(self):
        self.get_logger().info("탐색 완료 신호를 받았습니다. 벽 따라가기를 시작합니다.")
        if self.timer is None:
            self.timer = self.create_timer(5.0, self.send_wall_follow_goal, callback_group=self.callback_group)

    def send_wall_follow_goal(self):
        if not self.action_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('WallFollow 액션 서버를 찾을 수 없습니다.')
            return

        self.get_logger().info("Sending wall follow goal...")
        goal_msg = WallFollow.Goal()
        goal_msg.follow_side = self.follow_side
        goal_msg.max_runtime = Duration(sec=60, nanosec=0) # 60초 동안 실행

        self.get_logger().info(f'WallFollow 시작: 방향={"왼쪽" if self.follow_side == 1 else "오른쪽"}')
        self.action_client.send_goal_async(goal_msg, self.goal_response_callback)

    def goal_response_callback(self, future):
        try:
            goal_handle = future.result()
            if not goal_handle.accepted:
                self.get_logger().error('WallFollow 목표가 거부되었습니다.')
                self.handle_failure()
                return

            self.get_logger().info('WallFollow 목표가 수락되었습니다.')
            self._get_result_future = goal_handle.get_result_async()
            self._get_result_future.add_done_callback(self.result_callback)

        except Exception as e:
            self.get_logger().error(f"Goal response callback에서 오류 발생: {str(e)}")
            self.handle_failure()

    def result_callback(self, future):
        try:
            result = future.result().result
            self.get_logger().info('WallFollow 액션 완료.')
            self.retry_count = 0
            self.follow_side = -self.follow_side
            self.send_wall_follow_goal()  # 다음 벽 따라가기 목표 전송
        except Exception as e:
            self.get_logger().error(f"Result callback에서 오류 발생: {str(e)}")
            self.handle_failure()

def main(args=None):
    rclpy.init(args=args)
    node = WallFollowNavigator()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    finally:
        executor.shutdown()
        node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()