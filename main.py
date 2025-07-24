#!/usr/bin/env python3
import asyncssh
import asyncio
import sys
import random
import time
import signal
from collections import deque


# ASCII RPG 游戏类
class ASCIIRPG:
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
        controls = "Controls: ← → to move, SPACE to jump, Q to quit, R to restart"
        output += "\n" + controls + "\n"

        # 绘制游戏结束画面
        if self.game_over:
            msg = "GAME OVER! Press R to restart"
            output += "\n" + msg.center(self.width) + "\n"

        self.conn.write(output)

    def process_input(self, data):
        data = data.lower()
        self.last_input = data

        if 'q' in data:
            self.conn.close()
            return False

        if 'r' in data and (self.game_over or 'r' in self.last_input):
            self.__init__(self.conn)
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

            # 更新游戏状态
            self.update()

            # 重绘游戏
            self.draw()

            # 控制游戏速度
            await asyncio.sleep(0.05)


# SSH 这一块
class SSHGameServer(asyncssh.SSHServer):
    def __init__(self):
        self.username = None

    def connection_made(self, conn):
        self.conn = conn
        print(f"New connection from {conn.get_extra_info('peername')[0]}")

    def connection_lost(self, exc):
        if exc:
            print(f"Connection lost: {exc}")
        print("Client disconnected")

    def begin_auth(self, username):
        self.username = username
        return True

    def password_auth_supported(self):
        return True

    def validate_password(self, username, password):
        # 密码的
        if password == "ciallo":
            print(f"User {username} authenticated successfully")
            return True
        print(f"Failed authentication attempt for {username}")
        return False

    def session_requested(self):
        return True

    async def start_session(self, process):
        game = ASCIIRPG(process)
        await game.run()
        process.exit(0)


# 跑起来主服务器
async def run_server():
    host = '0.0.0.0'
    port = 22

    print(f"Starting SSH game server on {host}:{port}")
    print("Connect with: ssh -p 22 player@localhost")
    print("Password: ciallo")

    await asyncssh.create_server(
        SSHGameServer,
        host,
        port,
        server_host_keys=['ssh_host_key'],
        process_factory=None
    )


# 密钥
async def generate_ssh_key():
    key = await asyncssh.generate_private_key('ssh-rsa')
    key.write_private_key('ssh_host_key')
    return key


# 面
def main():
    loop = asyncio.get_event_loop()


    try:
        open('ssh_host_key', 'r').close()
    except FileNotFoundError:
        print("Generating SSH host key...")
        loop.run_until_complete(generate_ssh_key())

    # 启动！
    try:
        loop.run_until_complete(run_server())
        loop.run_forever()
    except (OSError, asyncssh.Error) as exc:
        sys.exit(f"Error starting server: {exc}")
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        loop.close()


if __name__ == "__main__":
    main()