#!/usr/bin/env python3
import asyncssh
import asyncio
import sys
import random
import time
import os
import signal
from collections import deque


# 主游戏
class OI:
    def __init__(self, conn):
        self.conn = conn
        self.width = 80
        self.height = 24
        self.player_char = "@"
        self.ground_char = "#"
        self.coin_char = "$"
        self.enemy_char = "X"
        self.platform_char = "="
        self.background_char = "."
        self.game_over = False
        self.score = 0
        self.lives = 3
        self.level = 1
        self.player_x = 5
        self.player_y = self.height - 5
        self.player_velocity = 0
        self.gravity = 0.3
        self.jump_power = -4
        self.coins = []
        self.enemies = []
        self.platforms = []
        self.generate_level()
        self.message_queue = deque(maxlen=3)
        self.last_input = ""
        self.conn.write("\033[2J\033[H")  # 清屏

    def generate_level(self):
        # 生成地面
        self.ground_y = self.height - 2
        self.platforms = []

        # 生成平台
        for i in range(3 + self.level):
            x = random.randint(5, self.width - 15)
            y = random.randint(self.height // 2, self.ground_y - 3)
            width = random.randint(5, 15)
            self.platforms.append((x, y, width))

        # 生成金币
        self.coins = []
        for _ in range(5 + self.level * 2):
            if self.platforms:
                plat = random.choice(self.platforms)
                x = random.randint(plat[0] + 1, plat[0] + plat[2] - 2)
                y = plat[1] - 1
                self.coins.append((x, y))

        # 在地面上也放一些金币
        for _ in range(3):
            x = random.randint(5, self.width - 5)
            y = self.ground_y - 1
            self.coins.append((x, y))

        # 生成敌人
        self.enemies = []
        for _ in range(min(self.level, 5)):
            x = random.randint(self.width // 2, self.width - 5)
            y = self.ground_y - 1
            speed = random.choice([-1, 1]) * (0.3 + self.level * 0.1)
            self.enemies.append([x, y, speed])

        # 添加消息
        self.add_message(f"Level {self.level} Start!")

    def add_message(self, msg):
        self.message_queue.append(msg)

    def draw(self):
        # 清屏
        output = "\033[2J\033[H"

        # 绘制UI
        status = f"Level: {self.level}  Score: {self.score}  Lives: {self.lives}"
        output += status + "\n"

        # 绘制游戏区域
        for y in range(1, self.height - 1):
            line = ""
            for x in range(0, self.width):
                char = self.background_char

                # 绘制地面
                if y == self.ground_y:
                    char = self.ground_char

                # 绘制平台
                for plat in self.platforms:
                    px, py, pwidth = plat
                    if y == py and px <= x < px + pwidth:
                        char = self.platform_char

                # 绘制金币
                for coin in self.coins:
                    cx, cy = coin
                    if int(cx) == x and int(cy) == y:
                        char = self.coin_char

                # 绘制敌人
                for enemy in self.enemies:
                    ex, ey, _ = enemy
                    if int(ex) == x and int(ey) == y:
                        char = self.enemy_char

                # 绘制玩家
                if int(self.player_x) == x and int(self.player_y) == y:
                    char = self.player_char

                line += char
            output += line + "\n"

        # 绘制消息
        output += "\n"
        for msg in self.message_queue:
            output += f"> {msg}\n"

        # 绘制控制说明
        controls = "Controls: A/← = left, D/→ = right, SPACE = jump, Q = quit, R = restart"
        output += "\n" + controls + "\n"

        # 绘制游戏结束画面
        if self.game_over:
            msg = "GAME OVER! Press R to restart"
            output += "\n" + msg.center(self.width) + "\n"

        self.conn.write(output)

    def process_input(self, data):
        # 处理输入数据
        if data == '\x1b':  # ESC序列开始
            # 读取接下来的2个字符
            data += self.conn.read(2, timeout=0.01)

        data = data.lower()
        self.last_input = data

        if 'q' in data:
            self.conn.close()
            return False

        if 'r' in data and (self.game_over or 'r' in self.last_input):
            self.reset()
            return True

        if self.game_over:
            return True

        # 左右移动
        if 'd' in data or '\x1b[c' in data:  # 右箭头或 d
            self.player_x = min(self.width - 2, self.player_x + 1)
        elif 'a' in data or '\x1b[d' in data:  # 左箭头或 a
            self.player_x = max(1, self.player_x - 1)

        # 跳跃
        if ' ' in data and self.is_on_ground():
            self.player_velocity = self.jump_power

        return True

    def is_on_ground(self):
        # 检查是否在地面上
        if self.player_y >= self.ground_y - 0.5:
            return True

        # 检查是否在平台上
        for plat in self.platforms:
            x, y, width = plat
            if (int(self.player_y) == y - 1 and
                    x <= self.player_x <= x + width - 1):
                return True

        return False

    def update(self):
        if self.game_over:
            return

        # 应用重力
        self.player_velocity += self.gravity
        self.player_y += self.player_velocity

        # 地面碰撞检测
        if self.player_y >= self.ground_y - 0.5:
            self.player_y = self.ground_y - 0.5
            self.player_velocity = 0

        # 平台碰撞检测
        on_platform = False
        for plat in self.platforms:
            x, y, width = plat
            if (self.player_y >= y - 1.5 and self.player_y <= y - 0.5 and
                    x <= self.player_x <= x + width - 1):
                self.player_y = y - 1.5
                self.player_velocity = 0
                on_platform = True
                break

        # 收集金币
        new_coins = []
        for coin in self.coins:
            coin_x, coin_y = coin
            if (abs(self.player_x - coin_x) < 1 and
                    abs(self.player_y - coin_y) < 1):
                self.score += 10
                self.add_message("+10 points!")
            else:
                new_coins.append(coin)
        self.coins = new_coins

        # 敌人移动和碰撞检测
        for enemy in self.enemies:
            enemy[0] += enemy[2]

            # 敌人边界检测
            if enemy[0] <= 1 or enemy[0] >= self.width - 2:
                enemy[2] *= -1

            # 玩家与敌人碰撞
            if (abs(self.player_x - enemy[0]) < 1 and
                    abs(self.player_y - enemy[1]) < 1):
                self.lives -= 1
                self.add_message("Ouch! Lost a life!")
                self.player_x = 5
                self.player_y = self.height - 5
                self.player_velocity = 0
                if self.lives <= 0:
                    self.game_over = True
                    self.add_message("Game Over!")
                break

        # 检查是否进入下一关
        if not self.coins:
            self.level += 1
            self.add_message(f"Level {self.level}!")
            self.generate_level()
            self.player_x = 5
            self.player_y = self.height - 5
            self.player_velocity = 0

    async def run(self):
        self.draw()

        while not self.conn._closing:
            # 处理输入
            try:
                data = await asyncio.wait_for(self.conn.read(1), timeout=0.05)
                if not self.process_input(data):
                    break
            except asyncio.TimeoutError:
                pass
            except (asyncssh.ConnectionLost, asyncssh.TerminalSizeChanged, ConnectionResetError):
                break
            except Exception as e:
                print(f"Input error: {e}")
                break

            # 更新游戏状态
            self.update()

            # 重绘游戏
            self.draw()

            # 控制游戏速度
            await asyncio.sleep(0.05)

    def reset(self):
        """重启游戏，但保留 conn 等不变"""
        self.__init__(self.conn)


# SSH 服务器处理类
class SSHGameServer(asyncssh.SSHServer, asyncssh.SSHServerSession):
    def __init__(self):
        super().__init__()
        self.username = None
        self._chan = None

    # ---------- 以下 4 个方法是 SSHServer 协议 ----------
    def connection_made(self, conn):
        self.conn = conn
        try:
            peer = conn.get_extra_info('peername')
            print(f"New connection from {peer[0]}")
        except Exception as e:
            print(f"Connection made error: {e}")

    def connection_lost(self, exc):
        print("Client disconnected" if exc is None else f"Connection lost: {exc}")

    def begin_auth(self, username):
        self.username = username
        return True

    def password_auth_supported(self):
        return True

    def validate_password(self, username, password):
        if password == "ciallo":
            print(f"User {username} authenticated successfully")
            return True
        print(f"Failed authentication attempt for {username}")
        return False

    def session_requested(self):
        # 关键：返回自己（SSHServerSession 实例），而不是 bool
        return self

    # ---------- 以下 3 个方法是 SSHServerSession 协议 ----------
    def session_started(self):
        # 会话真正开始时启动游戏
        pass

    async def _run_game(self):
        try:
            game = OI(self._chan)
            await game.run()
        except Exception as e:
            print(f"Game session error: {e}")
        finally:
            if self._chan is not None:
                try:
                    self._chan.exit(0)
                except asyncssh.ConnectionLost:
                    pass

    # 让 SSHServerSession 的 process 回调指向我们
    def shell_requested(self):
        return True

    def exec_requested(self, command):
        return False     # 不允许执行命令，只提供交互式 shell

    def pty_requested(self, term_type, term_size, term_modes):
        return True      # 允许分配伪终端

    def subsystem_requested(self, subsystem):
        return False

    # asyncssh 在会话建立后会调用此函数，把 channel 传进来
    def connection_made_chan(self, chan):
        self._chan = chan
        asyncio.create_task(self._run_game())


# 生成SSH主机密钥
def generate_ssh_key():
    key_path = 'ssh_host_key'
    if not os.path.exists(key_path):
        print("Generating SSH host key...")
        # 生成RSA密钥（2048位）
        key = asyncssh.generate_private_key('ssh-rsa', key_size=2048)
        key.write_private_key(key_path)
        print(f"SSH host key generated and saved to {key_path}")
    else:
        print(f"Using existing SSH host key at {key_path}")


# 主服务器函数
async def run_server():
    host = '0.0.0.0'
    port = 2222

    print(f"Starting SSH game server on {host}:{port}")
    print("Connect with: ssh -p 2222 player@localhost")
    print("Password: ciallo")  # 使用您设置的密码

    try:
        await asyncssh.create_server(
            lambda: SSHGameServer(),
            host,
            port,
            server_host_keys=['ssh_host_key'],
            process_factory=None
        )
    except Exception as e:
        print(f"Server creation error: {e}")
        raise


# 主函数
def main():
    # 生成SSH主机密钥（如果不存在）
    generate_ssh_key()

    # 设置信号处理
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 创建服务器任务
    server_task = None

    async def start_server():
        nonlocal server_task
        server_task = asyncio.create_task(run_server())
        await asyncio.sleep(0)  # 确保任务被调度

    # 启动服务器
    try:
        print("Starting server...")
        loop.run_until_complete(start_server())
        print("Server started. Press Ctrl+C to stop.")
        loop.run_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        # 关闭服务器
        if server_task and not server_task.done():
            server_task.cancel()

        # 取消所有任务
        tasks = asyncio.all_tasks(loop)
        for task in tasks:
            task.cancel()

        # 等待所有任务完成
        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        loop.close()
        print("Server stopped.")


if __name__ == "__main__":
    main()