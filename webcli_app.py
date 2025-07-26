#!/usr/bin/env python3
import cherrypy
import json
import os
import sys
from typing import Dict, Any

# 添加当前目录到Python路径，以便导入其他模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from service_game import GameService
from service_config import ConfigService


class WebCLIApp:
    """WebCLI主应用类"""
    
    def __init__(self):
        self.game_service = GameService()
        self.config_service = ConfigService()
        self.session_data = {}  # 简单的会话存储
        
    def _get_session_id(self):
        """获取会话 ID（简化版本，实际项目中应使用更安全的会话管理）"""
        return cherrypy.session.get('session_id', 'default')
    
    def _get_game_state(self):
        """获取当前游戏状态"""
        session_id = self._get_session_id()
        if session_id not in self.session_data:
            self.session_data[session_id] = self.game_service.create_new_game()
        return self.session_data[session_id]
    
    @cherrypy.expose
    def index(self, command=''):
        """主页面，处理命令输入和显示"""
        game_state = self._get_game_state()
        
        # 处理命令
        if command.strip():
            response = self.game_service.process_command(command.strip(), game_state)
            game_state['history'].append({
                'type': 'command',
                'content': f"> {command}"
            })
            game_state['history'].append({
                'type': 'response',
                'content': response
            })
        
        # 构建历史记录 HTML
        history_html = ""
        for entry in game_state.get('history', []):
            if entry['type'] == 'command':
                history_html += f'<div class="command-line">{entry["content"]}</div>'
            else:
                history_html += f'<div class="response-line">{entry["content"]}</div>'
        
        # 返回完整的 HTML 页面
        return f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>OI</title>
            <style>
                body {{
                    font-family: 'Courier New', monospace;
                    background-color: #1a1a1a;
                    color: #00ff00;
                    margin: 0;
                    padding: 20px;
                    line-height: 1.4;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                }}
                .header {{
                    text-align: center;
                    border-bottom: 2px solid #00ff00;
                    padding-bottom: 20px;
                    margin-bottom: 20px;
                }}
                .game-title {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #00ffff;
                }}
                .game-subtitle {{
                    font-size: 14px;
                    color: #888;
                    margin-top: 5px;
                }}
                .terminal {{
                    background-color: #000;
                    border: 2px solid #00ff00;
                    border-radius: 5px;
                    padding: 15px;
                    min-height: 400px;
                    max-height: 500px;
                    overflow-y: auto;
                    margin-bottom: 20px;
                }}
                .command-line {{
                    color: #ffff00;
                    margin: 5px 0;
                }}
                .response-line {{
                    color: #00ff00;
                    margin: 5px 0;
                    white-space: pre-wrap;
                }}
                .input-area {{
                    display: flex;
                    gap: 10px;
                }}
                .command-input {{
                    flex: 1;
                    background-color: #000;
                    border: 2px solid #00ff00;
                    color: #00ff00;
                    padding: 10px;
                    font-family: 'Courier New', monospace;
                    font-size: 14px;
                }}
                .command-input:focus {{
                    outline: none;
                    border-color: #00ffff;
                }}
                .submit-btn {{
                    background-color: #00ff00;
                    color: #000;
                    border: none;
                    padding: 10px 20px;
                    font-family: 'Courier New', monospace;
                    font-weight: bold;
                    cursor: pointer;
                }}
                .submit-btn:hover {{
                    background-color: #00ffff;
                }}
                .help-text {{
                    color: #888;
                    font-size: 12px;
                    margin-top: 10px;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="game-title">OI</div>
                    <div class="game-subtitle">AI驱动的文字冒险游戏</div>
                </div>
                
                <div class="terminal" id="terminal">
                    {history_html}
                </div>
                
                <form action="/" method="post" class="input-area">
                    <input type="text" name="command" class="command-input" 
                           placeholder="输入命令... (例如: look, help, go north)" 
                           id="commandInput" autocomplete="off">
                    <button type="submit" class="submit-btn">执行</button>
                </form>
                
                <div class="help-text">
                    提示: 输入 'help' 查看可用命令 | 输入 'clear' 清空屏幕
                </div>
            </div>
            
            <script>
                // 自动聚焦到输入框
                document.getElementById('commandInput').focus();
                
                // 回车键提交
                document.getElementById('commandInput').addEventListener('keypress', function(e) {{
                    if (e.key === 'Enter') {{
                        e.preventDefault();
                        this.form.submit();
                    }}
                }});
                
                // 自动滚动到底部
                var terminal = document.getElementById('terminal');
                terminal.scrollTop = terminal.scrollHeight;
                
                // 页面加载后重新聚焦
                window.onload = function() {{
                    document.getElementById('commandInput').focus();
                }};
            </script>
        </body>
        </html>
        """
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def api_command(self, command=''):
        """API 接口，用于处理命令（可选的 JSON API）"""
        game_state = self._get_game_state()
        
        if not command.strip():
            return {'error': '命令不能为空'}
        
        try:
            response = self.game_service.process_command(command.strip(), game_state)
            return {
                'success': True,
                'command': command,
                'response': response,
                'game_state': {
                    'location': game_state.get('current_location', 'unknown'),
                    'history_count': len(game_state.get('history', []))
                }
            }
        except Exception as e:
            return {'error': f'处理命令时出错: {str(e)}'}
    
    @cherrypy.expose
    def clear(self):
        """清空游戏历史"""
        game_state = self._get_game_state()
        game_state['history'] = []
        # 重定向回主页
        raise cherrypy.HTTPRedirect('/')


def main():
    """启动 WebCLI 应用"""
    config_service = ConfigService()
    
    # CherryPy配置
    config = {
        'global': {
            'server.socket_host': config_service.get('server_host', '0.0.0.0'),
            'server.socket_port': config_service.get('server_port', 8080),
            'engine.autoreload.on': True,
        },
        '/': {
            'tools.sessions.on': True,
            'tools.sessions.timeout': config_service.get('session_timeout', 3600),
        }
    }
    
    print("=" * 60)
    print(f"Chat Game WebCLI Starting - {config_service.get_game_title()}")
    print("=" * 60)
    print(f"Web Address: http://localhost:{config_service.get('server_port', 8080)}")
    print(f"API Endpoint: http://localhost:{config_service.get('server_port', 8080)}/api_command")
    print(f"Game Version: {config_service.get('game_version')}")
    print(f"AI Provider: {config_service.get('ai_provider')}")
    print("Press Ctrl+C to stop server")
    print("=" * 60)
    
    # 启动应用
    cherrypy.quickstart(WebCLIApp(), '/', config)


if __name__ == '__main__':
    main()

