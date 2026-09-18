from __future__ import annotations

import ctypes
import logging
import sys
import threading
import msvcrt
from logging.handlers import RotatingFileHandler

from runtime_paths import DATA_ROOT, RESOURCE_ROOT


def main() -> int:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    instance = (DATA_ROOT / 'desktop.lock').open('a+b')
    instance.seek(0)
    try:
        msvcrt.locking(instance.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        instance.close()
        user32 = ctypes.windll.user32
        user32.FindWindowW.restype = ctypes.c_void_p
        handle = user32.FindWindowW(None, 'WeWrite')
        if handle:
            user32.ShowWindow(ctypes.c_void_p(handle), 9)
            user32.SetForegroundWindow(ctypes.c_void_p(handle))
        return 0
    log = RotatingFileHandler(DATA_ROOT / 'desktop.log', maxBytes=2_000_000, backupCount=2, encoding='utf-8')
    logging.basicConfig(handlers=[log], level=logging.INFO)
    # Windowed executables do not have console streams.
    if sys.stderr is None:
        sys.stderr = log.stream
    if sys.stdout is None:
        sys.stdout = log.stream
    httpd = None
    try:
        import webview
        from server import AppHandler, ThreadingHTTPServer
        httpd = ThreadingHTTPServer(('127.0.0.1', 0), AppHandler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        webview.settings['ALLOW_DOWNLOADS'] = True
        webview.create_window('WeWrite', f'http://127.0.0.1:{httpd.server_port}/',
                              width=1280, height=860, min_size=(800, 600),
                              text_select=True, confirm_close=True)
        webview.start(gui='edgechromium', private_mode=False,
                      storage_path=str(DATA_ROOT / 'webview'),
                      icon=str(RESOURCE_ROOT / 'packaging' / 'wewrite.ico'),
                      localization={'global.quitConfirmation': '确定退出 WeWrite？正在执行的任务将被中断。'})
        return 0
    except Exception:
        logging.exception('Desktop startup failed')
        ctypes.windll.user32.MessageBoxW(None,
            'WeWrite 启动失败。请确认电脑已安装 Microsoft Edge WebView2 Runtime，'
            '并且程序所在目录可写。详细信息见 data/desktop.log。', 'WeWrite', 16)
        return 1
    finally:
        if httpd:
            httpd.shutdown()
            httpd.server_close()
        from rewrite_service import stop_owned_server
        stop_owned_server()
        instance.close()


if __name__ == '__main__':
    raise SystemExit(main())
