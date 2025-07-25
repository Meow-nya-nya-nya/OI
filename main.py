#!/usr/bin/env python3
import asyncssh
import asyncio
import os
import time

class OI:
    def __init__(self, chan):
        self.chan = chan
        self.terminal_width = 80
        self.terminal_height = 24
        self.running = True

    async def run(self):
        """主游戏循环"""
        try:
            # 初始化终端
            await self.initialize_terminal()

            # 主循环
            while self.running:
                # 检查用户输入
                if await self.check_input():
                    break

                # 更新显示
                await self.update_display()

                # 控制刷新率
                await asyncio.sleep(0.1)
        finally:
            await self.cleanup()

    async def initialize_terminal(self):
        """初始化终端设置"""
        self.chan.write("\x1b[?25l")  # 隐藏光标
        self.chan.write("\x1b[?1049h")  # 进入备用屏幕缓冲区
        await self.clear_screen()
        await self.draw_ascii_art()

    async def cleanup(self):
        """清理终端设置"""
        try:
            await self.chan.write("\x1b[?25h")  # 显示光标
            await self.chan.write("\x1b[?1049l")  # 退出备用屏幕缓冲区
            await self.chan.write("\x1b[2J\x1b[H")  # 清屏
            await self.chan.write("Goodbye! Thanks for playing.\r\n")
        except:
            pass

    async def check_input(self):
        """检查用户输入"""
        try:
            if self.chan.reader._buffer:
                data = await self.chan.read(1)
                if data.lower() == 'q':
                    self.running = False
                    return True
        except:
            self.running = False
            return True
        return False

    async def clear_screen(self):
        """清屏并重置光标位置"""
        self.chan.write("\x1b[2J\x1b[H")

    async def draw_ascii_art(self):
        """绘制 Ciallo 的 ASCII 艺术字"""
        art = r"""
  ____  _       _        _       _ 
 / ___|(_) __ _| | ___  | | ___ | |
| |    | |/ _` | |/ _ \ | |/ _ \| |
| |____| | (_| | |  __/ | | (_) | |
 \____||_|\__, |_|\___| |_|\___/|_|
          |___/                    
""".strip('\n')

        # 居中显示
        lines = art.split('\n')
        max_width = max(len(line) for line in lines)
        center_x = max(0, (self.terminal_width - max_width) // 2)
        center_y = max(0, (self.terminal_height - len(lines)) // 2)

        # 定位光标并绘制
        self.chan.write(f"\x1b[{center_y}H")  # 移动到垂直中心
        for line in lines:
            self.chan.write(f"\x1b[{center_x}G")  # 移动到水平位置
            self.chan.write(line + "\r\n")

        # 显示提示信息
        prompt = "Press 'q' to exit"
        prompt_x = max(0, (self.terminal_width - len(prompt)) // 2)
        self.chan.write(f"\x1b[{center_y + len(lines) + 2}H")  # 移动到提示行
        self.chan.write(f"\x1b[{prompt_x}G")  # 移动到水平位置
        self.chan.write(f"\x1b[1;33m{prompt}\x1b[0m")  # 黄色加粗文本

    async def update_display(self):
        """更新屏幕显示"""
        pass

class SSHGameServer(asyncssh.SSHServer):
    def __init__(self):
        super().__init__()
        self.username = None

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
        return SSHGameSession()

class SSHGameSession(asyncssh.SSHServerSession):
    def __init__(self):
        super().__init__()
        self.chan = None

    def shell_requested(self):
        return True

    def pty_requested(self, term_type, term_size, term_modes):
        if term_size:
            print(f"Terminal size: {term_size[0]}x{term_size[1]}")
        return True

    def session_started(self):
        asyncio.create_task(self._run_game())

    def connection_made(self, chan):
        self.chan = chan

    async def _run_game(self):
        try:
            self.chan.set_write_buffer_limits(0)
            game = OI(self.chan)
            await game.run()
        except (asyncssh.BreakReceived, asyncssh.TerminalSizeChanged):
            pass
        except Exception as e:
            print(f"Game session error: {e}")
        finally:
            if self.chan is not None:
                try:
                    await self.chan.close()
                except asyncssh.ConnectionLost:
                    pass

def generate_ssh_key():
    key_path = 'ssh_host_key'
    if not os.path.exists(key_path):
        print("Generating SSH host key...")
        key = asyncssh.generate_private_key('ssh-rsa', key_size=2048)
        key.write_private_key(key_path)
        print(f"SSH host key generated and saved to {key_path}")
    else:
        print(f"Using existing SSH host key at {key_path}")

async def run_server():
    host = '0.0.0.0'
    port = 2222

    print(f"Starting SSH game server on {host}:{port}")
    print("Connect with: ssh -p 2222 player@localhost")
    print("Password: ciallo")

    try:
        await asyncssh.create_server(
            SSHGameServer,
            host,
            port,
            server_host_keys=['ssh_host_key']
        )
    except Exception as e:
        print(f"Server creation error: {e}")
        raise

def main():
    generate_ssh_key()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        print("Starting server...")
        server_task = loop.create_task(run_server())
        loop.run_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        tasks = asyncio.all_tasks(loop)
        for task in tasks:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        loop.close()
        print("Server stopped.")

if __name__ == "__main__":
    main()