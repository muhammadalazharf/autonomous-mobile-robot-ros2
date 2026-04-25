#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/joy.hpp"
#include <fcntl.h>
#include <termios.h>
#include <unistd.h>
#include <cstring>
#include <cstdio>
#include <string>

// ===== KONFIGURASI =====
#define SERIAL_PORT  "/dev/ttyACM1"
#define BAUD_RATE    B115200
#define MAX_PWM      4000
#define MAX_STEER    45
#define DEADMAN_BTN  5
#define AXIS_VEL     1
#define AXIS_STEER   3
// =======================

class STM32Bridge : public rclcpp::Node
{
public:
  STM32Bridge() : Node("stm32_bridge"), serial_fd_(-1)
  {
    serial_fd_ = open(SERIAL_PORT, O_RDWR | O_NOCTTY | O_SYNC);
    if (serial_fd_ < 0) {
      RCLCPP_ERROR(this->get_logger(),
        "[ERROR] Gagal buka port %s. Colok kabel STM32!", SERIAL_PORT);
    } else {
      configure_serial(serial_fd_);
      RCLCPP_INFO(this->get_logger(),
        "[OK] STM32 terhubung di %s", SERIAL_PORT);
    }
    subscription_ = this->create_subscription<sensor_msgs::msg::Joy>(
      "/joy", 10,
      std::bind(&STM32Bridge::joy_callback, this, std::placeholders::_1));
    RCLCPP_INFO(this->get_logger(),
      "[OK] Siap! Tahan R1 + gerak analog untuk menjalankan robot.");
  }

  ~STM32Bridge()
  {
    if (serial_fd_ >= 0) {
      send_command(0, 0);
      close(serial_fd_);
      RCLCPP_INFO(this->get_logger(), "[OK] Motor stopped. Serial closed.");
    }
  }

private:
  rclcpp::Subscription<sensor_msgs::msg::Joy>::SharedPtr subscription_;
  int serial_fd_;

  void joy_callback(const sensor_msgs::msg::Joy::SharedPtr msg)
  {
    if (serial_fd_ < 0) {
      RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 3000,
        "[WARN] Serial belum terbuka! Colok kabel STM32.");
      return;
    }
    bool deadman = (msg->buttons.size() > DEADMAN_BTN &&
                    msg->buttons[DEADMAN_BTN] == 1);
    if (!deadman) {
      send_command(0, 0);
      return;
    }
    float vel_raw   = (msg->axes.size() > AXIS_VEL)
                      ? msg->axes[AXIS_VEL] : 0.0f;
    float steer_raw = (msg->axes.size() > AXIS_STEER)
                      ? msg->axes[AXIS_STEER] : 0.0f;

    // Negate: analog up (+1.0) = forward
    int velocity = static_cast<int>(vel_raw   * -MAX_PWM);
    int steering = static_cast<int>(steer_raw * -MAX_STEER);

    velocity = std::max(-MAX_PWM,  std::min(MAX_PWM,  velocity));
    steering = std::max(-MAX_STEER, std::min(MAX_STEER, steering));

    send_command(velocity, steering);
  }

  void send_command(int velocity, int steering)
  {
    char buffer[64];
    snprintf(buffer, sizeof(buffer), "V:%d,S:%d\n", velocity, steering);
    ssize_t n = write(serial_fd_, buffer, strlen(buffer));
    if (n < 0) {
      RCLCPP_ERROR(this->get_logger(), "[ERROR] Gagal kirim serial!");
    } else {
      RCLCPP_INFO(this->get_logger(), "[TX] %s", buffer);
    }
  }

  void configure_serial(int fd)
  {
    struct termios tty;
    memset(&tty, 0, sizeof(tty));
    tcgetattr(fd, &tty);
    cfsetospeed(&tty, BAUD_RATE);
    cfsetispeed(&tty, BAUD_RATE);
    tty.c_cflag  = (tty.c_cflag & ~CSIZE) | CS8;
    tty.c_cflag |= (CLOCAL | CREAD);
    tty.c_cflag &= ~(PARENB | PARODD | CSTOPB | CRTSCTS);
    tty.c_iflag &= ~IGNBRK;
    tty.c_lflag  = 0;
    tty.c_oflag  = 0;
    tty.c_cc[VMIN]  = 0;
    tty.c_cc[VTIME] = 5;
    tcsetattr(fd, TCSANOW, &tty);
  }
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<STM32Bridge>());
  rclcpp::shutdown();
  return 0;
}