"""
Brain Node — "Bos di kursi belakang" yang memutuskan apa yang robot lakukan.

FSM (Finite State Machine) dengan 5 state:
  IDLE → MAPPING → NAVIGATING → STUCK → ERROR

Transisi:
  IDLE       + goal diterima          → NAVIGATING
  IDLE       + perintah mapping       → MAPPING
  NAVIGATING + goal tercapai          → IDLE
  NAVIGATING + stuck terdeteksi       → STUCK
  NAVIGATING + sensor kritis mati     → ERROR
  MAPPING    + sensor kritis mati     → ERROR
  STUCK      + recovery berhasil      → NAVIGATING (lanjut goal lama)
  STUCK      + recovery gagal 3x     → ERROR
  ERROR      + sensor kembali hidup   → IDLE
  *any*      + perintah stop          → IDLE

Publish:
  /brain/state    — state saat ini (String)
  /brain/status   — detail lengkap (DiagnosticStatus)
  /cmd_vel        — perintah mundur saat recovery (Twist)

Subscribe:
  /scan, /camera/... dll — cek sensor hidup
  /odometry/filtered      — cek robot bergerak
  /navigate_to_pose/_action/status — status Nav2
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from rclpy.time import Time

from std_msgs.msg import String
from sensor_msgs.msg import LaserScan, Image, Imu
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from diagnostic_msgs.msg import DiagnosticStatus, KeyValue
from action_msgs.msg import GoalStatusArray

import math


SENSOR_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=5,
)


class BrainNode(Node):

    # ---- States ----
    IDLE = 'IDLE'
    MAPPING = 'MAPPING'
    NAVIGATING = 'NAVIGATING'
    STUCK = 'STUCK'
    ERROR = 'ERROR'

    def __init__(self):
        super().__init__('brain')

        # --- Parameters dari brain.yaml ---
        self.declare_parameter('critical_sensors', ['/scan'])
        self.declare_parameter('warning_sensors', [])
        self.declare_parameter('sensor_timeout', 3.0)
        self.declare_parameter('stuck_timeout', 15.0)
        self.declare_parameter('stuck_distance_threshold', 0.10)
        self.declare_parameter('max_recovery_attempts', 3)
        self.declare_parameter('recovery_reverse_speed', -0.15)
        self.declare_parameter('recovery_reverse_duration', 2.0)

        self._critical = self.get_parameter('critical_sensors').value
        self._warning = self.get_parameter('warning_sensors').value
        self._sensor_timeout = self.get_parameter('sensor_timeout').value
        self._stuck_timeout = self.get_parameter('stuck_timeout').value
        self._stuck_dist = self.get_parameter('stuck_distance_threshold').value
        self._max_recovery = self.get_parameter('max_recovery_attempts').value
        self._rev_speed = self.get_parameter('recovery_reverse_speed').value
        self._rev_duration = self.get_parameter('recovery_reverse_duration').value

        # --- State ---
        self._state = self.IDLE
        self._prev_state = self.IDLE
        self._recovery_count = 0
        self._last_position = None
        self._last_move_time = self.get_clock().now()
        self._recovery_start = None

        # --- Sensor tracking ---
        self._sensor_last_seen = {}
        self._sensor_map = {
            '/scan': (LaserScan, SENSOR_QOS),
            '/camera/camera/color/image_raw': (Image, SENSOR_QOS),
            '/camera/camera/depth/image_rect_raw': (Image, SENSOR_QOS),
            '/imu/data': (Imu, SENSOR_QOS),
        }

        for topic, (msg_type, qos) in self._sensor_map.items():
            self.create_subscription(
                msg_type, topic,
                lambda msg, t=topic: self._on_sensor(t),
                qos)

        # --- Odometry (untuk stuck detection) ---
        self.create_subscription(
            Odometry, '/odometry/filtered',
            self._on_odom, SENSOR_QOS)

        # --- Nav2 goal status ---
        self.create_subscription(
            GoalStatusArray,
            '/navigate_to_pose/_action/status',
            self._on_nav_status, 10)

        # --- Command input (dari user / higher level) ---
        self.create_subscription(
            String, '/brain/command',
            self._on_command, 10)

        # --- Publishers ---
        self._pub_state = self.create_publisher(String, '/brain/state', 10)
        self._pub_status = self.create_publisher(
            DiagnosticStatus, '/brain/status', 10)
        self._pub_cmd = self.create_publisher(Twist, '/cmd_vel', 10)

        # --- Main loop: 2 Hz ---
        self.create_timer(0.5, self._tick)

        self.get_logger().info(
            f'Brain aktif | Critical: {self._critical} | State: {self._state}')

    # ==== Sensor callbacks ====

    def _on_sensor(self, topic):
        self._sensor_last_seen[topic] = self.get_clock().now()

    def _on_odom(self, msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y

        if self._last_position is not None:
            dx = x - self._last_position[0]
            dy = y - self._last_position[1]
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > self._stuck_dist:
                self._last_move_time = self.get_clock().now()

        self._last_position = (x, y)

    def _on_nav_status(self, msg):
        if not msg.status_list:
            return

        latest = msg.status_list[-1]

        # STATUS_SUCCEEDED = 4
        if latest.status == 4 and self._state == self.NAVIGATING:
            self._transition(self.IDLE, 'Goal tercapai')

        # STATUS_ACCEPTED = 2, STATUS_EXECUTING = 6
        if latest.status in (2, 6) and self._state == self.IDLE:
            self._transition(self.NAVIGATING, 'Goal baru diterima Nav2')

    def _on_command(self, msg):
        cmd = msg.data.strip().lower()

        if cmd == 'stop':
            self._stop_motion()
            self._transition(self.IDLE, 'Perintah STOP dari user')

        elif cmd == 'mapping':
            if self._state == self.IDLE:
                self._transition(self.MAPPING, 'Perintah MAPPING dari user')

    # ==== Main tick ====

    def _tick(self):
        now = self.get_clock().now()

        # 1. Cek sensor kritis
        dead_critical = self._check_dead_sensors(self._critical, now)
        dead_warning = self._check_dead_sensors(self._warning, now)

        if dead_critical and self._state != self.ERROR:
            self._stop_motion()
            self._transition(
                self.ERROR,
                f'Sensor KRITIS mati: {dead_critical}')

        # 2. Recovery dari ERROR kalau sensor kembali
        if self._state == self.ERROR and not dead_critical:
            self._transition(self.IDLE, 'Sensor kritis kembali hidup')

        # 3. Stuck detection (hanya saat NAVIGATING)
        if self._state == self.NAVIGATING:
            elapsed = (now - self._last_move_time).nanoseconds / 1e9
            if elapsed > self._stuck_timeout:
                self._transition(
                    self.STUCK,
                    f'Tidak bergerak {self._stuck_timeout}s')

        # 4. Recovery saat STUCK
        if self._state == self.STUCK:
            self._do_recovery(now)

        # 5. Warning sensors
        if dead_warning and self._state not in (self.ERROR, self.IDLE):
            self.get_logger().warn(f'Sensor WARNING mati: {dead_warning}')

        # 6. Publish state
        self._publish_state(dead_critical, dead_warning)

    # ==== Helpers ====

    def _check_dead_sensors(self, sensor_list, now):
        dead = []
        for topic in sensor_list:
            last = self._sensor_last_seen.get(topic)
            if last is None:
                dead.append(topic)
            else:
                age = (now - last).nanoseconds / 1e9
                if age > self._sensor_timeout:
                    dead.append(topic)
        return dead

    def _transition(self, new_state, reason):
        if new_state == self._state:
            return
        self._prev_state = self._state
        self._state = new_state
        self._recovery_count = 0
        self._recovery_start = None
        self.get_logger().info(
            f'[{self._prev_state}] → [{self._state}] | {reason}')

    def _stop_motion(self):
        stop = Twist()
        self._pub_cmd.publish(stop)

    def _do_recovery(self, now):
        if self._recovery_count >= self._max_recovery:
            self._stop_motion()
            self._transition(
                self.ERROR,
                f'Recovery gagal {self._max_recovery}x — menyerah')
            return

        if self._recovery_start is None:
            self._recovery_start = now
            self._recovery_count += 1
            self.get_logger().info(
                f'Recovery #{self._recovery_count}: mundur {self._rev_duration}s')

        elapsed = (now - self._recovery_start).nanoseconds / 1e9

        if elapsed < self._rev_duration:
            cmd = Twist()
            cmd.linear.x = self._rev_speed
            self._pub_cmd.publish(cmd)
        else:
            self._stop_motion()
            self._last_move_time = now
            self._recovery_start = None
            self._transition(
                self.NAVIGATING,
                f'Recovery #{self._recovery_count} selesai — lanjut navigasi')

    def _publish_state(self, dead_critical, dead_warning):
        # Simple state
        state_msg = String()
        state_msg.data = self._state
        self._pub_state.publish(state_msg)

        # Detailed status
        diag = DiagnosticStatus()
        diag.name = 'AMR Brain'
        diag.hardware_id = 'brain_fsm'

        if self._state == self.ERROR:
            diag.level = DiagnosticStatus.ERROR
        elif self._state == self.STUCK:
            diag.level = DiagnosticStatus.WARN
        else:
            diag.level = DiagnosticStatus.OK

        diag.message = self._state
        diag.values = [
            KeyValue(key='state', value=self._state),
            KeyValue(key='prev_state', value=self._prev_state),
            KeyValue(key='recovery_count', value=str(self._recovery_count)),
            KeyValue(key='dead_critical', value=str(dead_critical)),
            KeyValue(key='dead_warning', value=str(dead_warning)),
        ]
        self._pub_status.publish(diag)


def main(args=None):
    rclpy.init(args=args)
    node = BrainNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
