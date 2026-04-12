# -*- coding: utf-8 -*-
"""
UDI 扫码打印 APP（Android / Kivy / Python）
升级点：扫码改为 Google ML Kit（GmsBarcodeScanner），优先识别 DataMatrix（兼容 QR）
"""

from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.utils import platform

IS_ANDROID = platform == "android"

if IS_ANDROID:
    from android.permissions import Permission, check_permission, request_permissions
    from android.runnable import run_on_ui_thread
    from jnius import PythonJavaClass, autoclass, java_method

    BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
    JavaString = autoclass("java.lang.String")
    UUID = autoclass("java.util.UUID")
    PythonActivity = autoclass("org.kivy.android.PythonActivity")

    GmsBarcodeScannerOptions = autoclass("com.google.android.gms.code.scanner.GmsBarcodeScannerOptions")
    GmsBarcodeScanning = autoclass("com.google.android.gms.code.scanner.GmsBarcodeScanning")

    # ML Kit 条码格式常量
    Barcode = autoclass("com.google.mlkit.vision.barcode.common.Barcode")


class BluetoothPrinter:
    """蓝牙热敏打印（SPP）"""

    SPP_UUID = "00001101-0000-1000-8000-00805F9B34FB"

    def __init__(self):
        if not IS_ANDROID:
            raise RuntimeError("蓝牙打印仅支持 Android 真机")

        self.adapter = BluetoothAdapter.getDefaultAdapter()
        if self.adapter is None:
            raise RuntimeError("当前设备不支持蓝牙")

    def list_paired_devices(self):
        bonded = self.adapter.getBondedDevices()
        it = bonded.iterator()
        result = []
        while it.hasNext():
            d = it.next()
            result.append(
                {
                    "name": str(d.getName() or "未命名设备"),
                    "address": str(d.getAddress()),
                    "device": d,
                }
            )
        return result

    def print_text(self, device_address: str, text: str):
        target = None
        for d in self.list_paired_devices():
            if d["address"] == device_address:
                target = d["device"]
                break

        if target is None:
            raise RuntimeError("未找到目标打印机，请先配对并刷新蓝牙设备")

        socket = None
        try:
            self.adapter.cancelDiscovery()
            socket = target.createRfcommSocketToServiceRecord(UUID.fromString(self.SPP_UUID))
            socket.connect()
            out = socket.getOutputStream()

            payload = (
                "UDI二维码内容\n"
                f"打印时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                "--------------------------------\n"
                f"{text}\n\n\n"
            )

            # 常见热敏打印机中文编码
            out.write(JavaString(payload).getBytes("GBK"))
            out.flush()
        finally:
            if socket:
                socket.close()


if IS_ANDROID:
    class _OnSuccessListener(PythonJavaClass):
        __javainterfaces__ = ["com/google/android/gms/tasks/OnSuccessListener"]
        __javacontext__ = "app"

        def __init__(self, callback):
            super().__init__()
            self.callback = callback

        @java_method("(Ljava/lang/Object;)V")
        def onSuccess(self, result):
            raw = ""
            fmt = -1
            try:
                if result is not None:
                    raw = str(result.getRawValue() or "")
                    fmt = int(result.getFormat())
            except Exception:
                pass
            self.callback(raw, fmt)


    class _OnFailureListener(PythonJavaClass):
        __javainterfaces__ = ["com/google/android/gms/tasks/OnFailureListener"]
        __javacontext__ = "app"

        def __init__(self, callback):
            super().__init__()
            self.callback = callback

        @java_method("(Ljava/lang/Exception;)V")
        def onFailure(self, exc):
            self.callback(str(exc))


class MLKitDataMatrixScanner:
    """调用 Google Code Scanner（底层 ML Kit）进行扫描。"""

    def __init__(self):
        if not IS_ANDROID:
            raise RuntimeError("ML Kit 扫码仅支持 Android")

        self.activity = PythonActivity.mActivity
        self._ok_listener = None
        self._err_listener = None

        # 优先 DataMatrix，同时兼容 QR，方便现场混用
        try:
            options = (
                GmsBarcodeScannerOptions.Builder()
                .setBarcodeFormats(Barcode.FORMAT_DATA_MATRIX, Barcode.FORMAT_QR_CODE)
                .build()
            )
            self.scanner = GmsBarcodeScanning.getClient(self.activity, options)
        except Exception:
            # 若不同设备 API 兼容性异常，则回退默认扫描配置
            self.scanner = GmsBarcodeScanning.getClient(self.activity)

    def start_scan(self, on_success, on_error):
        self._ok_listener = _OnSuccessListener(on_success)
        self._err_listener = _OnFailureListener(on_error)
        self._start_scan_ui()

    @run_on_ui_thread
    def _start_scan_ui(self):
        task = self.scanner.startScan()
        task.addOnSuccessListener(self._ok_listener)
        task.addOnFailureListener(self._err_listener)


class UdiPrinterUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=10, padding=12, **kwargs)
        Window.clearcolor = (1, 1, 1, 1)

        self.printer = None
        self.scanner = None
        self.paired_devices = []

        self.add_widget(Label(text="UDI(DataMatrix/QR) 扫码 + 蓝牙打印", size_hint_y=None, height=42, color=(0, 0, 0, 1)))

        row_bt = BoxLayout(size_hint_y=None, height=46, spacing=8)
        self.device_spinner = Spinner(text="请选择已配对蓝牙打印机", values=[])
        btn_refresh = Button(text="刷新蓝牙")
        btn_refresh.bind(on_press=lambda *_: self.refresh_paired_devices())
        row_bt.add_widget(self.device_spinner)
        row_bt.add_widget(btn_refresh)
        self.add_widget(row_bt)

        self.text_input = TextInput(
            hint_text="点击“扫描UDI”，识别内容将显示在这里",
            multiline=True,
            foreground_color=(0, 0, 0, 1),
            background_color=(0.96, 0.96, 0.96, 1),
        )
        self.add_widget(self.text_input)

        row_ops = BoxLayout(size_hint_y=None, height=52, spacing=10)
        btn_scan = Button(text="扫描UDI（ML Kit）")
        btn_print = Button(text="蓝牙打印")
        btn_scan.bind(on_press=self.scan_udi)
        btn_print.bind(on_press=self.print_now)
        row_ops.add_widget(btn_scan)
        row_ops.add_widget(btn_print)
        self.add_widget(row_ops)

        self.status = Label(text="状态：待机", size_hint_y=None, height=34, color=(0, 0, 0, 1))
        self.add_widget(self.status)

    def set_status(self, text: str):
        self.status.text = f"状态：{text}"

    def ensure_permissions(self):
        if not IS_ANDROID:
            self.set_status("当前非 Android 环境，仅可预览 UI")
            return

        # Code Scanner 通常不需要 CAMERA 权限，但这里保留，兼容部分机型
        perms = [
            Permission.CAMERA,
            Permission.BLUETOOTH,
            Permission.BLUETOOTH_ADMIN,
            Permission.ACCESS_FINE_LOCATION,
            "android.permission.BLUETOOTH_SCAN",
            "android.permission.BLUETOOTH_CONNECT",
        ]
        need = [p for p in perms if not check_permission(p)]
        if need:
            request_permissions(need)

    def refresh_paired_devices(self):
        if not IS_ANDROID:
            self.set_status("仅 Android 可连接蓝牙打印机")
            return

        try:
            if self.printer is None:
                self.printer = BluetoothPrinter()

            self.paired_devices = self.printer.list_paired_devices()
            names = [f"{d['name']} ({d['address']})" for d in self.paired_devices]
            self.device_spinner.values = names
            if names:
                self.device_spinner.text = names[0]
                self.set_status(f"已发现 {len(names)} 台已配对设备")
            else:
                self.device_spinner.text = "请选择已配对蓝牙打印机"
                self.set_status("未发现已配对蓝牙设备，请先在系统蓝牙中配对")
        except Exception as e:
            self.set_status(f"刷新蓝牙失败: {e}")

    def scan_udi(self, *_):
        if not IS_ANDROID:
            self.set_status("扫码仅支持 Android 真机")
            return

        try:
            if self.scanner is None:
                self.scanner = MLKitDataMatrixScanner()

            self.set_status("正在打开 ML Kit 扫码界面...")
            self.scanner.start_scan(self._on_scan_success, self._on_scan_error)
        except Exception as e:
            self.set_status(f"扫码启动失败: {e}")

    def _on_scan_success(self, raw_text: str, fmt: int):
        def _update(_dt):
            txt = (raw_text or "").strip()
            if not txt:
                self.set_status("未识别到内容，请重试")
                return
            self.text_input.text = txt
            self.set_status(f"扫描成功（format={fmt}），内容已写入文本框")

        Clock.schedule_once(_update, 0)

    def _on_scan_error(self, error_text: str):
        def _update(_dt):
            err = (error_text or "").strip() or "未知错误或用户取消"
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            block = f"[扫描错误 {stamp}]\n{err}"

            if self.text_input.text.strip():
                self.text_input.text = self.text_input.text.rstrip() + "\n\n" + block
            else:
                self.text_input.text = block

            self.set_status("扫码失败/取消，完整错误已写入文本框")

        Clock.schedule_once(_update, 0)

    def _selected_address(self):
        t = self.device_spinner.text.strip()
        if "(" in t and t.endswith(")"):
            return t[t.rfind("(") + 1 : -1]
        return ""

    def print_now(self, *_):
        if not IS_ANDROID:
            self.set_status("蓝牙打印仅支持 Android")
            return

        text = self.text_input.text.strip()
        if not text:
            self.set_status("请先扫描或输入要打印内容")
            return

        address = self._selected_address()
        if not address:
            self.set_status("请先选择蓝牙打印机")
            return

        try:
            if self.printer is None:
                self.printer = BluetoothPrinter()
            self.printer.print_text(address, text)
            self.set_status("打印成功")
        except Exception as e:
            self.set_status(f"打印失败: {e}")


class UDIPrinterApp(App):
    def build(self):
        ui = UdiPrinterUI()
        ui.ensure_permissions()
        ui.refresh_paired_devices()
        return ui


if __name__ == "__main__":
    UDIPrinterApp().run()
