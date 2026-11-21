"""Send keyboard input to Chrome's native Open dialog on the R22 test desktop.

launch_browser.mjs owns the profile guard and calls the launch subcommand.
choose BROWSER_PID FILE waits for a visible Open dialog on this desktop,
types into its visible File name Edit, and presses Enter. The driver must
then observe the resulting import in the App.
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import subprocess
import time

user32 = C.WinDLL("user32", use_last_error=True)
kernel32 = C.WinDLL("kernel32", use_last_error=True)
desktop_name = os.environ.get("L4_PICKER_DESKTOP", "GeometryL4Picker20261121")
callback_type = C.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)


def win_api(lib, name, result_type, *arg_types):
    func = getattr(lib, name)
    func.argtypes, func.restype = arg_types, result_type
    return func


def checked(result):
    if not result:
        raise C.WinError(C.get_last_error())
    return result


close_handle = win_api(kernel32, "CloseHandle", W.BOOL, W.HANDLE)
close_desktop = win_api(user32, "CloseDesktop", W.BOOL, W.HANDLE)
open_process = win_api(kernel32, "OpenProcess", W.HANDLE, W.DWORD, W.BOOL, W.DWORD)
query_process = win_api(C.WinDLL("ntdll"), "NtQueryInformationProcess", C.c_long,
                        W.HANDLE, W.DWORD, C.c_void_p, W.DWORD, C.POINTER(W.DWORD))
enum_top = win_api(user32, "EnumDesktopWindows", W.BOOL, W.HANDLE, callback_type, W.LPARAM)
enum_children = win_api(user32, "EnumChildWindows", W.BOOL, W.HWND, callback_type, W.LPARAM)
window_pid = win_api(user32, "GetWindowThreadProcessId", W.DWORD, W.HWND, C.POINTER(W.DWORD))
window_class = win_api(user32, "GetClassNameW", C.c_int, W.HWND, W.LPWSTR, C.c_int)
window_title = win_api(user32, "GetWindowTextW", C.c_int, W.HWND, W.LPWSTR, C.c_int)
visible = win_api(user32, "IsWindowVisible", W.BOOL, W.HWND)
control_id = win_api(user32, "GetDlgCtrlID", C.c_int, W.HWND)
post = win_api(user32, "PostMessageW", W.BOOL, W.HWND, W.UINT, W.WPARAM, W.LPARAM)


class StartupInfo(C.Structure):
    _fields_ = [
        ("cb", W.DWORD), ("lpReserved", W.LPWSTR), ("lpDesktop", W.LPWSTR),
        ("lpTitle", W.LPWSTR), ("dwX", W.DWORD), ("dwY", W.DWORD),
        ("dwXSize", W.DWORD), ("dwYSize", W.DWORD), ("dwXCountChars", W.DWORD),
        ("dwYCountChars", W.DWORD), ("dwFillAttribute", W.DWORD),
        ("dwFlags", W.DWORD), ("wShowWindow", W.WORD), ("cbReserved2", W.WORD),
        ("lpReserved2", C.c_void_p), ("hStdInput", W.HANDLE),
        ("hStdOutput", W.HANDLE), ("hStdError", W.HANDLE),
    ]


class ProcessInfo(C.Structure):
    _fields_ = [("hProcess", W.HANDLE), ("hThread", W.HANDLE),
                ("dwProcessId", W.DWORD), ("dwThreadId", W.DWORD)]


def launch(exe, profile):
    # Require the caller's prepared Local State before spawning Chromium.
    guard = json.loads((Path(profile) / "Local State").read_bytes())["password_manager"]
    if guard["os_password_blank"] is not False or not guard["os_password_last_changed"].isdigit():
        raise ValueError("The test profile has not passed the browser guard")
    create_desktop = win_api(user32, "CreateDesktopW", W.HANDLE, W.LPCWSTR,
                             C.c_void_p, C.c_void_p, W.DWORD, W.DWORD, C.c_void_p)
    create_process = win_api(kernel32, "CreateProcessW", W.BOOL, W.LPCWSTR,
                             W.LPWSTR, C.c_void_p, C.c_void_p, W.BOOL, W.DWORD,
                             C.c_void_p, W.LPCWSTR, C.POINTER(StartupInfo), C.POINTER(ProcessInfo))
    desktop = checked(create_desktop(desktop_name, None, None, 0, 0x000F01FF, None))
    try:
        command = subprocess.list2cmdline([
            exe, "--user-data-dir=" + profile, "--remote-debugging-port=0",
            "--remote-debugging-address=127.0.0.1", "--disable-background-mode",
            "--no-first-run", "--no-default-browser-check", "--disable-gpu",
            "--window-size=1400,900", "about:blank",
        ])
        startup = StartupInfo()
        startup.cb = C.sizeof(startup)
        startup.lpDesktop = "WinSta0\\" + desktop_name
        process = ProcessInfo()
        checked(create_process(exe, C.create_unicode_buffer(command), None, None,
                               False, 0, None, None, C.byref(startup), C.byref(process)))
        close_handle(process.hThread)
        close_handle(process.hProcess)
        print(process.dwProcessId, flush=True)
        time.sleep(1)
    finally:
        close_desktop(desktop)


def parent_pid(pid):
    handle = open_process(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return None
    try:
        # PROCESS_BASIC_INFORMATION ends with InheritedFromUniqueProcessId.
        words = (C.c_size_t * 6)()
        status = query_process(handle, 0, C.byref(words), C.sizeof(words), None)
        return words[5] if status == 0 else None
    finally:
        close_handle(handle)


def matching_windows(enumerate_windows, owner, predicate):
    result = []

    @callback_type
    def collect(hwnd, _):
        if visible(hwnd) and predicate(hwnd):
            result.append(hwnd)
        return True

    enumerate_windows(owner, collect, 0)
    return result


def name_of(hwnd, function):
    buff = C.create_unicode_buffer(128)
    function(hwnd, buff, len(buff))
    return buff.value


def choose(browser_pid, filename):
    file = Path(filename).resolve(strict=True)
    if not file.is_file():
        raise ValueError("Choose requires a regular file")

    def is_open_dialog(hwnd):
        pid = W.DWORD()
        window_pid(hwnd, C.byref(pid))
        return (name_of(hwnd, window_class) == "#32770"
                and name_of(hwnd, window_title) in ("開啟", "Open")
                and (pid.value == browser_pid or parent_pid(pid.value) == browser_pid))

    open_desktop = win_api(user32, "OpenDesktopW", W.HANDLE, W.LPCWSTR, W.DWORD, W.BOOL, W.DWORD)
    desktop = checked(open_desktop(desktop_name, 0, False, 0x0041))
    try:
        for _ in range(100):
            dialogs = matching_windows(enum_top, desktop, is_open_dialog)
            if dialogs:
                break
            time.sleep(.1)
        if len(dialogs) != 1:
            raise RuntimeError("Expected one native Open dialog for the test Chrome")
        is_filename = lambda h: control_id(h) == 1148 and name_of(h, window_class) == "Edit"
        edits = matching_windows(enum_children, dialogs[0], is_filename)
        if len(edits) != 1:
            raise RuntimeError("Expected one visible File name Edit")
        edit = edits[0]
        encoded = str(file).encode("utf-16-le")
        for i in range(0, len(encoded), 2):
            checked(post(edit, 0x0102, int.from_bytes(encoded[i:i+2], "little"), 1))  # WM_CHAR
        time.sleep(.25)
        checked(post(edit, 0x0100, 0x0D, 0x001C0001))  # Enter key down
        checked(post(edit, 0x0101, 0x0D, 0xC01C0001))  # Enter key up
        print(json.dumps({"browserPid": browser_pid, "file": file.name, "input": "filename + Enter"}))
    finally:
        close_desktop(desktop)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    launch_args = modes.add_parser("launch")
    launch_args.add_argument("exe")
    launch_args.add_argument("profile")
    choose_args = modes.add_parser("choose")
    choose_args.add_argument("pid", type=int)
    choose_args.add_argument("path")
    args = parser.parse_args()
    if args.mode == "launch":
        launch(args.exe, args.profile)
    else:
        choose(args.pid, args.path)
